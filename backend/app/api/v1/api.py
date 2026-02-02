from fastapi import APIRouter
from app.api.v1.endpoints import chat, escalations, auth, clinician

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(escalations.router, prefix="/escalations", tags=["escalations"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(clinician.router, prefix="/clinician", tags=["clinician"])
