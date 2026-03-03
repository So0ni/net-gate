from fastapi import APIRouter

from api.devices import router as devices_router
from api.profiles import router as profiles_router

api_router = APIRouter()
api_router.include_router(devices_router)
api_router.include_router(profiles_router)
