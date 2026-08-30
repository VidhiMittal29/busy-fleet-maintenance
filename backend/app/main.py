from fastapi import FastAPI

app = FastAPI(title="Fleet Maintenance API")


@app.get("/")
def root():
    return {"message": "Fleet Maintenance API is running"}