import csv
import io
import json
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from datetime import date
from app.auth import get_current_user, require_manager
from app.database import get_db
from app.models import AuditEvent, OdometerReading, ServiceRecord, ServiceTechnician, User, Vehicle
from app.schemas import (
    ServiceRecordResponse,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)


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
    last_service_date=date.today(),
    last_service_odometer=vehicle_data.current_odometer,
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

@router.post("/odometer/bulk")
def bulk_update_odometer(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file",
        )

    try:
        contents = file.file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="CSV file must use UTF-8 encoding",
        )

    reader = csv.DictReader(io.StringIO(contents))

    if not reader.fieldnames:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty or missing headers",
        )

    required_columns = {"vehicle_id", "reading"}

    if not required_columns.issubset(set(reader.fieldnames)):
        raise HTTPException(
            status_code=400,
            detail="CSV must contain vehicle_id and reading columns",
        )

    results = []

    for row_number, row in enumerate(reader, start=2):
        vehicle_id = row.get("vehicle_id")
        reading_value = row.get("reading")

        if not vehicle_id or not reading_value:
            results.append(
                {
                    "row": row_number,
                    "status": "rejected",
                    "reason": "vehicle_id and reading are required",
                }
            )
            continue

        try:
            vehicle_id = int(vehicle_id)
            reading = int(reading_value)
        except ValueError:
            results.append(
                {
                    "row": row_number,
                    "status": "rejected",
                    "reason": "vehicle_id and reading must be integers",
                }
            )
            continue

        vehicle = (
            db.query(Vehicle)
            .filter(Vehicle.id == vehicle_id)
            .first()
        )

        if not vehicle:
            results.append(
                {
                    "row": row_number,
                    "vehicle_id": vehicle_id,
                    "status": "rejected",
                    "reason": "Vehicle not found",
                }
            )
            continue

        latest_reading = (
            db.query(OdometerReading)
            .filter(OdometerReading.vehicle_id == vehicle_id)
            .order_by(OdometerReading.recorded_at.desc())
            .first()
        )

        previous_reading = (
            latest_reading.reading
            if latest_reading
            else vehicle.current_odometer
        )

        if reading < previous_reading:
            results.append(
                {
                    "row": row_number,
                    "vehicle_id": vehicle_id,
                    "status": "rejected",
                    "reason": (
                        f"Reading {reading} is lower than "
                        f"previous reading {previous_reading}"
                    ),
                }
            )
            continue

        vehicle.current_odometer = reading

        db.add(
            OdometerReading(
                vehicle_id=vehicle_id,
                reading=reading,
            )
        )

        results.append(
            {
                "row": row_number,
                "vehicle_id": vehicle_id,
                "status": "success",
                "reading": reading,
            }
        )

    db.commit()

    return {
        "total_rows": len(results),
        "results": results,
    }

@router.get("/services/export")
def export_service_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    services = (
        db.query(ServiceRecord, Vehicle)
        .join(Vehicle, Vehicle.id == ServiceRecord.vehicle_id)
        .order_by(ServiceRecord.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "vehicle_id",
        "registration_number",
        "service_id",
        "description",
        "status",
        "scheduled_date",
        "created_at",
        "updated_at",
    ])

    for service, vehicle in services:
        writer.writerow([
            vehicle.id,
            vehicle.registration_number,
            service.id,
            service.description,
            service.status,
            service.scheduled_date,
            service.created_at,
            service.updated_at,
        ])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=service_history.csv"
        },
    )

@router.get(
    "/{vehicle_id}/services",
    response_model=list[ServiceRecordResponse],
)
def get_vehicle_service_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    query = db.query(ServiceRecord).filter(
    ServiceRecord.vehicle_id == vehicle_id
)

    if current_user.role == "TECHNICIAN":
        query = query.join(
            ServiceTechnician,
            ServiceTechnician.service_id == ServiceRecord.id,
        ).filter(
            ServiceTechnician.technician_id == current_user.id
        )

    return query.order_by(ServiceRecord.created_at.desc()).all()