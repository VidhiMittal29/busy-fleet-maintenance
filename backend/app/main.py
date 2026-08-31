from fastapi import FastAPI

from app.auth import router as auth_router


app = FastAPI(title="Fleet Maintenance API")

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "Fleet Maintenance API is running"}