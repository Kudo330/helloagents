"""服务模块测试"""

import pytest
from app.services.unsplash_service import UnsplashService
from app.services.amap_service import AMapService


class TestUnsplashService:
    """测试 Unsplash 服务"""

    def test_unsplash_service_init(self):
        """测试服务初始化"""
        service = UnsplashService("test_key")

        assert service.access_key == "test_key"
        assert service.base_url == "https://api.unsplash.com"

    @pytest.mark.skip(reason="需要真实的 Unsplash API Key")
    def test_search_photos(self):
        """测试搜索图片（需要真实API）"""
        service = UnsplashService("your_key_here")
        photos = service.search_photos("travel", per_page=5)

        assert len(photos) <= 5


class TestAMapService:
    """测试高德地图服务"""

    def test_amap_service_init(self):
        """测试服务初始化"""
        # 需要设置环境变量
        import os
        os.environ["AMAP_API_KEY"] = "test_key"

        service = AMapService()

        assert service.api_key == "test_key"
        assert service.base_url == "https://restapi.amap.com/v3"

    def test_format_poi(self):
        """测试 POI 格式化"""
        service = AMapService()

        poi = {
            "name": "测试景点",
            "address": "测试地址",
            "location": "120.1,30.2",
            "typecode": "110101",
            "tel": "123456789",
            "cost": "100",
            "business_area": "西湖区"
        }

        formatted = service._format_poi(poi)

        assert formatted["name"] == "测试景点"
        assert formatted["address"] == "测试地址"
        assert formatted["location"]["longitude"] == 120.1
        assert formatted["location"]["latitude"] == 30.2
