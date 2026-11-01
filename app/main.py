from fastapi import FastAPI
from app.routes import services

app = FastAPI(
    title="Online Examination System",
    description="Backend API for Online Examination System",
    version="1.0.0"
)

app.include_router(services.router)
