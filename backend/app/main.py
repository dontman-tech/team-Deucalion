from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import engine, Base
from app.routes import (
    auth_router, 
    students_router, 
    teachers_router, 
    parents_router,
    ai_router,
    admin_router
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered learning companion for Cameroonian students aligned to GCE, BAC, and BEPC curricula"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(students_router, prefix=settings.API_PREFIX)
app.include_router(teachers_router, prefix=settings.API_PREFIX)
app.include_router(parents_router, prefix=settings.API_PREFIX)
app.include_router(ai_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "message": "Welcome to Lumina Cameroon - Your Personal Learning Companion"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get(f"{settings.API_PREFIX}")
async def api_root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "endpoints": {
            "auth": "/auth",
            "students": "/students",
            "teachers": "/teachers",
            "parents": "/parents",
            "ai": "/ai"
        }
    }
