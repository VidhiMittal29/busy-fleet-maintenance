import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_manager
from app.database import get_db
from app.models import AuditEvent, User, Vehicle
from app.schemas import VehicleCreate, VehicleResponse, VehicleUpdate


router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"],
)


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    existing_vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.registration_number
            == vehicle_data.registration_number
        )
        .first()
    )

    if existing_vehicle:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle registration number already exists",
        )

    vehicle = Vehicle(
    registration_number=vehicle_data.registration_number,
    make=vehicle_data.make,
    model=vehicle_data.model,
    current_odometer=vehicle_data.current_odometer,
    service_date_interval_days=vehicle_data.service_date_interval_days,
    service_mileage_interval=vehicle_data.service_mileage_interval,
    is_archived=False,
)

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle

from fastapi import Query


@router.get("", response_model=list[VehicleResponse])
def list_vehicles(
    search: str | None = None,
    make: str | None = None,
    model: str | None = None,
    is_archived: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Vehicle)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Vehicle.registration_number.ilike(search_term))
            | (Vehicle.make.ilike(search_term))
            | (Vehicle.model.ilike(search_term))
        )

    if make:
        query = query.filter(Vehicle.make.ilike(make))

    if model:
        query = query.filter(Vehicle.model.ilike(model))

    query = query.filter(Vehicle.is_archived == is_archived)

    offset = (page - 1) * page_size

    return (
        query
        .order_by(Vehicle.id)
        .offset(offset)
        .limit(page_size)
        .all()
    )

@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id)
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    update_data = vehicle_data.model_dump(exclude_unset=True)

    if "registration_number" in update_data:
        existing = (
            db.query(Vehicle)
            .filter(
                Vehicle.registration_number
                == update_data["registration_number"],
                Vehicle.id != vehicle_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle registration number already exists",
            )

    changes = {}

    for field, new_value in update_data.items():
        old_value = getattr(vehicle, field)

        if old_value != new_value:
            changes[field] = {
                "old": old_value,
                "new": new_value,
            }
            setattr(vehicle, field, new_value)

    if changes:
        audit_event = AuditEvent(
            user_id=current_user.id,
            action="UPDATE_VEHICLE",
            entity_type="vehicle",
            entity_id=vehicle.id,
            details=json.dumps(changes),
        )
        db.add(audit_event)

    db.commit()
    db.refresh(vehicle)

    return vehicle


@router.post("/{vehicle_id}/archive", response_model=VehicleResponse)
def archive_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id)
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    if vehicle.is_archived:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is already archived",
        )

    vehicle.is_archived = True

    audit_event = AuditEvent(
        user_id=current_user.id,
        action="ARCHIVE_VEHICLE",
        entity_type="vehicle",
        entity_id=vehicle.id,
        details=json.dumps({
    "registration_number": vehicle.registration_number
}),
    )

    db.add(audit_event)
    db.commit()
    db.refresh(vehicle)

    return vehicle

@router.post(
    "/{vehicle_id}/unarchive",
    response_model=VehicleResponse,
)
def unarchive_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    vehicle = (
        db.query(Vehicle)
        .filter(Vehicle.id == vehicle_id)
        .first()
    )

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    if not vehicle.is_archived:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle is already active",
        )

    vehicle.is_archived = False

    db.add(
        AuditEvent(
            user_id=current_user.id,
            action="UNARCHIVE",
            entity_type="VEHICLE",
            entity_id=vehicle.id,
            details=json.dumps({
                "registration_number": vehicle.registration_number
            }),
        )
    )

    db.commit()
    db.refresh(vehicle)

    return vehicle