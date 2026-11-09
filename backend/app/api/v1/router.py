from fastapi import APIRouter

from .routes import analyze, health, metadata, models, overview

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(metadata.router)
api_router.include_router(analyze.router)
api_router.include_router(overview.router)
api_router.include_router(models.router)
