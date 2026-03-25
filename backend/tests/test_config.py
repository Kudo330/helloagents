"""配置模块测试"""

import os
import pytest
from app.config import Settings


class TestSettings:
    """测试配置"""

    def test_settings_load_from_env(self, monkeypatch):
        """测试从环境变量加载配置"""
        monkeypatch.setenv("AMAP_API_KEY", "test_api_key")
        monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "test_unsplash_key")
        monkeypatch.setenv("LLM_API_KEY", "test_llm_key")

        settings = Settings()

        assert settings.amap_api_key == "test_api_key"
        assert settings.unsplash_access_key == "test_unsplash_key"
        assert settings.llm_api_key == "test_llm_key"

    def test_settings_defaults(self, monkeypatch):
        """测试默认值"""
        monkeypatch.setenv("AMAP_API_KEY", "test_key")

        settings = Settings()

        assert settings.amap_web_key == ""
        assert settings.llm_provider == "auto"
        assert settings.llm_model is None
