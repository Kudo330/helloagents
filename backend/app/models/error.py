"""错误响应模型"""

from typing import Optional, List
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """统一错误响应"""
    success: bool = False
    error: str
    details: Optional[List[ErrorDetail]] = None
    code: Optional[str] = None


class APIError(Exception):
    """API异常基类"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: int = 500
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIError):
    """验证错误"""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=400)
        self.field = field


class ConfigurationError(APIError):
    """配置错误"""

    def __init__(self, message: str):
        super().__init__(message, code="CONFIGURATION_ERROR", status_code=500)


class ExternalAPIError(APIError):
    """外部API错误"""

    def __init__(self, service: str, message: str):
        super().__init__(
            f"{service} 服务暂时不可用，请稍后重试",
            code="EXTERNAL_API_ERROR",
            status_code=503
        )
        self.service = service


class LLMError(APIError):
    """LLM调用错误"""

    def __init__(self, message: str):
        super().__init__(
            f"旅行计划生成失败：{message}",
            code="LLM_ERROR",
            status_code=500
        )
