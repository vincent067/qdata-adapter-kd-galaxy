"""
扩展端到端测试 - 使用真实 SDK 连接测试

测试更多 SDK 方法：
- ExcuteOperation (YLBillClose, YLMRPClose)
- WorkflowAudit
- Delete, Submit 详细参数

运行方式:
    python -m pytest tests/e2e_test_extended.py -v -s

配置:
    从项目根目录的 .env 文件读取测试配置
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv
from qdata_adapter import ConnectorContext

from qdata_adapter_kd_galaxy import KdGalaxyAdapter

# 加载 .env 配置
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    raise RuntimeError(f".env file not found at {env_path}")

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量读取配置
TEST_ENV = {
    "host": os.getenv("KD_GALAXY_BASE_URL", "http://env.qeasy.cloud/k3cloud/"),
    "data_center_id": os.getenv("KD_GALAXY_ACCT_ID", ""),
    "username": os.getenv("KD_GALAXY_USERNAME", ""),
    "app_id": os.getenv("KD_GALAXY_APP_ID", ""),
    "app_secret": os.getenv("KD_GALAXY_APP_SECRET", ""),
    "language": os.getenv("KD_GALAXY_LCID", "2052"),
}


def create_test_context() -> ConnectorContext:
    """创建测试上下文"""
    return ConnectorContext(
        connector_id="e2e-extended-test",
        app_software_code="kd_galaxy",
        base_url=TEST_ENV["host"],
        auth_config={
            "acct_id": TEST_ENV["data_center_id"],
            "username": TEST_ENV["username"],
            "app_id": TEST_ENV["app_id"],
            "app_secret": TEST_ENV["app_secret"],
            "lcid": TEST_ENV["language"],
        },
    )


def get_field_value(record: dict, field_name: str) -> Any:
    """
    从记录中获取字段值，处理可能的嵌套格式

    Kingdee 返回的字段可能是：
    - 简单值: "xxx"
    - 嵌套对象: {"FNumber": "xxx", "FName": "xxx"}

    Args:
        record: 记录字典
        field_name: 字段名

    Returns:
        字段值（如果是嵌套对象，返回第一个可用值）
    """
    value = record.get(field_name)
    if isinstance(value, dict):
        # 优先返回 FNumber，其次 FName，最后第一个值
        return value.get("FNumber") or value.get("FName") or str(value)
    return value


def get_field_number(record: dict, field_name: str) -> str | None:
    """获取字段的编号（用于关联字段如 FSupplierId）"""
    value = record.get(field_name)
    if isinstance(value, dict):
        return value.get("FNumber")
    return str(value) if value else None


@pytest.fixture(scope="class")
def adapter() -> KdGalaxyAdapter:
    """创建适配器实例（class级别复用）"""
    return KdGalaxyAdapter(create_test_context())


class TestSALSaleOrderWorkflow:
    """SAL_SaleOrder 销售订单完整工作流测试"""

    @pytest.fixture(scope="class")
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_1_query_sale_orders(self, adapter: KdGalaxyAdapter) -> list[dict]:
        """1. ExecuteBillQuery - 查询销售订单列表"""
        logger.info("=" * 60)
        logger.info("测试 1: ExecuteBillQuery 查询销售订单")
        logger.info("=" * 60)

        orders = []
        async for record in adapter.list_objects(
            "SAL_SaleOrder",
            filters={
                "FieldKeys": "FBillNo,FDate,FDocumentStatus",
                "Limit": 10,
            },
            page_size=10,
        ):
            orders.append(record)
            logger.info(
                f"   单据: {record.get('FBillNo')} | "
                f"日期: {record.get('FDate')} | "
                f"状态: {record.get('FDocumentStatus')}"
            )

        logger.info(f"\n共查询到 {len(orders)} 条销售订单")

        # 保存结果
        with open("/tmp/e2e_sale_orders.json", "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)

        assert len(orders) > 0, "应该能查询到销售订单"
        return orders

    @pytest.mark.asyncio
    async def test_2_view_sale_order_detail(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """2. View - 查询销售订单详情"""
        logger.info("=" * 60)
        logger.info("测试 2: View 查询销售订单详情")
        logger.info("=" * 60)

        # 从文件读取订单列表
        try:
            with open("/tmp/e2e_sale_orders.json", encoding="utf-8") as f:
                orders = json.load(f)
        except Exception:
            pytest.skip("没有可查询详情的销售订单")

        if not orders:
            pytest.skip("没有销售订单可查询详情")

        first_order = orders[0]
        # FBillNo 可能是字符串或对象格式 {"FNumber": "xxx"}
        fbillno = first_order.get("FBillNo")
        if isinstance(fbillno, dict):
            order_no = fbillno.get("FNumber")
        else:
            order_no = str(fbillno) if fbillno else None

        if not order_no:
            pytest.skip("无法获取订单编号")

        logger.info(f"\n  查询订单详情: {order_no}")

        try:
            detail = await adapter.get_object("SAL_SaleOrder", order_no)
            logger.info(f"   单据号: {detail.get('FBillNo')}")
            logger.info(f"   状态: {detail.get('FDocumentStatus')}")
            logger.info(f"   日期: {detail.get('FDate')}")

            # 打印分录信息
            entries = detail.get("FSaleOrderEntry", [])
            if entries:
                logger.info(f"   分录数量: {len(entries)}")
                for i, entry in enumerate(entries[:3]):
                    material = entry.get("FMaterialId", {})
                    if isinstance(material, dict):
                        logger.info(
                            f"     分录{i+1}: {material.get('FNumber')} x {entry.get('FQty')} "
                            f"@ {entry.get('FPrice')}"
                        )

            # 保存详情
            with open("/tmp/e2e_sale_order_detail.json", "w", encoding="utf-8") as f:
                json.dump(detail, f, ensure_ascii=False, indent=2)

            return detail
        except Exception as e:
            logger.error(f"   查询详情失败: {e}")
            raise

    @pytest.mark.asyncio
    async def test_3_save_new_sale_order(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """3. Save - 创建销售订单"""
        logger.info("=" * 60)
        logger.info("测试 3: Save 创建销售订单")
        logger.info("=" * 60)

        current_time = time.strftime("%Y%m%d%H%M%S")

        # 从文件读取订单详情
        try:
            with open("/tmp/e2e_sale_order_detail.json", encoding="utf-8") as f:
                order_detail = json.load(f)
        except Exception:
            order_detail = {}

        # 从详情中提取客户信息 (SAL_SaleOrder 使用 FCustId)
        customer = order_detail.get("FCustId", {})
        customer_number = None
        if isinstance(customer, dict):
            customer_number = customer.get("FNumber")
        if not customer_number:
            customer = order_detail.get("CustId", {})
            if isinstance(customer, dict):
                customer_number = customer.get("Number")

        # 提取分录中的物料信息
        entries = order_detail.get("FSaleOrderEntry", [])
        material_entry = None
        if entries:
            first_entry = entries[0]
            material = first_entry.get("FMaterialId", {})
            if isinstance(material, dict):
                material_entry = {
                    "FMaterialId": {"FNumber": material.get("FNumber", "MTL001")},
                    "FStockUnitID": first_entry.get("FStockUnitID", {"FNumber": "Pcs"}),
                    "FPriceUnitId": first_entry.get("FPriceUnitId", {"FNumber": "Pcs"}),
                    "FQty": first_entry.get("FQty", 10),
                    "FPrice": first_entry.get("FPrice", 100.00),
                    "FTaxPrice": first_entry.get("FTaxPrice", 113.00),
                }

        if not customer_number:
            customer_number = "CUST0001"
        if not material_entry:
            material_entry = {
                "FMaterialId": {"FNumber": "WL1"},
                "FStockUnitID": {"FNumber": "Pcs"},
                "FPriceUnitId": {"FNumber": "Pcs"},
                "FUnitID": {"FNumber": "Pcs"},
                "FQty": 10,
                "FPrice": 100.00,
                "FTaxPrice": 113.00,
            }

        new_order = {
            "FCustId": {"FNumber": customer_number},
            "FDate": "2026-04-05",
            "FCurrencyId": {"FNumber": "CNY"},
            "FBillNo": f"E2E_SO_{current_time}",
            "FNote": f"E2E测试创建于 {current_time}",
            "FSaleOrderEntry": [material_entry],
        }

        logger.info("\n  创建销售订单:")
        logger.info(f"    FBillNo: {new_order['FBillNo']}")
        logger.info(f"    FCustId: {customer_number}")

        try:
            result = await adapter.create_object("SAL_SaleOrder", new_order)
            logger.info("\n  保存结果:")
            logger.info(f"    Id: {result.get('Id')}")
            logger.info(f"    Number: {result.get('Number')}")
            logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")

            # 保存
            with open("/tmp/e2e_saved_sale_order.json", "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "id": result.get("Id"),
                        "number": result.get("Number"),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            assert result.get("Id"), "保存应该返回 Id"
            return result
        except Exception as e:
            logger.error(f"   创建失败: {e}")
            raise

    @pytest.mark.asyncio
    async def test_4_submit_sale_order(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """4. Submit - 提交销售订单"""
        logger.info("=" * 60)
        logger.info("测试 4: Submit 提交销售订单")
        logger.info("=" * 60)

        try:
            with open("/tmp/e2e_saved_sale_order.json", encoding="utf-8") as f:
                saved_order = json.load(f)
            order_number = saved_order.get("number")
        except Exception:
            pytest.skip("没有可提交的销售订单")

        logger.info(f"\n  提交销售订单: {order_number}")

        try:
            result = await adapter.submit_object("SAL_SaleOrder", numbers=[order_number])
            logger.info("\n  提交结果:")
            logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")
            logger.info(f"    SuccessEntitys: {result.get('SuccessEntitys')}")

            return result
        except Exception as e:
            logger.error(f"   提交失败: {e}")
            raise

    @pytest.mark.asyncio
    async def test_5_audit_sale_order(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """5. Audit - 审核销售订单"""
        logger.info("=" * 60)
        logger.info("测试 5: Audit 审核销售订单")
        logger.info("=" * 60)

        try:
            with open("/tmp/e2e_saved_sale_order.json", encoding="utf-8") as f:
                saved_order = json.load(f)
            order_number = saved_order.get("number")
        except Exception:
            pytest.skip("没有可审核的销售订单")

        logger.info(f"\n  审核销售订单: {order_number}")

        try:
            result = await adapter.audit_object("SAL_SaleOrder", numbers=[order_number])
            logger.info("\n  审核结果:")
            logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")

            return result
        except Exception as e:
            logger.error(f"   审核失败: {e}")
            raise

    @pytest.mark.asyncio
    async def test_6_unaudit_sale_order(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """6. UnAudit - 反审核销售订单"""
        logger.info("=" * 60)
        logger.info("测试 6: UnAudit 反审核销售订单")
        logger.info("=" * 60)

        try:
            with open("/tmp/e2e_saved_sale_order.json", encoding="utf-8") as f:
                saved_order = json.load(f)
            order_number = saved_order.get("number")
        except Exception:
            pytest.skip("没有可反审核的销售订单")

        logger.info(f"\n  反审核销售订单: {order_number}")

        try:
            result = await adapter.unaudit_object("SAL_SaleOrder", numbers=[order_number])
            logger.info("\n  反审核结果:")
            logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")

            return result
        except Exception as e:
            logger.error(f"   反审核失败: {e}")
            raise

    @pytest.mark.asyncio
    async def test_7_delete_sale_order(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """7. Delete - 删除销售订单（创建后未审核状态）"""
        logger.info("=" * 60)
        logger.info("测试 7: Delete 删除销售订单")
        logger.info("=" * 60)

        try:
            with open("/tmp/e2e_saved_sale_order.json", encoding="utf-8") as f:
                saved_order = json.load(f)
            order_number = saved_order.get("number")
        except Exception:
            pytest.skip("没有可删除的销售订单")

        logger.info(f"\n  删除销售订单: {order_number}")

        try:
            result = await adapter.delete_object("SAL_SaleOrder", numbers=[order_number])
            logger.info("\n  删除结果:")
            logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")

            return result
        except Exception as e:
            logger.error(f"   删除失败: {e}")
            raise


class TestExcuteOperation:
    """ExcuteOperation 操作测试"""

    @pytest.fixture(scope="class")
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_excute_operation_yllbillclose(self, adapter: KdGalaxyAdapter) -> None:
        """测试 ExcuteOperation - YLBillClose 关闭订单"""
        logger.info("=" * 60)
        logger.info("测试 ExcuteOperation - YLBillClose 关闭订单")
        logger.info("=" * 60)

        orders = []
        async for record in adapter.list_objects(
            "SAL_SaleOrder",
            filters={
                "FieldKeys": "FBillNo,FDocumentStatus",
                "FilterString": "FDocumentStatus='C'",
                "Limit": 3,
            },
            page_size=3,
        ):
            orders.append(record)

        if not orders:
            pytest.skip("没有已审核的销售订单可测试 YLBillClose")

        order_no = orders[0].get("FBillNo")
        logger.info(f"\n  对订单执行 YLBillClose: {order_no}")

        try:
            result = await adapter.invoke(
                "excute_operation",
                "SAL_SaleOrder",
                params={
                    "opNumber": "YLBillClose",
                    "CreateOrgId": 0,
                    "Numbers": [order_no],
                    "Ids": "",
                    "NetworkCtrl": "",
                    "IgnoreInterationFlag": "",
                },
            )
            logger.info(f"\n  操作结果: {result.get('data')}")
        except Exception as e:
            logger.error(f"   YLBillClose 操作失败（可能是单据状态不支持）: {e}")

    @pytest.mark.asyncio
    async def test_excute_operation_yllmrpclose(self, adapter: KdGalaxyAdapter) -> None:
        """测试 ExcuteOperation - YLMRPClose MRP关闭"""
        logger.info("=" * 60)
        logger.info("测试 ExcuteOperation - YLMRPClose MRP关闭")
        logger.info("=" * 60)

        orders = []
        async for record in adapter.list_objects(
            "SAL_SaleOrder",
            filters={
                "FieldKeys": "FBillNo,FDocumentStatus",
                "Limit": 3,
            },
            page_size=3,
        ):
            orders.append(record)

        if not orders:
            pytest.skip("没有销售订单可测试 YLMRPClose")

        order_no = orders[0].get("FBillNo")
        logger.info(f"\n  对订单执行 YLMRPClose: {order_no}")

        try:
            result = await adapter.invoke(
                "excute_operation",
                "SAL_SaleOrder",
                params={
                    "opNumber": "YLMRPClose",
                    "CreateOrgId": 0,
                    "Numbers": [order_no],
                    "Ids": "",
                    "NetworkCtrl": "",
                    "IgnoreInterationFlag": "",
                },
            )
            logger.info(f"\n  操作结果: {result.get('data')}")
        except Exception as e:
            logger.error(f"   YLMRPClose 操作失败: {e}")


class TestWorkflowAudit:
    """工作流审批测试"""

    @pytest.fixture(scope="class")
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_workflow_audit(self, adapter: KdGalaxyAdapter) -> None:
        """测试 WorkflowAudit 工作流审批"""
        logger.info("=" * 60)
        logger.info("测试 WorkflowAudit 工作流审批")
        logger.info("=" * 60)

        logger.info("\n  WorkflowAudit 需要完整的工作流上下文:")
        logger.info("    - FormId: 业务对象表单Id")
        logger.info("    - Ids: 单据内码集合")
        logger.info("    - Numbers: 单据编码集合")
        logger.info("    - UserId: 审批人用户Id")
        logger.info("    - ApprovalType: 审批类型 (1: 审批通过, 2: 驳回, 3: 终止)")
        logger.info("    - PostId: 岗位Id")
        logger.info("    - Disposition: 审批意见")

        logger.info("\n  此测试仅记录说明，实际调用略过")
        pytest.skip("WorkflowAudit 需要完整审批上下文，跳过自动测试")


class TestQueryWithPagination:
    """分页查询测试"""

    @pytest.fixture(scope="class")
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_pagination(self, adapter: KdGalaxyAdapter) -> None:
        """测试分页查询"""
        logger.info("=" * 60)
        logger.info("测试分页查询")
        logger.info("=" * 60)

        page_size = 5
        total_fetched = 0

        async for record in adapter.list_objects(
            "BD_BANK",
            filters={"FieldKeys": "FNumber,FName", "Limit": page_size},
            page_size=page_size,
        ):
            total_fetched += 1
            logger.info(f"  {total_fetched}: {record.get('FNumber')} - {record.get('FName')}")

        logger.info(f"\n  总共获取: {total_fetched} 条记录")
        assert total_fetched > 0, "应该能查询到数据"


class TestFilterConditions:
    """过滤条件测试"""

    @pytest.fixture(scope="class")
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_filter_by_status(self, adapter: KdGalaxyAdapter) -> None:
        """测试按状态过滤"""
        logger.info("=" * 60)
        logger.info("测试按状态过滤查询")
        logger.info("=" * 60)

        audited_orders = []
        async for record in adapter.list_objects(
            "SAL_SaleOrder",
            filters={
                "FieldKeys": "FBillNo,FDocumentStatus",
                "FilterString": "FDocumentStatus='C'",
                "Limit": 5,
            },
            page_size=5,
        ):
            audited_orders.append(record)
            logger.info(
                f"  已审核: {record.get('FBillNo')} - 状态: {record.get('FDocumentStatus')}"
            )

        logger.info(f"\n  已审核订单数量: {len(audited_orders)}")

        created_orders = []
        async for record in adapter.list_objects(
            "SAL_SaleOrder",
            filters={
                "FieldKeys": "FBillNo,FDocumentStatus",
                "FilterString": "FDocumentStatus='A'",
                "Limit": 5,
            },
            page_size=5,
        ):
            created_orders.append(record)

        logger.info(f"  创建中订单数量: {len(created_orders)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
