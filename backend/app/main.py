from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.services import router as services_router
from app.auth import router as auth_router
from app.vehicles import router as vehicles_router
from app.dashboard import router as dashboard_router
from app.alerts import router as alerts_router


app = FastAPI(title="Fleet Maintenance API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://busy-fleet-maintenance.vercel.app",
        "https://busy-fleet-maintenance-a9l4gjsx1-busy-fleet.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vehicles_router)
app.include_router(services_router)
app.include_router(dashboard_router)
app.include_router(alerts_router)

@app.get("/")
def root():
    return {"message": "Fleet Maintenance API is running"}