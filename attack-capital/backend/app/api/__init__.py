"""
API Router package for the Attack Capital backend
"""
from fastapi import APIRouter

router = APIRouter()

# Import and include all API routers
from .token_endpoint import router as token_router

router.include_router(token_router, prefix="/token", tags=["token"])
