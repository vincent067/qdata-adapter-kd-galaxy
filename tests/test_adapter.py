"""
适配器测试

测试 KdGalaxyAdapter 的核心功能

基于金蝶云星空官方 Python SDK
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qdata_adapter_kd_galaxy import KdGalaxyAdapter
from qdata_adapter import ConnectorContext


class TestKdGalaxyAdapter:
    """KdGalaxyAdapter 测试类"""

    @pytest.fixture
    def mock_sdk(self) -> MagicMock:
        """创建 mock SDK 实例"""
        mock = MagicMock()
        mock.configure_mock(**{
            "is_configured.return_value": True,
            # Kingdee ExecuteBillQuery 返回 2D 数组，每行都是数据
            # FieldKeys 指定了字段顺序，数据行顺序对应
            "execute_bill_query.return_value": [
                ["物料1", "MTL001", {"FNumber": "MTL001", "FName": "物料1"}],
                ["物料2", "MTL002", {"FNumber": "MTL002", "FName": "物料2"}],
            ],
            "view.return_value": {
                "ResponseStatus": {"IsSuccess": True},
                "Result": {
                    "Id": 100001,
                    "BillNo": "SAL001",
                    "DocumentStatus": "C",
                },
            },
            "save.return_value": {
                "Result": {
                    "ResponseStatus": {
                        "IsSuccess": True,
                        "SuccessEntitys": [{"Id": 100002, "Number": "SAL_NEW_001"}],
                    },
                    "Id": 100002,
                    "Number": "SAL_NEW_001",
                }
            },
            "audit.return_value": {
                "Result": {
                    "ResponseStatus": {
                        "IsSuccess": True,
                        "SuccessEntitys": [{"Id": 100001, "Number": "SAL001"}],
                    }
                }
            },
            "submit.return_value": {
                "Result": {
                    "ResponseStatus": {
                        "IsSuccess": True,
                        "SuccessEntitys": [{"Id": 100001, "Number": "SAL001"}],
                    }
                }
            },
        })
        return mock

    @pytest.fixture
    def mock_sdk_class(self, mock_sdk: MagicMock) -> MagicMock:
        """Mock KdGalaxySDK 类"""
        mock_class = MagicMock(return_value=mock_sdk)
        return mock_class

    @pytest.mark.asyncio
    async def test_adapter_initialization(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
    ) -> None:
        """测试适配器初始化"""
        adapter = KdGalaxyAdapter(standard_context, mock_token_cache)

        assert adapter.app_code == "kd_galaxy"
        assert adapter.adapter_version == "0.1.0"
        assert adapter.context == standard_context

    @pytest.mark.asyncio
    async def test_authenticate_success(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试标准接口认证成功"""
        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            result = await adapter.authenticate()

            assert result["authenticated"] is True

    @pytest.mark.asyncio
    async def test_authenticate_failure(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试认证失败"""
        mock_sdk = mock_sdk_class.return_value
        mock_sdk.execute_bill_query.side_effect = Exception("Authentication failed")

        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)

            with pytest.raises(Exception):
                await adapter.authenticate()

    @pytest.mark.asyncio
    async def test_list_objects_success(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试列表查询成功"""
        # 设置 mock 返回值
        mock_sdk = mock_sdk_class.return_value
        mock_sdk.execute_bill_query.return_value = [
            ["物料1", "MTL001", {"FNumber": "MTL001", "FName": "物料1"}],
            ["物料2", "MTL002", {"FNumber": "MTL002", "FName": "物料2"}],
        ]

        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            records = []
            async for record in adapter.list_objects(
                "BD_MATERIAL",
                filters={"FieldKeys": "FName,FNumber,FMaterialId"},
                page_size=100,
            ):
                records.append(record)

            assert len(records) == 2
            assert records[0]["FName"] == "物料1"
            assert records[0]["FNumber"] == "MTL001"
            assert records[1]["FName"] == "物料2"

    @pytest.mark.asyncio
    async def test_list_objects_with_filters(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试带过滤条件的列表查询"""
        mock_sdk = mock_sdk_class.return_value
        # Kingdee 返回 2D 数组，每行都是数据，没有表头行
        mock_sdk.execute_bill_query.return_value = [
            ["SAL001", "2026-01-01", 1000.00],
            ["SAL002", "2026-01-02", 2000.00],
        ]

        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            filters = {
                "FieldKeys": "FBillNo,FDate,FAmount",
                "FilterString": "FDocumentStatus='C'",
                "Limit": 50,
            }
            records = []
            async for record in adapter.list_objects("SAL_OUTSTOCK", filters=filters, page_size=50):
                records.append(record)

            assert len(records) == 2
            assert records[0]["FBillNo"] == "SAL001"

    @pytest.mark.asyncio
    async def test_get_object_success(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试获取单个对象"""
        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            result = await adapter.get_object("SAL_OUTSTOCK", "SAL001")

            assert result["BillNo"] == "SAL001"
            assert result["DocumentStatus"] == "C"
            assert result["Id"] == 100001

    @pytest.mark.asyncio
    async def test_create_object_success(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试创建对象"""
        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            data = {
                "FMaterialId": {"FNumber": "MTL001"},
                "FQuantity": 50,
            }
            result = await adapter.create_object("SAL_OUTSTOCK", data)

            assert result["Id"] == 100002
            assert result["Number"] == "SAL_NEW_001"

    @pytest.mark.asyncio
    async def test_test_connection_success(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试连接测试 - 成功场景"""
        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            result = await adapter.test_connection()

            assert result.success is True
            assert result.status == "connected"

    @pytest.mark.asyncio
    async def test_test_connection_failure(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试连接测试 - 失败场景"""
        mock_sdk = mock_sdk_class.return_value
        mock_sdk.execute_bill_query.side_effect = Exception("Connection failed")

        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            result = await adapter.test_connection()

            assert result.success is False
            assert result.status == "network_error"

    @pytest.mark.asyncio
    async def test_invoke_query(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试 invoke 方法 - query 操作"""
        mock_sdk = mock_sdk_class.return_value
        # Kingdee 返回 2D 数组，每行都是数据
        mock_sdk.execute_bill_query.return_value = [
            ["Customer1", "C001"],
            ["Customer2", "C002"],
        ]

        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            result = await adapter.invoke("query", "BD_CUSTOMER", params={"Limit": 50})

            assert "data" in result
            assert result["total"] == 2
            assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_invoke_audit(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
        mock_sdk_class: MagicMock,
    ) -> None:
        """测试 invoke 方法 - audit 操作"""
        with patch(
            "qdata_adapter_kd_galaxy.interfaces.standard.KdGalaxySDK",
            mock_sdk_class,
        ):
            adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
            result = await adapter.invoke(
                "audit", "SAL_OUTSTOCK", params={"Numbers": ["SAL001"]}
            )

            assert "data" in result
            assert result["data"]["ResponseStatus"]["IsSuccess"] is True

    @pytest.mark.asyncio
    async def test_get_interface_info(
        self,
        standard_context: ConnectorContext,
        mock_token_cache: Any,
    ) -> None:
        """测试获取接口信息"""
        adapter = KdGalaxyAdapter(standard_context, mock_token_cache)
        info = adapter.get_interface_info()

        assert "interface_name" in info
        assert "available_interfaces" in info
        assert info["adapter_version"] == "0.1.0"
        assert info["app_code"] == "kd_galaxy"
        assert info["interface_name"] == "standard"


__all__ = ["TestKdGalaxyAdapter"]
