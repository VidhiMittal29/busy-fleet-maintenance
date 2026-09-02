from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import require_manager
from app.database import get_db
from app.models import ServiceRecord, ServiceTechnician, User, Vehicle

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    today = date.today()

    # -------------------------
    # Vehicle due / overdue
    # -------------------------
    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_archived == False)
        .all()
    )

    due_vehicles = []
    overdue_vehicles = []

    for vehicle in vehicles:
        due = False

        if vehicle.last_service_date is None:
            due = True
        else:
            date_due = (
                vehicle.last_service_date
                + timedelta(days=vehicle.service_date_interval_days)
            )

            mileage_due = (
                vehicle.last_service_odometer is not None
                and vehicle.current_odometer
                >= vehicle.last_service_odometer
                + vehicle.service_mileage_interval
            )

            due = today >= date_due or mileage_due

        if due:
            due_vehicles.append(vehicle)

            if vehicle.service_due_since is not None:
                if today >= vehicle.service_due_since + timedelta(days=7):
                    overdue_vehicles.append(vehicle)

    # -------------------------
    # Vehicles currently in service
    # -------------------------
    in_service_vehicle_ids = (
        db.query(ServiceRecord.vehicle_id)
        .filter(ServiceRecord.status == "IN_SERVICE")
        .distinct()
        .all()
    )

    vehicles_in_service = len(in_service_vehicle_ids)

    # -------------------------
    # Completed this week
    # -------------------------
    start_of_week = today - timedelta(days=today.weekday())

    completed_this_week = (
        db.query(ServiceRecord)
        .filter(
            ServiceRecord.status == "COMPLETED",
            func.date(ServiceRecord.updated_at) >= start_of_week,
        )
        .count()
    )

    # -------------------------
    # Status breakdown
    # -------------------------
    status_rows = (
        db.query(
            ServiceRecord.status,
            func.count(ServiceRecord.id),
        )
        .group_by(ServiceRecord.status)
        .all()
    )

    status_breakdown = {
        status_name: count
        for status_name, count in status_rows
    }

    # -------------------------
    # Technician breakdown
    # -------------------------
    technician_rows = (
        db.query(
            User.id,
            User.email,
            func.count(ServiceTechnician.service_id),
        )
        .join(
            ServiceTechnician,
            ServiceTechnician.technician_id == User.id,
        )
        .filter(User.role == "TECHNICIAN")
        .group_by(User.id, User.email)
        .all()
    )

    technician_breakdown = [
        {
            "technician_id": technician_id,
            "technician_email": email,
            "service_count": count,
        }
        for technician_id, email, count in technician_rows
    ]

    # -------------------------
    # 8-week completion chart
    # -------------------------
    eight_weeks_ago = today - timedelta(days=55)

    completed_records = (
        db.query(ServiceRecord)
        .filter(
            ServiceRecord.status == "COMPLETED",
            func.date(ServiceRecord.updated_at) >= eight_weeks_ago,
        )
        .all()
    )

    weekly_completion = []

    for week_number in range(8):
        week_start = today - timedelta(
            days=today.weekday() + (7 * (7 - week_number))
        )
        week_end = week_start + timedelta(days=6)

        count = sum(
            1
            for service in completed_records
            if week_start
            <= service.updated_at.date()
            <= week_end
        )

        weekly_completion.append(
            {
                "week_start": week_start,
                "week_end": week_end,
                "completed": count,
            }
        )

    return {
        "headline": {
            "vehicles_due": len(due_vehicles),
            "vehicles_in_service": vehicles_in_service,
            "services_completed_this_week": completed_this_week,
            "vehicles_overdue": len(overdue_vehicles),
        },
        "status_breakdown": status_breakdown,
        "technician_breakdown": technician_breakdown,
        "eight_week_completion": weekly_completion,
    }