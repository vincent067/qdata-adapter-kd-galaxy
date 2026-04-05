"""
kd-galaxy 适配器异常定义

金蝶云星空 API 专用异常类型
"""

from typing import Any


class KdGalaxyAdapterError(Exception):
    """
    kd-galaxy 适配器基础异常

    Example:
        >>> raise KdGalaxyAdapterError("操作失败", code="OP_FAILED")
    """

    def __init__(
        self,
        message: str,
        code: str = "KD_GALAXY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class KdGalaxyAdapterAuthError(KdGalaxyAdapterError):
    """
    kd-galaxy 认证失败异常

    Example:
        >>> raise KdGalaxyAdapterAuthError("Invalid credentials")
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, "KD_GALAXY_AUTH_ERROR", details)


class KdGalaxyAdapterAPIError(KdGalaxyAdapterError):
    """
    kd-galaxy API 错误异常

    Attributes:
        status_code: HTTP 状态码
        api_code: kd-galaxy 错误码
        is_success: API 响应中的成功标志

    Example:
        >>> raise KdGalaxyAdapterAPIError(
        ...     "API call failed",
        ...     status_code=500,
        ...     api_code="INTERNAL_ERROR"
        ... )
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        api_code: str | None = None,
        is_success: bool | None = None,
        response_body: dict[str, Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        details = details or {}
        if status_code is not None:
            details["status_code"] = status_code
        if api_code is not None:
            details["api_code"] = api_code
        if is_success is not None:
            details["is_success"] = is_success
        if response_body is not None:
            details["response_body"] = response_body

        super().__init__(message, "KD_GALAXY_API_ERROR", details)
        self.status_code = status_code
        self.api_code = api_code
        self.is_success = is_success
        self.response_body = response_body


class KdGalaxyAdapterValidationError(KdGalaxyAdapterError):
    """
    kd-galaxy 数据验证错误异常

    Example:
        >>> raise KdGalaxyAdapterValidationError(
        ...     "Invalid data",
        ...     field_errors={"FName": "名称不能为空"}
        ... )
    """

    def __init__(
        self,
        message: str,
        field_errors: dict[str, str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        details = details or {}
        if field_errors is not None:
            details["field_errors"] = field_errors
        super().__init__(message, "KD_GALAXY_VALIDATION_ERROR", details)
        self.field_errors = field_errors or {}


class KdGalaxyAdapterNotFoundError(KdGalaxyAdapterError):
    """
    kd-galaxy 资源不存在异常

    Example:
        >>> raise KdGalaxyAdapterNotFoundError(
        ...     "Object not found",
        ...     object_type="SAL_OUTSTOCK",
        ...     object_id="100001"
        ... )
    """

    def __init__(
        self,
        message: str,
        object_type: str | None = None,
        object_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        details = details or {}
        if object_type is not None:
            details["object_type"] = object_type
        if object_id is not None:
            details["object_id"] = object_id
        super().__init__(message, "KD_GALAXY_NOT_FOUND", details)
        self.object_type = object_type
        self.object_id = object_id


class KdGalaxyAdapterSessionError(KdGalaxyAdapterAuthError):
    """
    kd-galaxy 会话失效异常

    当 cookie 过期或会话丢失时抛出此异常
    """

    def __init__(
        self,
        message: str = "Session expired or invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details)
        self.code = "KD_GALAXY_SESSION_ERROR"


__all__ = [
    "KdGalaxyAdapterError",
    "KdGalaxyAdapterAuthError",
    "KdGalaxyAdapterAPIError",
    "KdGalaxyAdapterValidationError",
    "KdGalaxyAdapterNotFoundError",
    "KdGalaxyAdapterSessionError",
]
