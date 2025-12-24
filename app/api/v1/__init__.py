"""
API v1 router aggregating all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, contacts, deals, properties

api_router = APIRouter(prefix="/api/v1")

# Include authentication routes
api_router.include_router(auth.router)

# Include CRM routes
api_router.include_router(contacts.router)
api_router.include_router(deals.router)

# Include Real Estate routes
api_router.include_router(properties.router)
