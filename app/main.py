# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.watersheds import router as watersheds_router
from app.api.routes.weather import router as weather_router


app = FastAPI(
    title="EcoHydroAI API",
    description="API backend for the EcoHydroAI Watershed Intelligence Platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://fanzhang0830.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(watersheds_router)
app.include_router(weather_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to EcoHydroAI API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "watersheds": "/api/v1/watersheds",
    }