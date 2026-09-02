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


@router.get("", response_model=list[ServiceRecordResponse])
def list_service_records(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ServiceRecord)

    if current_user.role == "TECHNICIAN":
        query = query.join(
            ServiceTechnician,
            ServiceTechnician.service_id == ServiceRecord.id,
        ).filter(
            ServiceTechnician.technician_id == current_user.id
        )

    return query.order_by(ServiceRecord.id.desc()).all()


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