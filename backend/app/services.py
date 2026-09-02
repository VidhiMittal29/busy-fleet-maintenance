from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_manager
from app.database import get_db
from app.models import (
    ServiceEvent,
    ServiceRecord,
    ServiceTechnician,
    User,
    Vehicle,
)
from app.schemas import (
    ServiceBooking,
    ServiceRecordCreate,
    ServiceRecordResponse,
    ServiceStatusUpdate,
    TechnicianAssignment,
)


router = APIRouter(
    prefix="/services",
    tags=["Service Records"],
)


@router.post(
    "",
    response_model=ServiceRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_record(
    service_data: ServiceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == service_data.vehicle_id,
            Vehicle.is_archived == False,
        )
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active vehicle not found",
        )

    service = ServiceRecord(
        vehicle_id=service_data.vehicle_id,
        description=service_data.description,
        status="DUE",
        scheduled_date=service_data.scheduled_date,
    )

    db.add(service)
    db.flush()

    db.add(
        ServiceEvent(
            service_id=service.id,
            event_type="CREATED",
            old_status=None,
            new_status="DUE",
            note="Service record created",
            created_by=current_user.id,
        )
    )

    db.commit()
    db.refresh(service)

    return service


@router.get("")
def list_service_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: str | None = None,
    vehicle_id: int | None = None,
    service_status: str | None = None,
    technician_id: int | None = None,
    sort_by: str = "updated_at",
    page: int = 1,
    page_size: int = 10,
):
    query = db.query(ServiceRecord)

    if current_user.role == "TECHNICIAN":
        query = query.join(
            ServiceTechnician,
            ServiceTechnician.service_id == ServiceRecord.id,
        ).filter(
            ServiceTechnician.technician_id == current_user.id
        )

    if search:
        query = query.filter(
            ServiceRecord.description.ilike(f"%{search}%")
        )

    if vehicle_id is not None:
        query = query.filter(
            ServiceRecord.vehicle_id == vehicle_id
        )

    if service_status:
        query = query.filter(
            ServiceRecord.status == service_status.upper()
        )

    if technician_id is not None:
        if current_user.role == "TECHNICIAN":
            query = query.filter(
                ServiceTechnician.technician_id == technician_id
            )
        else:
            query = query.join(
                ServiceTechnician,
                ServiceTechnician.service_id == ServiceRecord.id,
            ).filter(
                ServiceTechnician.technician_id == technician_id
            )

    if sort_by == "scheduled_date":
        query = query.order_by(ServiceRecord.scheduled_date.asc())
    elif sort_by == "status":
        query = query.order_by(ServiceRecord.status.asc())
    else:
        query = query.order_by(ServiceRecord.updated_at.desc())

    total = query.count()

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 10

    services = (
        query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": services,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/{service_id}/book",
    response_model=ServiceRecordResponse,
)
def book_service(
    service_id: int,
    booking: ServiceBooking,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    service = (
        db.query(ServiceRecord)
        .filter(ServiceRecord.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service record not found",
        )

    if service.status != "DUE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Only DUE services can be booked. "
                f"Current status is {service.status}."
            ),
        )

    if not booking.technician_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one technician must be assigned when booking",
        )

    technicians = (
        db.query(User)
        .filter(
            User.id.in_(booking.technician_ids),
            User.role == "TECHNICIAN",
            User.is_active == True,
        )
        .all()
    )

    if len(technicians) != len(set(booking.technician_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more technician IDs are invalid or inactive",
        )

    service.scheduled_date = booking.scheduled_date
    service.status = "BOOKED"
    service.updated_at = datetime.utcnow()

    for technician in technicians:
        existing = (
            db.query(ServiceTechnician)
            .filter(
                ServiceTechnician.service_id == service.id,
                ServiceTechnician.technician_id == technician.id,
            )
            .first()
        )

        if not existing:
            db.add(
                ServiceTechnician(
                    service_id=service.id,
                    technician_id=technician.id,
                )
            )

            db.add(
                ServiceEvent(
                    service_id=service.id,
                    event_type="TECHNICIAN_ASSIGNED",
                    old_status="DUE",
                    new_status="BOOKED",
                    note=f"Technician {technician.email} assigned",
                    created_by=current_user.id,
                )
            )

    db.add(
        ServiceEvent(
            service_id=service.id,
            event_type="STATUS_CHANGE",
            old_status="DUE",
            new_status="BOOKED",
            note=f"Service booked for {booking.scheduled_date}",
            created_by=current_user.id,
        )
    )

    db.commit()
    db.refresh(service)

    return service


@router.patch(
    "/{service_id}/status",
    response_model=ServiceRecordResponse,
)
def update_service_status(
    service_id: int,
    status_data: ServiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = (
        db.query(ServiceRecord)
        .filter(ServiceRecord.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service record not found",
        )

    new_status = status_data.status.upper()

    allowed_statuses = {
        "DUE",
        "BOOKED",
        "IN_SERVICE",
        "COMPLETED",
    }

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid service status",
        )

    old_status = service.status

    if old_status == new_status:
        return service

    valid_transitions = {
        "DUE": "BOOKED",
        "BOOKED": "IN_SERVICE",
        "IN_SERVICE": "COMPLETED",
    }

    expected_next_status = valid_transitions.get(old_status)

    if expected_next_status != new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition: "
                f"{old_status} -> {new_status}. "
                f"Expected {expected_next_status or 'no further transition'}."
            ),
        )

    if current_user.role == "TECHNICIAN":
        assignment = (
            db.query(ServiceTechnician)
            .filter(
                ServiceTechnician.service_id == service.id,
                ServiceTechnician.technician_id == current_user.id,
            )
            .first()
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this service record",
            )

    if new_status == "BOOKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the booking endpoint to book a service",
        )

    if new_status == "COMPLETED":
        vehicle = (
            db.query(Vehicle)
            .filter(Vehicle.id == service.vehicle_id)
            .first()
        )

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found",
            )

        vehicle.last_service_date = datetime.utcnow().date()
        vehicle.last_service_odometer = vehicle.current_odometer

    service.status = new_status
    service.updated_at = datetime.utcnow()

    db.add(
        ServiceEvent(
            service_id=service.id,
            event_type="STATUS_CHANGE",
            old_status=old_status,
            new_status=new_status,
            note=f"Status changed from {old_status} to {new_status}",
            created_by=current_user.id,
        )
    )

    if new_status == "COMPLETED":
        next_service = ServiceRecord(
            vehicle_id=service.vehicle_id,
            description=service.description,
            status="DUE",
            scheduled_date=None,
        )

        db.add(next_service)
        db.flush()

        db.add(
            ServiceEvent(
                service_id=next_service.id,
                event_type="CREATED",
                old_status=None,
                new_status="DUE",
                note="Next service cycle created after completion",
                created_by=current_user.id,
            )
        )

    db.commit()
    db.refresh(service)

    return service


