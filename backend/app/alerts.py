from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_manager
from app.database import get_db
from app.models import AlertDismissal, User, Vehicle

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)

GRACE_PERIOD_DAYS = 7


@router.get("")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    today = date.today()

    vehicles = (
        db.query(Vehicle)
        .filter(Vehicle.is_archived == False)
        .all()
    )

    alerts = []

    for vehicle in vehicles:
        if vehicle.service_due_since is None:
            continue

        overdue = today >= (
            vehicle.service_due_since
            + timedelta(days=GRACE_PERIOD_DAYS)
        )

        if not overdue:
            continue

        dismissed = (
            db.query(AlertDismissal)
            .filter(
                AlertDismissal.vehicle_id == vehicle.id,
                AlertDismissal.service_due_since
                == vehicle.service_due_since,
            )
            .first()
        )

        if dismissed:
            continue

        alerts.append(
            {
                "vehicle_id": vehicle.id,
                "registration_number": vehicle.registration_number,
                "service_due_since": vehicle.service_due_since,
                "status": "OVERDUE",
            }
        )

    return {
        "count": len(alerts),
        "items": alerts,
    }


@router.get("/count")
def get_alert_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    result = get_alerts(db, current_user)
    return {"count": result["count"]}


@router.post("/{vehicle_id}/dismiss")
def dismiss_alert(
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
            status_code=404,
            detail="Vehicle not found",
        )

    if vehicle.service_due_since is None:
        raise HTTPException(
            status_code=400,
            detail="Vehicle has no active overdue cycle",
        )

    existing = (
        db.query(AlertDismissal)
        .filter(
            AlertDismissal.vehicle_id == vehicle_id,
            AlertDismissal.service_due_since
            == vehicle.service_due_since,
        )
        .first()
    )

    if existing:
        return {"message": "Alert already dismissed"}

    db.add(
        AlertDismissal(
            vehicle_id=vehicle_id,
            service_due_since=vehicle.service_due_since,
            dismissed_by=current_user.id,
        )
    )

    db.commit()

    return {"message": "Alert dismissed"}