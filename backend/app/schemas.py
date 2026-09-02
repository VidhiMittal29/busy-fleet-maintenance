from datetime import date, datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }

class VehicleCreate(BaseModel):
    registration_number: str
    make: str
    model: str
    current_odometer: int = 0
    service_date_interval_days: int
    service_mileage_interval: int


class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    make: str
    model: str
    current_odometer: int
    service_date_interval_days: int
    service_mileage_interval: int
    last_service_date: date | None
    last_service_odometer: int | None
    service_due_since: date | None
    is_archived: bool

    model_config = {
        "from_attributes": True
    }

class VehicleUpdate(BaseModel):
    registration_number: str | None = None
    make: str | None = None
    model: str | None = None
    current_odometer: int | None = None
    service_date_interval_days: int | None = None
    service_mileage_interval: int | None = None

class ServiceRecordCreate(BaseModel):
    vehicle_id: int
    description: str
    scheduled_date: date | None = None


class ServiceRecordResponse(BaseModel):
    id: int
    vehicle_id: int
    description: str
    status: str
    scheduled_date: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class ServiceStatusUpdate(BaseModel):
    status: str


class TechnicianAssignment(BaseModel):
    technician_id: int

class ServiceBooking(BaseModel):
    scheduled_date: date
    technician_ids: list[int]

class ServiceNote(BaseModel):
    note: str