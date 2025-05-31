from fastapi import APIRouter

from . import auth, records, users

api_router_v1 = APIRouter(prefix='/v1')

api_router_v1.include_router(records.router)
api_router_v1.include_router(auth.router)
api_router_v1.include_router(users.router)
