"""工具模块测试"""

import pytest
from app.utils import setup_utf8_encoding, get_logger


class TestEncoding:
    """测试编码设置"""

    def test_setup_utf8_encoding(self, monkeypatch):
        """测试 UTF-8 编码设置"""
        # 测试函数调用不抛出异常
        setup_utf8_encoding()

        # 验证环境变量已设置
        import os
        assert os.environ.get('PYTHONIOENCODING') == 'utf-8'


class TestLogger:
    """测试日志系统"""

    def test_get_logger(self):
        """测试获取日志记录器"""
        logger = get_logger("test_logger")

        assert logger is not None
        assert logger.name == "test_logger"

    def test_logger_has_handlers(self):
        """测试日志记录器有处理器"""
        logger = get_logger("test_logger")

        # 应该至少有一个处理器
        assert len(logger.handlers) > 0
