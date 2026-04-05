"""
kd-galaxy 适配器常量定义

金蝶云星空 API 常量和配置
"""

from enum import Enum


# =============================================================================
# API 服务配置
# =============================================================================

# API 服务基础路径
API_SERVICE_BASE = "Kingdee.BOS.WebApi.ServicesStub.DynamicFormService"

# API 操作端点
class KingdeeAPIOperations(str, Enum):
    """金蝶云星空标准操作枚举"""

    # 认证相关
    LOGIN_BY_APP_SECRET = "LoginByAppSecret"

    # CRUD 操作
    SAVE = "Save"
    VIEW = "View"
    SUBMIT = "Submit"
    DELETE = "Delete"

    # 审核操作
    AUDIT = "Audit"
    UNAUDIT = "UnAudit"

    # 查询操作
    EXECUTE_BILL_QUERY = "ExecuteBillQuery"
    QUERY_BUSINESS_INFO = "QueryBusinessInfo"

    # 批量操作
    BATCH_SAVE = "BatchSave"


def get_api_url(base_url: str, operation: str | KingdeeAPIOperations) -> str:
    """
    构建完整的 API URL

    Args:
        base_url: API 基础地址 (e.g., https://api.example.com/k3cloud/)
        operation: 操作名称 (e.g., ExecuteBillQuery) 或 KingdeeAPIOperations 枚举

    Returns:
        完整的 API URL
    """
    # 确保 base_url 不以斜杠结尾
    base_url = base_url.rstrip("/")
    # 如果是枚举，获取其值
    if isinstance(operation, KingdeeAPIOperations):
        operation = operation.value
    return f"{base_url}/{API_SERVICE_BASE}.{operation}.common.kdsvc"


# =============================================================================
# 字段类型映射
# =============================================================================

FIELD_TYPE_MAPPING = {
    56: "integer",      # 整数
    61: "datetime",     # 日期时间
    106: "decimal",     # 小数
    127: "base_data",   # 基础资料
    167: "enum",        # 枚举
    175: "enum",        # 单据状态枚举
    231: "string",      # 字符串
}


# =============================================================================
# 默认配置
# =============================================================================

# 默认语言 (简体中文)
DEFAULT_LCID = 2052

# Cookie 缓存有效期 (秒) - 2小时
COOKIE_VALIDITY_SECONDS = 7200

# 默认分页大小
DEFAULT_PAGE_SIZE = 100

# 最大分页大小
MAX_PAGE_SIZE = 10000

# 请求超时 (秒)
REQUEST_TIMEOUT = 300


# =============================================================================
# 认证配置键名
# =============================================================================

class AuthConfigKeys(str, Enum):
    """认证配置键名"""

    ACCT_ID = "acct_id"           # 账套ID (data_center_id)
    USERNAME = "username"          # 用户名
    APP_ID = "app_id"             # 应用ID
    APP_SECRET = "app_secret"     # 应用密钥
    LCID = "lcid"                 # 语言ID
    SERVER_URL = "server_url"     # 服务器URL
    ORG_NUM = "org_num"           # 组织编码


# =============================================================================
# 响应状态码
# =============================================================================

class ResponseStatus:
    """响应状态常量"""

    SUCCESS = "success"
    FAILURE = "failure"
    NETWORK_ERROR = "network_error"


__all__ = [
    "API_SERVICE_BASE",
    "KingdeeAPIOperations",
    "get_api_url",
    "FIELD_TYPE_MAPPING",
    "DEFAULT_LCID",
    "COOKIE_VALIDITY_SECONDS",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "REQUEST_TIMEOUT",
    "AuthConfigKeys",
    "ResponseStatus",
]
