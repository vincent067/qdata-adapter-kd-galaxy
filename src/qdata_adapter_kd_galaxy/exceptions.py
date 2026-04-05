"""
kd-galaxy 适配器异常定义
"""

from qdata_adapter.exceptions import AdapterError, AuthenticationError, ResponseError


class KdGalaxyAdapterError(AdapterError):
    """
    kd-galaxy 适配器基础异常

    Example:
        >>> raise KdGalaxyAdapterError("操作失败", code="OP_FAILED")
    """

    def __init__(self, message: str, code: str = "KD_GALAXY_ERROR", details: dict | None = None):
        super().__init__(message, code, details)


class KdGalaxyAdapterAuthError(AuthenticationError):
    """
    kd-galaxy 认证失败异常

    Example:
        >>> raise KdGalaxyAdapterAuthError("Invalid API key")
    """

    def __init__(self, message: str = "Authentication failed", details: dict | None = None):
        super().__init__(message, "KD_GALAXY_AUTH_ERROR", details)


class KdGalaxyAdapterAPIError(ResponseError):
    """
    kd-galaxy API 错误异常

    Attributes:
        status_code: HTTP 状态码
        api_code: kd-galaxy 错误码

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
        response_body: dict | None = None,
        details: dict | None = None,
    ):
        details = details or {}
        if api_code is not None:
            details["api_code"] = api_code
        super().__init__(message, "KD_GALAXY_API_ERROR", status_code, response_body, details)
        self.api_code = api_code


__all__ = [
    "KdGalaxyAdapterError",
    "KdGalaxyAdapterAuthError",
    "KdGalaxyAdapterAPIError",
]