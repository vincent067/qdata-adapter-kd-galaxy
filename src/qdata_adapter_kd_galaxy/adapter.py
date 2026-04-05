"""
KdGalaxyAdapter

适配器主类 - 组合器模式实现
单一接口适配器实现

金蝶云星空 API 基于 Cookie 会话的 WebAPI
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from qdata_adapter import BaseAppAdapter
from qdata_adapter.context import ConnectorContext
from qdata_adapter import TestConnectionResult

from qdata_adapter_kd_galaxy.interfaces.base import BaseInterface
from qdata_adapter_kd_galaxy.interfaces.standard import KdGalaxyAdapterStandardInterface

logger = logging.getLogger(__name__)


class KdGalaxyAdapter(BaseAppAdapter):
    """
    kd-galaxy 适配器

    标准适配器实现，基于金蝶云星空 standard 接口。

    金蝶云星空 API 特点：
    - Cookie-based 会话认证
    - ExecuteBillQuery 用于列表查询
    - View 用于单条查询
    - Save/Submit/Audit/UnAudit/Delete 用于单据操作

    Example:
        >>> context = ConnectorContext(
        ...     connector_id="my-connector",
        ...     app_software_code="kd_galaxy",
        ...     base_url="https://api.example.com/k3cloud/",
        ...     auth_config={
        ...         "acct_id": "YOUR_DATA_CENTER_ID",
        ...         "username": "YOUR_USERNAME",
        ...         "app_id": "YOUR_APP_ID",
        ...         "app_secret": "YOUR_APP_SECRET",
        ...     },
        ... )
        >>> adapter = KdGalaxyAdapter(context)
        >>> result = await adapter.test_connection()
    """

    app_code = "kd_galaxy"
    adapter_version = "0.1.0"

    def __init__(self, context: ConnectorContext, token_cache: Any = None) -> None:
        """
        初始化适配器

        Args:
            context: 连接器上下文
            token_cache: Token 缓存（可选）

        Note:
            context.settings.interface 控制接口路由：
            - "standard"（默认）
        """
        super().__init__(context, token_cache)
        self._interface = self._resolve_interface()
        logger.debug(
            "Initialized KdGalaxyAdapter with %s interface",
            self._interface.interface_name
        )

    def _resolve_interface(self) -> BaseInterface:
        """
        根据 settings 路由到对应的接口实现

        Returns:
            接口实现实例
        """
        # 单一接口模式 - 始终使用 standard 接口
        return KdGalaxyAdapterStandardInterface(self.context)

    async def authenticate(self) -> dict[str, Any]:
        """
        获取认证凭证

        委托给当前接口实现进行 Cookie 会话认证
        """
        return await self._interface.authenticate()

    async def refresh_token(self) -> dict[str, Any]:
        """
        刷新认证凭证

        金蝶云星空使用 Cookie 会话，不需要刷新
        重新调用 authenticate() 获取新会话
        """
        return await self._interface.authenticate()

    async def list_objects(
        self,
        object_type: str,
        filters: dict[str, Any] | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        列表查询（自动翻页）

        使用 ExecuteBillQuery 接口查询列表数据

        Args:
            object_type: 表单ID，如 "SAL_OUTSTOCK", "BD_MATERIAL"
            filters: 过滤条件，支持 FieldKeys, FilterString, OrderString 等
            page_size: 每页大小

        Yields:
            单条记录字典
        """
        async for item in self._interface.list_objects(object_type, filters, page_size):
            yield item

    async def query_objects(
        self,
        object_type: str,
        filters: dict[str, Any] | None = None,
        page_size: int = 100,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        查询对象列表（工作流节点优先使用此方法）

        这是 list_objects() 的别名，用于与工作流节点的契约匹配。

        Args:
            object_type: 对象类型
            filters: 过滤条件
            page_size: 每页大小

        Yields:
            单条记录字典
        """
        async for item in self._interface.list_objects(object_type, filters, page_size):
            yield item

    async def get_object(self, object_type: str, object_id: str) -> dict[str, Any]:
        """
        获取单个对象

        使用 View 接口查询单据详情

        Args:
            object_type: 表单ID
            object_id: 单据ID（编号或内码）

        Returns:
            单据详情字典
        """
        return await self._interface.get_object(object_type, object_id)

    async def create_object(self, object_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        创建对象

        使用 Save 接口保存单据

        Args:
            object_type: 表单ID
            data: 单据数据

        Returns:
            创建结果
        """
        return await self._interface.create_object(object_type, data)

    async def submit_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        提交单据

        Args:
            object_type: 表单ID
            object_id: 单据内码
            numbers: 单据编号列表

        Returns:
            提交结果
        """
        return await self._interface.submit_object(
            object_type, object_id=object_id, numbers=numbers
        )

    async def audit_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        审核单据

        Args:
            object_type: 表单ID
            object_id: 单据内码
            numbers: 单据编号列表

        Returns:
            审核结果
        """
        return await self._interface.audit_object(
            object_type, object_id=object_id, numbers=numbers
        )

    async def unaudit_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        反审核单据

        Args:
            object_type: 表单ID
            object_id: 单据内码
            numbers: 单据编号列表

        Returns:
            反审核结果
        """
        return await self._interface.unaudit_object(
            object_type, object_id=object_id, numbers=numbers
        )

    async def delete_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        删除单据

        Args:
            object_type: 表单ID
            object_id: 单据内码
            numbers: 单据编号列表

        Returns:
            删除结果
        """
        return await self._interface.delete_object(
            object_type, object_id=object_id, numbers=numbers
        )

    async def invoke(
        self,
        method: str,
        object_type: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        统一的 API 调用方法

        支持金蝶云星空的所有标准操作：
        - query/list: ExecuteBillQuery 列表查询
        - get/view: View 单条查询
        - create/save: Save 保存
        - submit: Submit 提交
        - audit: Audit 审核
        - unaudit: UnAudit 反审核
        - delete: Delete 删除

        Args:
            method: API 方法名
            object_type: 表单ID
            data: 请求体数据
            params: 查询参数

        Returns:
            API 响应数据
        """
        return await self._interface.invoke(method, object_type, data, params)

    async def test_connection(self) -> TestConnectionResult:
        """
        测试连接

        检查与 kd-galaxy 平台的连接是否正常

        Returns:
            连接测试结果
        """
        import time

        start_time = time.time()

        try:
            if await self._interface.health_check():
                return TestConnectionResult.connected(
                    message=f"kd-galaxy 连接成功",
                    duration_ms=int((time.time() - start_time) * 1000),
                    metadata={
                        "interface": self._interface.interface_name,
                        "base_url": self.context.base_url,
                    },
                )
            else:
                return TestConnectionResult.network_error(
                    message="健康检查失败",
                    duration_ms=int((time.time() - start_time) * 1000),
                )

        except Exception as e:
            logger.error("Connection test failed: %s", e)
            return TestConnectionResult.network_error(
                message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
                details={"error": str(e)},
            )

    def get_interface_info(self) -> dict[str, Any]:
        """
        获取当前接口信息

        Returns:
            接口信息字典
        """
        return {
            "interface_name": self._interface.interface_name,
            "available_interfaces": ["standard"],
            "adapter_version": self.adapter_version,
            "app_code": self.app_code,
        }


__all__ = ["KdGalaxyAdapter"]
