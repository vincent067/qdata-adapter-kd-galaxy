# kd-galaxy API 文档

> kd-galaxy (金蝶云星空) API 文档和接口参考

## 文档来源

### 官方文档

- **API 平台**: 金蝶云星空 WebAPI
- **认证方式**: Cookie-Based 会话认证 (LoginByAppSecret)
- **服务基础路径**: `Kingdee.BOS.WebApi.ServicesStub.DynamicFormService`

### 本目录文件说明

```
api-docs/
├── README.md                 # 本文件
├── apis_list.json          # API 清单（完整表单列表）
└── details/                 # 各表单 API 详情
    ├── BD_MATERIAL.json     # 物料
    ├── SAL_OUTSTOCK.json    # 销售出库单
    └── ...
```

## 接口概览

### 认证方式

金蝶云星空使用 **Cookie-Based 会话认证**：

| 方式 | 端点 | 说明 |
|------|------|------|
| LoginByAppSecret | `/Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.LoginByAppSecret.common.kdsvc` | 应用密钥登录 |

**认证参数格式**:
```json
[acct_id, username, app_id, app_secret, lcid]
```

### 主要接口

金蝶云星空 API 基于动态表单服务，每个表单支持标准操作：

#### 1. 查询类操作

| 方法 | 端点 | 说明 |
|------|------|------|
| ExecuteBillQuery | POST | 列表查询，返回二维数组 |
| View | POST | 单据查看 |
| QueryBusinessInfo | POST | 业务对象信息查询 |

#### 2. 保存类操作

| 方法 | 端点 | 说明 |
|------|------|------|
| Save | POST | 保存单据 |
| BatchSave | POST | 批量保存 |

#### 3. 工作流操作

| 方法 | 端点 | 说明 |
|------|------|------|
| Submit | POST | 提交单据 |
| Audit | POST | 审核单据 |
| UnAudit | POST | 反审核 |
| Delete | POST | 删除单据 |

## API URL 格式

```
{base_url}/{service_path}.{operation}.common.kdsvc
```

示例：
```
https://api.example.com/k3cloud/Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.ExecuteBillQuery.common.kdsvc
```

## 请求格式

### 请求头
```
Content-Type: application/json; charset=UTF-8
Cookie: kdservice-sessionid={session_cookie}
```

### 请求体

**列表查询 (ExecuteBillQuery)**:
```json
{
    "FormId": "BD_MATERIAL",
    "FieldKeys": "FName,FNumber",
    "FilterString": "FNumber='MTL001'",
    "OrderString": "FNumber ASC",
    "TopRowCount": 0,
    "StartRow": 0,
    "Limit": 100,
    "SubSystemId": ""
}
```

**单据查看 (View)**:
```json
{
    "CreateOrgId": 0,
    "Number": "SAL001",
    "Id": "",
    "IsSortBySeq": "false"
}
```

**保存 (Save)**:
```json
{
    "formid": "SAL_OUTSTOCK",
    "NeedUpDateFields": [],
    "NeedReturnFields": [],
    "IsDeleteEntry": "True",
    "Model": {
        "FMaterialId": {"FNumber": "MTL001"},
        "FQuantity": 100
    }
}
```

## 响应格式

### ExecuteBillQuery 响应（二维数组）
```json
{
    "Result": [
        ["FName", "FNumber"],
        ["物料1", "MTL001"],
        ["物料2", "MTL002"]
    ]
}
```

### View/Save 响应
```json
{
    "Result": {
        "ResponseStatus": {
            "IsSuccess": true,
            "Errors": [],
            "SuccessEntitys": []
        },
        "Id": 100001,
        "Number": "SAL001"
    }
}
```

## 错误处理

### 会话失效
当响应包含 `{ctx == null}` 或 `会话信息已丢失，请重新登录` 时，需要重新认证。

### 业务错误
```json
{
    "Result": {
        "ResponseStatus": {
            "IsSuccess": false,
            "Errors": [
                {"FieldName": "FMaterialId", "Message": "物料不能为空"}
            ]
        }
    }
}
```

## 分页说明

- `StartRow`: 开始行索引，从 0 开始
- `Limit`: 最大返回行数，最大 10000
- `TopRowCount`: 返回总行数（用于分页导航）

## 更新记录

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-04-05 | 1.0.0 | 初始文档，基于金蝶云星空 8.2.0 API |
