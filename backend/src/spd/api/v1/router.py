"""Aggregates every v1 router behind a single mount point."""

from fastapi import APIRouter

from spd.api.v1 import auth, cohort, events, health, leaderboard, students

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(students.router, tags=["students"])
api_router.include_router(leaderboard.router, tags=["leaderboard"])
api_router.include_router(cohort.router, tags=["cohort"])
api_router.include_router(events.router, tags=["events"])
