from fastapi import APIRouter

from app.api.routes import trip_router

# 创建主路由器
api_router = APIRouter()

# 注册子路由
api_router.include_router(trip_router, prefix="/trip", tags=["trip"])

__all__ = ["api_router"]
