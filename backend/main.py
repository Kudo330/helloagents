"""HelloAgents Trip Planner 后端入口"""

# 设置 UTF-8 编码 - 必须在任何其他导入之前设置
from app.utils import setup_utf8_encoding

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    settings = get_settings()

    app = FastAPI(
        title="HelloAgents Trip Planner API",
        description="基于多智能体的旅行规划助手",
        version="1.0.0"
    )

    # 配置 CORS
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix="/api")

    @app.get("/")
    async def root():
        return {"message": "HelloAgents Trip Planner API", "status": "running"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
