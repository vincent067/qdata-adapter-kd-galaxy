"""
端到端测试 - 使用真实 SDK 连接测试

运行方式:
    python -m pytest tests/e2e_test.py -v -s

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
    "host": os.getenv("KD_GALAXY_BASE_URL", "https://api.example.com/k3cloud/"),
    "data_center_id": os.getenv("KD_GALAXY_ACCT_ID", ""),
    "username": os.getenv("KD_GALAXY_USERNAME", ""),
    "app_id": os.getenv("KD_GALAXY_APP_ID", ""),
    "app_secret": os.getenv("KD_GALAXY_APP_SECRET", ""),
    "language": os.getenv("KD_GALAXY_LCID", "2052"),
}


def create_test_context() -> ConnectorContext:
    """创建测试上下文"""
    return ConnectorContext(
        connector_id="e2e-test-connector",
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


@pytest.fixture
def adapter() -> KdGalaxyAdapter:
    """创建适配器实例"""
    context = create_test_context()
    return KdGalaxyAdapter(context)


class TestBDBankE2E:
    """BD_BANK 银行基础资料端到端测试"""

    @pytest.fixture
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_1_execute_bill_query(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """1. 通过 ExecuteBillQuery 查询现有银行资料"""
        logger.info("=" * 60)
        logger.info("测试 1: ExecuteBillQuery 查询银行资料列表")
        logger.info("=" * 60)

        records = []
        async for record in adapter.list_objects(
            "BD_BANK",
            filters={
                "FieldKeys": "FNumber,FName,FBankType,FIsDefault",
                "Limit": 20,
            },
            page_size=20,
        ):
            records.append(record)
            logger.info(f"  银行: {record.get('FNumber')} - {record.get('FName')}")

        logger.info(f"\n共查询到 {len(records)} 条银行记录")

        # 保存结果供后续使用
        with open("/tmp/e2e_bank_list.json", "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        assert len(records) > 0, "应该能查询到银行资料"
        return records

    @pytest.mark.asyncio
    async def test_2_view_bank_details(self, adapter: KdGalaxyAdapter) -> list[dict]:
        """2. 通过 View 查询银行详情"""
        logger.info("=" * 60)
        logger.info("测试 2: View 查询银行详情")
        logger.info("=" * 60)

        # 先查询列表
        records = []
        async for record in adapter.list_objects(
            "BD_BANK",
            filters={"FieldKeys": "FNumber,FName", "Limit": 3},
            page_size=3,
        ):
            records.append(record)

        if not records:
            pytest.skip("没有银行数据可查询详情")

        # 查询前3个银行详情
        bank_details = []
        for bank in records:
            bank_number = bank.get("FNumber")
            try:
                detail = await adapter.get_object("BD_BANK", bank_number)
                bank_details.append(detail)
                logger.info(f"\n  银行 {bank_number} 详情:")
                logger.info(f"    FNumber: {detail.get('FNumber')}")
                logger.info(f"    FName: {detail.get('FName')}")
            except Exception as e:
                logger.error(f"  查询银行 {bank_number} 详情失败: {e}")

        # 保存详情
        with open("/tmp/e2e_bank_details.json", "w", encoding="utf-8") as f:
            json.dump(bank_details, f, ensure_ascii=False, indent=2)

        assert len(bank_details) > 0, "应该能查询到至少一个银行详情"
        return bank_details

    @pytest.mark.asyncio
    async def test_3_save_new_bank(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """3. 通过 Save 保存新银行"""
        logger.info("=" * 60)
        logger.info("测试 3: Save 保存新银行")
        logger.info("=" * 60)

        current_time = time.strftime("%Y%m%d%H%M%S")

        new_bank_data = {
            "FCreateOrgId": {"FNumber": "100"},
            "FUseOrgId": {"FNumber": "100"},
            "FNumber": f"TEST_BANK_{current_time}",
            "FName": f"测试银行_{current_time}",
            "FRemark": f"E2E测试创建于 {current_time}",
        }

        logger.info("\n  创建银行:")
        logger.info(f"    FNumber: {new_bank_data['FNumber']}")
        logger.info(f"    FName: {new_bank_data['FName']}")

        result = await adapter.create_object("BD_BANK", new_bank_data)
        logger.info("\n  保存结果:")
        logger.info(f"    Id: {result.get('Id')}")
        logger.info(f"    Number: {result.get('Number')}")
        logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")

        # 保存到临时文件
        with open("/tmp/e2e_saved_bank.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id": result.get("Id"),
                    "number": result.get("Number"),
                    "data": new_bank_data,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        assert result.get("Id"), "保存应该返回 Id"
        return result

    @pytest.mark.asyncio
    async def test_4_submit_bank(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """4. 通过 Submit 提交银行（审核前必须先提交）"""
        logger.info("=" * 60)
        logger.info("测试 4: Submit 提交银行")
        logger.info("=" * 60)

        # 读取刚创建的银行
        try:
            with open("/tmp/e2e_saved_bank.json", encoding="utf-8") as f:
                saved_bank = json.load(f)
            bank_number = saved_bank.get("number")
        except Exception:
            pytest.skip("没有可提交的银行")

        logger.info(f"\n  提交银行: {bank_number}")

        result = await adapter.submit_object("BD_BANK", numbers=[bank_number])
        logger.info("\n  提交结果:")
        logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")
        logger.info(f"    SuccessEntitys: {result.get('SuccessEntitys')}")

        return result

    @pytest.mark.asyncio
    async def test_5_audit_bank(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """5. 通过 Audit 审核银行"""
        logger.info("=" * 60)
        logger.info("测试 5: Audit 审核银行")
        logger.info("=" * 60)

        # 读取刚创建的银行
        try:
            with open("/tmp/e2e_saved_bank.json", encoding="utf-8") as f:
                saved_bank = json.load(f)
            bank_number = saved_bank.get("number")
        except Exception:
            pytest.skip("没有可审核的银行")

        logger.info(f"\n  审核银行: {bank_number}")

        result = await adapter.audit_object("BD_BANK", numbers=[bank_number])
        logger.info("\n  审核结果:")
        logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")
        logger.info(f"    SuccessEntitys: {result.get('SuccessEntitys')}")

        return result

    @pytest.mark.asyncio
    async def test_6_unaudit_bank(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """6. 通过 UnAudit 反审核银行"""
        logger.info("=" * 60)
        logger.info("测试 6: UnAudit 反审核银行")
        logger.info("=" * 60)

        # 读取刚创建的银行
        try:
            with open("/tmp/e2e_saved_bank.json", encoding="utf-8") as f:
                saved_bank = json.load(f)
            bank_number = saved_bank.get("number")
        except Exception:
            pytest.skip("没有可反审核的银行")

        logger.info(f"\n  反审核银行: {bank_number}")

        result = await adapter.unaudit_object("BD_BANK", numbers=[bank_number])
        logger.info("\n  反审核结果:")
        logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")
        logger.info(f"    SuccessEntitys: {result.get('SuccessEntitys')}")

        return result

    @pytest.mark.asyncio
    async def test_7_delete_bank(self, adapter: KdGalaxyAdapter) -> dict[str, Any]:
        """7. 通过 Delete 删除银行（反审核后可删除）"""
        logger.info("=" * 60)
        logger.info("测试 7: Delete 删除银行")
        logger.info("=" * 60)

        # 读取刚创建的银行
        try:
            with open("/tmp/e2e_saved_bank.json", encoding="utf-8") as f:
                saved_bank = json.load(f)
            bank_number = saved_bank.get("number")
        except Exception:
            pytest.skip("没有可删除的银行")

        logger.info(f"\n  删除银行: {bank_number}")

        result = await adapter.delete_object("BD_BANK", numbers=[bank_number])
        logger.info("\n  删除结果:")
        logger.info(f"    Success: {result.get('ResponseStatus', {}).get('IsSuccess')}")
        logger.info(f"    SuccessEntitys: {result.get('SuccessEntitys')}")

        return result


class TestPURPurchaseOrderE2E:
    """PUR_PurchaseOrder 采购订单端到端测试"""

    @pytest.fixture
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_full_purchase_order_workflow(self, adapter: KdGalaxyAdapter) -> None:
        """完整采购订单工作流测试"""
        logger.info("\n" + "=" * 60)
        logger.info("完整采购订单工作流测试")
        logger.info("=" * 60)

        current_time = time.strftime("%Y%m%d%H%M%S")

        # 1. 查询采购订单列表
        logger.info("\n1. ExecuteBillQuery - 查询采购订单列表")
        orders = []
        async for record in adapter.list_objects(
            "PUR_PurchaseOrder",
            filters={
                "FieldKeys": "FBillNo,FDate,FSupplierId,FDocumentStatus",
                "Limit": 5,
            },
            page_size=5,
        ):
            orders.append(record)
            supplier = record.get("FSupplierId", {})
            if isinstance(supplier, dict):
                supplier_name = supplier.get("FName", "")
            else:
                supplier_name = str(supplier)
            logger.info(
                f"   单据: {record.get('FBillNo')} - 供应商: {supplier_name} - 状态: {record.get('FDocumentStatus')}"
            )

        logger.info(f"\n  成功获取 {len(orders)} 条采购订单")

        if not orders:
            pytest.skip("没有采购订单可测试")

        # 2. 查看采购订单详情
        first_order = orders[0]
        first_order_no = first_order.get("FBillNo")
        logger.info(f"\n2. View - 查询采购订单详情: {first_order_no}")

        try:
            order_detail = await adapter.get_object("PUR_PurchaseOrder", first_order_no)
            logger.info(f"   单据号: {order_detail.get('FBillNo')}")
            logger.info(f"   状态: {order_detail.get('FDocumentStatus')}")

            supplier = order_detail.get("FSupplierId", {})
            if isinstance(supplier, dict):
                logger.info(f"   供应商: {supplier.get('FName')} ({supplier.get('FNumber')})")

            # 保存详情
            with open("/tmp/e2e_po_detail.json", "w", encoding="utf-8") as f:
                json.dump(order_detail, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"   查询详情失败: {e}")

        # 3. 创建采购订单
        logger.info("\n3. Save - 创建采购订单")

        supplier = orders[0].get("FSupplierId", {})
        supplier_number = None
        if isinstance(supplier, dict):
            supplier_number = supplier.get("FNumber")

        if supplier_number:
            new_order_data = {
                "FSupplierId": {"FNumber": supplier_number},
                "FDate": "2026-04-05",
                "FCurrencyId": {"FNumber": "CNY"},
                "FBillNo": f"E2E_PO_{current_time}",
                "FNote": f"E2E测试创建于 {current_time}",
            }

            try:
                create_result = await adapter.create_object("PUR_PurchaseOrder", new_order_data)
                new_order_id = create_result.get("Id")
                new_order_no = create_result.get("Number")
                logger.info(f"   创建成功: Id={new_order_id}, Number={new_order_no}")

                # 保存创建结果
                with open("/tmp/e2e_po_saved.json", "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "id": new_order_id,
                            "number": new_order_no,
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )

                # 4. 提交
                if new_order_no:
                    logger.info("\n4. Submit - 提交采购订单")
                    submit_result = await adapter.submit_object(
                        "PUR_PurchaseOrder", numbers=[new_order_no]
                    )
                    logger.info(
                        f"   提交结果: {submit_result.get('ResponseStatus', {}).get('IsSuccess')}"
                    )

                    # 5. 审核
                    logger.info("\n5. Audit - 审核采购订单")
                    audit_result = await adapter.audit_object(
                        "PUR_PurchaseOrder", numbers=[new_order_no]
                    )
                    logger.info(
                        f"   审核结果: {audit_result.get('ResponseStatus', {}).get('IsSuccess')}"
                    )

                    # 6. 反审核
                    logger.info("\n6. UnAudit - 反审核采购订单")
                    unaudit_result = await adapter.unaudit_object(
                        "PUR_PurchaseOrder", numbers=[new_order_no]
                    )
                    logger.info(
                        f"   反审核结果: {unaudit_result.get('ResponseStatus', {}).get('IsSuccess')}"
                    )

            except Exception as e:
                logger.error(f"   操作失败: {e}")
        else:
            logger.warning("   无法获取供应商信息，跳过创建测试")

        logger.info("\n" + "=" * 60)
        logger.info("采购订单工作流测试完成!")
        logger.info("=" * 60)


class TestInvokeInterface:
    """通过 invoke 接口测试"""

    @pytest.fixture
    def adapter(self) -> KdGalaxyAdapter:
        return KdGalaxyAdapter(create_test_context())

    @pytest.mark.asyncio
    async def test_invoke_query(self, adapter: KdGalaxyAdapter) -> None:
        """测试 invoke 方法 - query"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 invoke('query', ...) 接口")
        logger.info("=" * 60)

        result = await adapter.invoke(
            "query",
            "BD_BANK",
            params={"FieldKeys": "FNumber,FName", "Limit": 3},
        )

        logger.info("\n  查询结果:")
        logger.info(f"    total: {result.get('total')}")
        logger.info(f"    data count: {len(result.get('data', []))}")

        for item in result.get("data", []):
            logger.info(f"    - {item.get('FNumber')}: {item.get('FName')}")

        assert "data" in result
        assert result.get("total") >= 0

    @pytest.mark.asyncio
    async def test_invoke_get(self, adapter: KdGalaxyAdapter) -> None:
        """测试 invoke 方法 - get"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 invoke('get', ...) 接口")
        logger.info("=" * 60)

        # 先查询一个银行编号
        result = await adapter.invoke(
            "query",
            "BD_BANK",
            params={"FieldKeys": "FNumber,FName", "Limit": 1},
        )

        if result.get("data") and len(result.get("data", [])) > 0:
            bank_no = result["data"][0].get("FNumber")

            # 然后用 get 获取详情
            get_result = await adapter.invoke("get", "BD_BANK", params={"id": bank_no})

            logger.info(f"\n  获取银行 {bank_no} 详情:")
            logger.info(f"    FNumber: {get_result.get('data', {}).get('FNumber')}")
            logger.info(f"    FName: {get_result.get('data', {}).get('FName')}")

            assert "data" in get_result
        else:
            pytest.skip("没有银行数据可测试")

    @pytest.mark.asyncio
    async def test_invoke_save(self, adapter: KdGalaxyAdapter) -> None:
        """测试 invoke 方法 - save"""
        logger.info("\n" + "=" * 60)
        logger.info("测试 invoke('save', ...) 接口")
        logger.info("=" * 60)

        current_time = time.strftime("%Y%m%d%H%M%S")

        save_data = {
            "FCreateOrgId": {"FNumber": "100"},
            "FUseOrgId": {"FNumber": "100"},
            "FNumber": f"E2E_INVOKE_{current_time}",
            "FName": f"E2E调用测试_{current_time}",
            "FRemark": f"invoke测试于 {current_time}",
        }

        result = await adapter.invoke("save", "BD_BANK", data=save_data)

        logger.info("\n  保存结果:")
        logger.info(f"    Id: {result.get('data', {}).get('Id')}")
        logger.info(f"    Number: {result.get('data', {}).get('Number')}")

        assert "data" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
