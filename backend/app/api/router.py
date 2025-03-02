# backend/app/api/router.py
from fastapi import APIRouter

from app.api import users, auth, hotels, rooms, reservations, keys, verify, passes

api_router = APIRouter()

# Include all API routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(hotels.router, prefix="/hotels", tags=["hotels"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
api_router.include_router(keys.router, prefix="/keys", tags=["digital keys"])
api_router.include_router(verify.router, prefix="/verify", tags=["verification"])
api_router.include_router(passes.router, prefix="/passes", tags=["passes"])