@router.post(
    "/{service_id}/technician",
    response_model=ServiceRecordResponse,
)
def assign_technician(
    service_id: int,
    assignment: TechnicianAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    service = (
        db.query(ServiceRecord)
        .filter(ServiceRecord.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service record not found",
        )

    technician = (
        db.query(User)
        .filter(
            User.id == assignment.technician_id,
            User.role == "TECHNICIAN",
            User.is_active == True,
        )
        .first()
    )

    if not technician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active technician not found",
        )

    existing_assignment = (
        db.query(ServiceTechnician)
        .filter(
            ServiceTechnician.service_id == service.id,
            ServiceTechnician.technician_id == technician.id,
        )
        .first()
    )

    if not existing_assignment:
        db.add(
            ServiceTechnician(
                service_id=service.id,
                technician_id=technician.id,
            )
        )

        db.add(
            ServiceEvent(
                service_id=service.id,
                event_type="TECHNICIAN_ASSIGNED",
                old_status=service.status,
                new_status=service.status,
                note=f"Technician {technician.email} assigned",
                created_by=current_user.id,
            )
        )

        db.commit()

    db.refresh(service)

    return service

@router.delete(
    "/{service_id}/technician/{technician_id}",
    response_model=ServiceRecordResponse,
)
def unassign_technician(
    service_id: int,
    technician_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    service = (
        db.query(ServiceRecord)
        .filter(ServiceRecord.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service record not found",
        )

    assignment = (
        db.query(ServiceTechnician)
        .filter(
            ServiceTechnician.service_id == service_id,
            ServiceTechnician.technician_id == technician_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technician is not assigned to this service",
        )

    technician = (
        db.query(User)
        .filter(User.id == technician_id)
        .first()
    )

    db.delete(assignment)

    db.add(
        ServiceEvent(
            service_id=service.id,
            event_type="TECHNICIAN_UNASSIGNED",
            old_status=service.status,
            new_status=service.status,
            note=(
                f"Technician {technician.email if technician else technician_id} "
                "unassigned"
            ),
            created_by=current_user.id,
        )
    )

    service.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(service)

    return service

@router.get(
    "/{service_id}/timeline",
)
def get_service_timeline(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = (
        db.query(ServiceRecord)
        .filter(ServiceRecord.id == service_id)
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service record not found",
        )

    # Technicians can only view the timeline of assigned services.
    if current_user.role == "TECHNICIAN":
        assignment = (
            db.query(ServiceTechnician)
            .filter(
                ServiceTechnician.service_id == service_id,
                ServiceTechnician.technician_id == current_user.id,
            )
            .first()
        )

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this service record",
            )

    events = (
        db.query(ServiceEvent)
        .filter(ServiceEvent.service_id == service_id)
        .order_by(ServiceEvent.created_at.asc(), ServiceEvent.id.asc())
        .all()
    )

    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "old_status": event.old_status,
            "new_status": event.new_status,
            "note": event.note,
            "created_by": event.created_by,
            "created_at": event.created_at,
        }
        for event in events
    ]

@router.patch(
    "/{service_id}",
    response_model=ServiceRecordResponse,
)
def update_service_description(
    service_id: int,
    description: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = db.query(ServiceRecord).filter(
        ServiceRecord.id == service_id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")

    # Managers can edit; technicians can edit only their assigned records.
    if current_user.role == "TECHNICIAN":
        assignment = (
            db.query(ServiceTechnician)
            .filter(
                ServiceTechnician.service_id == service_id,
                ServiceTechnician.technician_id == current_user.id,
            )
            .first()
        )

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="You can update only service records assigned to you",
            )

    elif current_user.role != "MANAGER":
        raise HTTPException(status_code=403, detail="Not authorized")

    service.description = description
    db.commit()
    db.refresh(service)

    return service