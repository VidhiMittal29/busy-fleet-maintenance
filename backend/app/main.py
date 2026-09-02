from fastapi import FastAPI
from app.services import router as services_router
from app.auth import router as auth_router
from app.vehicles import router as vehicles_router


app = FastAPI(title="Fleet Maintenance API")

app.include_router(services_router)
app.include_router(auth_router)
app.include_router(vehicles_router)


@app.get("/")
def root():
    return {"message": "Fleet Maintenance API is running"}