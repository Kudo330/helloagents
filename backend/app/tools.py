"""工具配置和集成"""

from app.services.amap_service import AMapService
from app.services.unsplash_service import UnsplashService
from app.config import get_settings


# 初始化服务
_settings = get_settings()

# 高德地图服务
amap_service = AMapService()

# Unsplash 图片服务
unsplash_service = UnsplashService(_settings.unsplash_access_key)


def get_amap_service() -> AMapService:
    """获取高德地图服务实例"""
    return amap_service


def get_unsplash_service() -> UnsplashService:
    """获取 Unsplash 服务实例"""
    return unsplash_service


# MCP 工具配置（保留用于将来的扩展）
def create_amap_mcp_tool():
    """创建高德地图 MCP 工具配置（已集成到 AMapService）"""
    # 注意：当前实现使用直接的 REST API 调用，更稳定可靠
    # MCP 工具功能已通过 AMapService 实现
    return None
