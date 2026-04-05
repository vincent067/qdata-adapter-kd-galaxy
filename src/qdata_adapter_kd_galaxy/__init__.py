"""
qdata-adapter-kd-galaxy

QDataV2 kd-galaxy 平台适配器
金蝶云星空 API 适配器
"""

from qdata_adapter_kd_galaxy.adapter import KdGalaxyAdapter
from qdata_adapter_kd_galaxy.exceptions import (
    KdGalaxyAdapterAPIError,
    KdGalaxyAdapterAuthError,
    KdGalaxyAdapterError,
    KdGalaxyAdapterNotFoundError,
    KdGalaxyAdapterSessionError,
    KdGalaxyAdapterValidationError,
)

__version__ = "0.1.0"

__all__ = [
    "KdGalaxyAdapter",
    "KdGalaxyAdapterError",
    "KdGalaxyAdapterAuthError",
    "KdGalaxyAdapterAPIError",
    "KdGalaxyAdapterValidationError",
    "KdGalaxyAdapterNotFoundError",
    "KdGalaxyAdapterSessionError",
]
