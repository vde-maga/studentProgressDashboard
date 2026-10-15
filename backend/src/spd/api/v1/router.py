"""Aggregates every v1 router behind a single mount point."""

from fastapi import APIRouter

from spd.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
