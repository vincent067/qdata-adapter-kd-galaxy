"""
kd-galaxy standard 接口实现

基于金蝶云星空官方 Python SDK 实现
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from k3cloud_webapi_sdk.main import K3CloudApiSdk

from qdata_adapter_kd_galaxy.constants import (
    DEFAULT_LCID,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    AuthConfigKeys,
)

from .base import BaseInterface

if TYPE_CHECKING:
    from qdata_adapter.context import ConnectorContext

logger = logging.getLogger(__name__)


class KdGalaxySDK:
    """
    金蝶云星空 SDK 封装

    封装官方 k3cloud_webapi_sdk，提供更友好的接口
    """

    def __init__(self, base_url: str) -> None:
        self._sdk = K3CloudApiSdk(base_url)
        self._initialized = False

    def configure(
        self,
        acct_id: str,
        username: str,
        app_id: str,
        app_secret: str,
        lcid: int = DEFAULT_LCID,
        org_num: str | None = None,
        server_url: str = "",
    ) -> None:
        """
        配置 SDK 认证参数

        Args:
            acct_id: 账套ID
            username: 用户名
            app_id: 应用ID
            app_secret: 应用密钥
            lcid: 语言ID (默认 2052)
            org_num: 组织编码
            server_url: 服务器URL
        """
        self._sdk.InitConfig(
            acct_id=acct_id,
            user_name=username,
            app_id=app_id,
            app_secret=app_secret,
            server_url=server_url,
            lcid=lcid,
            org_num=org_num or 0,
        )
        self._initialized = True
        logger.debug("SDK configured successfully")

    def is_configured(self) -> bool:
        return self._initialized

    def execute_bill_query(self, params: dict[str, Any]) -> list[Any]:
        """
        执行单据查询

        Args:
            params: 查询参数，包含 FormId, FieldKeys, FilterString 等

        Returns:
            查询结果列表（2D数组格式）
        """
        response = self._sdk.ExecuteBillQuery(params)
        return json.loads(response)

    def view(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        查看单据详情

        Args:
            form_id: 表单ID
            params: 查询参数

        Returns:
            单据详情字典
        """
        response = self._sdk.View(form_id, params)
        result = json.loads(response)
        return result.get("Result", {})

    def save(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        保存单据

        Args:
            form_id: 表单ID
            params: 保存参数

        Returns:
            保存结果
        """
        response = self._sdk.Save(form_id, params)
        return json.loads(response)

    def submit(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """提交单据"""
        response = self._sdk.Submit(form_id, params)
        return json.loads(response)

    def audit(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """审核单据"""
        response = self._sdk.Audit(form_id, params)
        return json.loads(response)

    def unaudit(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """反审核单据"""
        response = self._sdk.UnAudit(form_id, params)
        return json.loads(response)

    def delete(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """删除单据"""
        response = self._sdk.Delete(form_id, params)
        return json.loads(response)

    def batch_save(self, form_id: str, params: dict[str, Any]) -> dict[str, Any]:
        """批量保存单据"""
        response = self._sdk.BatchSave(form_id, params)
        return json.loads(response)

    def excute_operation(
        self,
        form_id: str,
        op_number: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        执行操作（如关闭、打开等）

        Args:
            form_id: 表单ID
            op_number: 操作编码（如 YLBillClose, YLMRPClose）
            params: 操作参数

        Returns:
            操作结果
        """
        response = self._sdk.ExcuteOperation(form_id, op_number, params)
        return json.loads(response)

    def workflow_audit(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        工作流审批

        Args:
            params: 审批参数，包含 FormId, Ids/Numbers, UserId, ApprovalType 等

        Returns:
            审批结果
        """
        response = self._sdk.WorkflowAudit(params)
        return json.loads(response)


class KdGalaxyAdapterStandardInterface(BaseInterface):
    """
    kd-galaxy standard 接口实现

    基于金蝶云星空官方 Python SDK。
    """

    interface_name = "standard"

    def __init__(self, context: ConnectorContext, http_client: Any = None) -> None:
        super().__init__(context, http_client)
        self._sdk: KdGalaxySDK | None = None

    def _get_sdk(self) -> KdGalaxySDK:
        """
        获取或创建 SDK 实例

        Returns:
            KdGalaxySDK 实例

        Raises:
            KdGalaxyAdapterAuthError: 未配置 SDK
        """
        if self._sdk is None:
            from qdata_adapter_kd_galaxy.exceptions import KdGalaxyAdapterAuthError

            base_url = self.context.base_url
            if not base_url:
                auth_config = self.get_auth_config()
                base_url = auth_config.get("base_url", "")

            if not base_url:
                raise KdGalaxyAdapterAuthError(
                    "Missing base_url configuration",
                    details={"base_url": base_url},
                )

            self._sdk = KdGalaxySDK(base_url)
            self._configure_sdk(base_url)

        return self._sdk

    def _configure_sdk(self, server_url: str) -> None:
        """
        配置 SDK 认证参数

        Args:
            server_url: 服务器URL

        Raises:
            KdGalaxyAdapterAuthError: 缺少认证参数
        """
        from qdata_adapter_kd_galaxy.exceptions import KdGalaxyAdapterAuthError

        auth_config = self.get_auth_config()

        acct_id = auth_config.get(AuthConfigKeys.ACCT_ID.value)
        username = auth_config.get(AuthConfigKeys.USERNAME.value)
        app_id = auth_config.get(AuthConfigKeys.APP_ID.value)
        app_secret = auth_config.get(AuthConfigKeys.APP_SECRET.value)
        lcid = auth_config.get(AuthConfigKeys.LCID.value, DEFAULT_LCID)
        org_num = auth_config.get(AuthConfigKeys.ORG_NUM.value)

        if not all([acct_id, username, app_id, app_secret]):
            missing = []
            if not acct_id:
                missing.append(AuthConfigKeys.ACCT_ID.value)
            if not username:
                missing.append(AuthConfigKeys.USERNAME.value)
            if not app_id:
                missing.append(AuthConfigKeys.APP_ID.value)
            if not app_secret:
                missing.append(AuthConfigKeys.APP_SECRET.value)
            raise KdGalaxyAdapterAuthError(
                "Missing required authentication credentials",
                details={"missing": missing},
            )

        self._sdk.configure(
            acct_id=acct_id,
            username=username,
            app_id=app_id,
            app_secret=app_secret,
            lcid=int(lcid) if lcid else DEFAULT_LCID,
            org_num=int(org_num) if org_num else 0,
            server_url=server_url,
        )

    async def authenticate(self) -> dict[str, Any]:
        """
        验证认证配置是否正确

        SDK 在首次调用时会自动进行认证

        Returns:
            认证结果

        Raises:
            KdGalaxyAdapterAuthError: 认证失败
        """
        try:
            sdk = self._get_sdk()
            # 通过执行一个简单查询来验证认证
            sdk.execute_bill_query(
                {
                    "FormId": "BD_MATERIAL",
                    "FieldKeys": "FNumber",
                    "Limit": 1,
                }
            )
            return {
                "authenticated": True,
                "message": "SDK configured successfully",
            }
        except Exception as e:
            from qdata_adapter_kd_galaxy.exceptions import KdGalaxyAdapterAuthError

            raise KdGalaxyAdapterAuthError(
                f"Authentication failed: {e}",
                details={"error": str(e)},
            ) from e

    async def list_objects(
        self,
        object_type: str,
        filters: dict[str, Any] | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        列表查询（自动翻页）

        使用 ExecuteBillQuery 接口查询列表数据

        Args:
            object_type: 表单ID，如 "SAL_OUTSTOCK", "BD_MATERIAL"
            filters: 过滤条件，支持以下键：
                - FieldKeys: str, 逗号分隔的字段名列表
                - FilterString: str, OData 格式过滤条件
                - OrderString: str, 排序条件
                - TopRowCount: int, 返回总行数
                - StartRow: int, 开始行索引
                - Limit: int, 最大行数
            page_size: 每页大小（会被 Limit 覆盖）

        Yields:
            单条记录（字典格式）

        Raises:
            KdGalaxyAdapterAuthError: 认证失败
            KdGalaxyAdapterAPIError: API 调用失败
        """
        filters = filters or {}
        sdk = self._get_sdk()

        # 构建查询参数
        field_keys = filters.get("FieldKeys")
        if not field_keys:
            field_keys = "*"

        query_params = {
            "FormId": object_type,
            "FieldKeys": field_keys,
            "FilterString": filters.get("FilterString", ""),
            "OrderString": filters.get("OrderString", ""),
            "TopRowCount": filters.get("TopRowCount", 0),
            "StartRow": filters.get("StartRow", 0),
            "Limit": min(filters.get("Limit", page_size), MAX_PAGE_SIZE),
            "SubSystemId": filters.get("SubSystemId", ""),
        }

        start_row = query_params["StartRow"]
        limit = query_params["Limit"]
        has_more = True

        while has_more:
            query_params["StartRow"] = start_row
            query_params["Limit"] = limit

            # 执行查询
            data_array = sdk.execute_bill_query(query_params)

            if not data_array or len(data_array) == 0:
                break

            # Kingdee ExecuteBillQuery 返回 2D 数组，每行都是数据
            # FieldKeys 指定了返回哪些字段，需要用它作为表头
            field_keys = query_params.get("FieldKeys", "")
            if field_keys == "*":
                # 如果是 *，则没有表头，只能通过索引访问
                headers = [f"col_{i}" for i in range(len(data_array[0]))]
            else:
                headers = field_keys.split(",")

            for row in data_array:
                # 检测是否是错误响应行
                if self._is_error_row(row, headers):
                    error_msg = self._extract_error_from_row(row, headers)
                    logger.warning(
                        "Skipping row with error response: %s",
                        error_msg,
                    )
                    continue
                record = self._convert_row_to_dict(headers, row)
                yield record

            # 判断是否还有更多数据
            if limit > 0 and len(data_array) < limit:
                has_more = False
            else:
                start_row += len(data_array)
                if not data_array:
                    has_more = False

    def _convert_row_to_dict(self, headers: list, row: list) -> dict[str, Any]:
        """
        将数组格式的行数据转换为字典

        Args:
            headers: 表头列表
            row: 行数据列表

        Returns:
            字典格式的记录
        """
        record = {}
        for i, header in enumerate(headers):
            if i < len(row):
                record[header] = row[i]
        return record

    def _is_error_row(self, row: Any, headers: list) -> bool:
        """
        检测行数据是否是错误响应

        Kingdee API 有时会返回错误信息嵌入在数据行中，
        例如: {"FBillNo": {"Result": {"ResponseStatus": {"ErrorCode": 500, ...}}}}

        Args:
            row: 行数据
            headers: 表头列表

        Returns:
            True 如果是错误响应行
        """
        if not isinstance(row, dict):
            return False

        # 检查是否有任何一个字段值包含错误响应结构
        for header in headers:
            value = row.get(header)
            if isinstance(value, dict) and "Result" in value:
                result = value.get("Result", {})
                if isinstance(result, dict) and "ResponseStatus" in result:
                    return True
        return False

    def _extract_error_from_row(self, row: Any, headers: list) -> str:
        """
        从错误响应行中提取错误信息

        Args:
            row: 行数据
            headers: 表头列表

        Returns:
            错误信息字符串
        """
        for header in headers:
            value = row.get(header)
            if isinstance(value, dict) and "Result" in value:
                result = value.get("Result", {})
                response_status = result.get("ResponseStatus", {})
                errors = response_status.get("Errors", [])
                if errors:
                    return "; ".join(e.get("Message", "Unknown error") for e in errors)
                error_msg = response_status.get("Message", "")
                if error_msg:
                    return error_msg
        return "Unknown error"

    async def get_object(
        self,
        object_type: str,
        object_id: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        获取单个对象

        使用 View 接口查询单据详情

        Args:
            object_type: 表单ID，如 "SAL_OUTSTOCK"
            object_id: 单据ID（可以是单据编号或内码）
            params: 额外参数，如 CreateOrgId

        Returns:
            单据详情字典

        Raises:
            KdGalaxyAdapterAuthError: 认证失败
            KdGalaxyAdapterNotFoundError: 对象不存在
            KdGalaxyAdapterAPIError: API 调用失败
        """
        from qdata_adapter_kd_galaxy.exceptions import (
            KdGalaxyAdapterAPIError,
            KdGalaxyAdapterNotFoundError,
        )

        sdk = self._get_sdk()
        params = params or {}

        view_params = {
            "CreateOrgId": params.get("CreateOrgId", 0),
            "Number": "",
            "Id": "",
        }

        # 判断 object_id 是编号还是内码
        if object_id.isdigit():
            view_params["Id"] = object_id
        else:
            view_params["Number"] = object_id

        if params:
            view_params.update({k: v for k, v in params.items() if k not in view_params})

        try:
            result = sdk.view(object_type, view_params)

            # 检查响应状态
            response_status = result.get("ResponseStatus", {})
            if not response_status.get("IsSuccess"):
                errors = response_status.get("Errors", [])
                error_messages = [e.get("Message", "") for e in errors if isinstance(e, dict)]
                error_msg = error_messages[0] if error_messages else "Unknown error"
                raise KdGalaxyAdapterAPIError(
                    f"Failed to get {object_type}/{object_id}: {error_msg}",
                    response_body=result,
                )

            inner_result = result.get("Result")
            if not inner_result:
                raise KdGalaxyAdapterNotFoundError(
                    f"{object_type} not found",
                    object_type=object_type,
                    object_id=object_id,
                )

            return inner_result

        except (KdGalaxyAdapterNotFoundError, KdGalaxyAdapterAPIError):
            raise
        except Exception as e:
            raise KdGalaxyAdapterAPIError(
                f"Failed to get {object_type}/{object_id}",
                details={"object_type": object_type, "object_id": object_id, "error": str(e)},
            ) from e

    async def create_object(
        self,
        object_type: str,
        data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        创建/保存对象

        使用 Save 接口保存单据

        Args:
            object_type: 表单ID
            data: 单据数据（Model 部分）
            params: 额外参数

        Returns:
            创建结果，包含 Id, Number 等

        Raises:
            KdGalaxyAdapterValidationError: 数据验证失败
            KdGalaxyAdapterAPIError: API 调用失败
        """
        from qdata_adapter_kd_galaxy.exceptions import (
            KdGalaxyAdapterAPIError,
            KdGalaxyAdapterValidationError,
        )

        sdk = self._get_sdk()
        params = params or {}

        save_params = {
            "NeedUpDateFields": [],
            "NeedReturnFields": [],
            "IsDeleteEntry": "True",
            "SubSystemId": "",
            "IsVerifyBaseDataField": "False",
            "IsEntryBatchFill": "True",
            "ValidateFlag": "True",
            "NumberSearch": "True",
            "IsAutoAdjustField": "False",
            "InterationFlags": "",
            "IgnoreInterationFlag": "",
            "IsControlPrecision": "False",
            "ValidateRepeatJson": "False",
            "IsAutoSubmitAndAudit": "False",
            "Model": data,
        }

        save_params.update(params)

        try:
            response = sdk.save(object_type, save_params)

            # 检查保存结果
            result = response.get("Result", {})
            response_status = result.get("ResponseStatus", {})

            if not response_status.get("IsSuccess"):
                errors = response_status.get("Errors", [])
                field_errors = {}
                error_messages = []

                for error in errors:
                    if isinstance(error, dict):
                        field_name = error.get("FieldName", "")
                        message = error.get("Message", "")
                        if field_name:
                            field_errors[field_name] = message
                        error_messages.append(message)

                if field_errors:
                    raise KdGalaxyAdapterValidationError(
                        "Validation failed",
                        field_errors=field_errors,
                        details={"errors": errors},
                    )

                error_msg = error_messages[0] if error_messages else "Unknown error"
                raise KdGalaxyAdapterAPIError(
                    f"Failed to create {object_type}: {error_msg}",
                    response_body=response,
                )

            # 返回保存结果
            return {
                "Id": result.get("Id"),
                "Number": result.get("Number"),
                "SuccessEntitys": response_status.get("SuccessEntitys", []),
                "ResponseStatus": response_status,
            }

        except (KdGalaxyAdapterValidationError, KdGalaxyAdapterAPIError):
            raise
        except Exception as e:
            raise KdGalaxyAdapterAPIError(
                f"Failed to create {object_type}",
                details={"object_type": object_type, "error": str(e)},
            ) from e

    async def update_object(
        self,
        object_type: str,
        object_id: str,
        data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        更新对象

        使用 Save 接口更新单据（通过 Model 中的 FID 标识为更新操作）

        金蝶 Save API 支持两种模式：
        - 不带 FID 或 FID=0：创建新单据
        - 带 FID（有效值）：更新已有单据

        Args:
            object_type: 表单ID
            object_id: 单据内码（FID），用于构建更新数据
            data: 单据数据（Model 部分），应包含 FID
            params: 额外参数，如 NeedUpDateFields 指定需要更新的字段

        Returns:
            更新结果，包含 Id, Number 等

        Raises:
            KdGalaxyAdapterValidationError: 数据验证失败
            KdGalaxyAdapterAPIError: API 调用失败
        """
        from qdata_adapter_kd_galaxy.exceptions import (
            KdGalaxyAdapterAPIError,
            KdGalaxyAdapterValidationError,
        )

        sdk = self._get_sdk()
        params = params or {}

        # 确保 data 中包含 FID（用于标识为更新操作）
        update_data = dict(data) if data else {}
        if "FID" not in update_data and object_id:
            update_data["FID"] = int(object_id) if object_id.isdigit() else object_id

        # 构建更新参数
        # NeedUpDateFields 指定需要更新的字段，为空表示更新所有字段
        save_params = {
            "NeedUpDateFields": params.get("NeedUpDateFields", []),
            "NeedReturnFields": params.get("NeedReturnFields", []),
            "IsDeleteEntry": params.get("IsDeleteEntry", "False"),  # 更新时通常不删除分录
            "SubSystemId": "",
            "IsVerifyBaseDataField": "False",
            "IsEntryBatchFill": "True",
            "ValidateFlag": "True",
            "NumberSearch": "True",
            "IsAutoAdjustField": "False",
            "InterationFlags": "",
            "IgnoreInterationFlag": "",
            "IsControlPrecision": "False",
            "ValidateRepeatJson": "False",
            "IsAutoSubmitAndAudit": "False",
            "Model": update_data,
        }

        # 更新特定字段时的额外参数
        if "NeedUpDateFields" in params:
            save_params.update(
                {
                    k: v
                    for k, v in params.items()
                    if k in ("NeedUpDateFields", "NeedReturnFields", "IsDeleteEntry")
                }
            )

        try:
            response = sdk.save(object_type, save_params)

            # 检查保存结果
            result = response.get("Result", {})
            response_status = result.get("ResponseStatus", {})

            if not response_status.get("IsSuccess"):
                errors = response_status.get("Errors", [])
                field_errors = {}
                error_messages = []

                for error in errors:
                    if isinstance(error, dict):
                        field_name = error.get("FieldName", "")
                        message = error.get("Message", "")
                        if field_name:
                            field_errors[field_name] = message
                        error_messages.append(message)

                if field_errors:
                    raise KdGalaxyAdapterValidationError(
                        "Validation failed",
                        field_errors=field_errors,
                        details={"errors": errors},
                    )

                error_msg = error_messages[0] if error_messages else "Unknown error"
                raise KdGalaxyAdapterAPIError(
                    f"Failed to update {object_type}/{object_id}: {error_msg}",
                    response_body=response,
                )

            # 返回更新结果
            return {
                "Id": result.get("Id"),
                "Number": result.get("Number"),
                "SuccessEntitys": response_status.get("SuccessEntitys", []),
                "ResponseStatus": response_status,
            }

        except (KdGalaxyAdapterValidationError, KdGalaxyAdapterAPIError):
            raise
        except Exception as e:
            raise KdGalaxyAdapterAPIError(
                f"Failed to update {object_type}/{object_id}",
                details={"object_type": object_type, "object_id": object_id, "error": str(e)},
            ) from e

    async def submit_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """提交单据"""
        return await self._submit_audit_operation(
            object_type, "submit", object_id=object_id, numbers=numbers, params=params
        )

    async def audit_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """审核单据"""
        return await self._submit_audit_operation(
            object_type, "audit", object_id=object_id, numbers=numbers, params=params
        )

    async def unaudit_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """反审核单据"""
        return await self._submit_audit_operation(
            object_type, "unaudit", object_id=object_id, numbers=numbers, params=params
        )

    async def delete_object(
        self,
        object_type: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """删除单据"""
        return await self._submit_audit_operation(
            object_type, "delete", object_id=object_id, numbers=numbers, params=params
        )

    async def _submit_audit_operation(
        self,
        object_type: str,
        operation: str,
        object_id: str | None = None,
        numbers: list[str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行提交流/审核/反审核/删除操作

        Args:
            object_type: 表单ID
            operation: 操作类型 (submit/audit/unaudit/delete)
            object_id: 单据内码
            numbers: 单据编号列表
            params: 额外参数

        Returns:
            操作结果
        """
        from qdata_adapter_kd_galaxy.exceptions import KdGalaxyAdapterAPIError

        sdk = self._get_sdk()
        params = params or {}

        op_params = {
            "CreateOrgId": params.get("CreateOrgId", 0),
            "Numbers": numbers or [],
            "Ids": object_id or "",
            "SelectedPostId": params.get("SelectedPostId", 0),
            "NetworkCtrl": params.get("NetworkCtrl", ""),
            "IgnoreInterationFlag": params.get("IgnoreInterationFlag", ""),
        }

        try:
            if operation == "submit":
                response = sdk.submit(object_type, op_params)
            elif operation == "audit":
                response = sdk.audit(object_type, op_params)
            elif operation == "unaudit":
                response = sdk.unaudit(object_type, op_params)
            elif operation == "delete":
                response = sdk.delete(object_type, op_params)
            else:
                raise ValueError(f"Unknown operation: {operation}")

            result = response.get("Result", {})
            response_status = result.get("ResponseStatus", {})

            if not response_status.get("IsSuccess"):
                errors = response_status.get("Errors", [])
                error_messages = [e.get("Message", "") for e in errors if isinstance(e, dict)]
                raise KdGalaxyAdapterAPIError(
                    f"{operation} failed: {', '.join(error_messages) or 'Unknown error'}",
                    response_body=response,
                )

            return {
                "SuccessEntitys": response_status.get("SuccessEntitys", []),
                "ResponseStatus": response_status,
            }

        except KdGalaxyAdapterAPIError:
            raise
        except Exception as e:
            raise KdGalaxyAdapterAPIError(
                f"{operation} operation failed",
                details={"object_type": object_type, "operation": operation, "error": str(e)},
            ) from e

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
        if method in ("query", "list", "list_objects"):
            results = []
            async for item in self.list_objects(object_type, filters=params, page_size=100):
                results.append(item)
            return {"data": results, "total": len(results)}

        elif method in ("get", "view"):
            object_id = params.get("id") if params else (params.get("Number") if params else None)
            if not object_id:
                raise ValueError("'get' method requires params['id'] or params['Number']")
            result = await self.get_object(object_type, object_id, params)
            return {"data": result}

        elif method in ("create", "save"):
            if not data:
                raise ValueError("'create' method requires data")
            result = await self.create_object(object_type, data, params)
            return {"data": result}

        elif method == "submit":
            result = await self.submit_object(
                object_type,
                object_id=params.get("id") if params else None,
                numbers=params.get("Numbers") if params else None,
                params=params,
            )
            return {"data": result}

        elif method == "audit":
            result = await self.audit_object(
                object_type,
                object_id=params.get("id") if params else None,
                numbers=params.get("Numbers") if params else None,
                params=params,
            )
            return {"data": result}

        elif method == "unaudit":
            result = await self.unaudit_object(
                object_type,
                object_id=params.get("id") if params else None,
                numbers=params.get("Numbers") if params else None,
                params=params,
            )
            return {"data": result}

        elif method == "delete":
            result = await self.delete_object(
                object_type,
                object_id=params.get("id") if params else None,
                numbers=params.get("Numbers") if params else None,
                params=params,
            )
            return {"data": result}

        elif method == "excute_operation":
            result = await self.excute_operation(object_type, params=params)
            return {"data": result}

        elif method == "workflow_audit":
            result = await self.workflow_audit(params=params)
            return {"data": result}

        else:
            raise NotImplementedError(
                f"Method '{method}' not implemented. "
                f"Supported methods: query, list, get, view, create, save, "
                f"submit, audit, unaudit, delete, excute_operation, workflow_audit"
            )

    async def excute_operation(
        self,
        object_type: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        执行操作（如关闭、打开等）

        Args:
            object_type: 表单ID
            params: 操作参数，包含 opNumber, Numbers/Ids 等

        Returns:
            操作结果
        """
        from qdata_adapter_kd_galaxy.exceptions import KdGalaxyAdapterAPIError

        sdk = self._get_sdk()
        params = params or {}

        op_number = params.pop("opNumber", "")
        if not op_number:
            raise ValueError("'excute_operation' requires params['opNumber']")

        try:
            response = sdk.excute_operation(object_type, op_number, params)

            result = response.get("Result", {})
            response_status = result.get("ResponseStatus", {})

            if not response_status.get("IsSuccess"):
                errors = response_status.get("Errors", [])
                error_messages = [e.get("Message", "") for e in errors if isinstance(e, dict)]
                raise KdGalaxyAdapterAPIError(
                    f"excute_operation failed: {', '.join(error_messages) or 'Unknown error'}",
                    response_body=response,
                )

            return {
                "SuccessEntitys": response_status.get("SuccessEntitys", []),
                "ResponseStatus": response_status,
            }
        except KdGalaxyAdapterAPIError:
            raise
        except Exception as e:
            raise KdGalaxyAdapterAPIError(
                "excute_operation failed",
                details={"object_type": object_type, "error": str(e)},
            ) from e

    async def workflow_audit(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        工作流审批

        Args:
            params: 审批参数，包含 FormId, Ids/Numbers, UserId, ApprovalType 等

        Returns:
            审批结果
        """
        from qdata_adapter_kd_galaxy.exceptions import KdGalaxyAdapterAPIError

        sdk = self._get_sdk()
        params = params or {}

        form_id = params.get("FormId")
        if not form_id:
            raise ValueError("'workflow_audit' requires params['FormId']")

        try:
            response = sdk.workflow_audit(params)

            result = response.get("Result", {})
            response_status = result.get("ResponseStatus", {})

            if not response_status.get("IsSuccess"):
                errors = response_status.get("Errors", [])
                error_messages = [e.get("Message", "") for e in errors if isinstance(e, dict)]
                raise KdGalaxyAdapterAPIError(
                    f"workflow_audit failed: {', '.join(error_messages) or 'Unknown error'}",
                    response_body=response,
                )

            return {
                "SuccessEntitys": response_status.get("SuccessEntitys", []),
                "ResponseStatus": response_status,
            }
        except KdGalaxyAdapterAPIError:
            raise
        except Exception as e:
            raise KdGalaxyAdapterAPIError(
                "workflow_audit failed",
                details={"error": str(e)},
            ) from e

    async def health_check(self) -> bool:
        """
        健康检查

        通过查询业务对象信息来检查连接

        Returns:
            True: 连接正常
            False: 连接异常
        """
        try:
            sdk = self._get_sdk()
            # 执行一个简单查询来验证连接
            sdk.execute_bill_query(
                {
                    "FormId": "BD_MATERIAL",
                    "FieldKeys": "FNumber",
                    "Limit": 1,
                }
            )
            return True
        except Exception as e:
            logger.warning("Health check failed: %s", e)
            return False


__all__ = ["KdGalaxyAdapterStandardInterface"]
