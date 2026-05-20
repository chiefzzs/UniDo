# L2a 项目与配置管理服务

## 1. 服务定位

**L2a 项目与配置管理服务** 是 L2 领域记忆与执行层的核心组件之一，负责管理项目及其相关配置数据。

### 1.1 核心职责
- **Project管理**：项目的创建、查询、更新、删除、归档
- **WorkspaceConfig管理**：工作区配置的创建、查询、更新、删除
- **ModelConfig管理**：模型配置的创建、查询、更新、删除
-

### 1.2 设计原则
- **聚合根模式**：Project作为聚合根，关联其他配置实体
- **配置中心化**：统一管理所有配置，供其他组件引用
- **松耦合**：通过ID引用，避免直接依赖

---

## 2. 数据结构定义

### 2.1 Project（项目）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| project_id | str | 项目唯一标识 | 非空，唯一 |
| name | str | 项目名称 | 非空 |
| description | str | 项目描述 | 可选 |
| workspace_config_id | str | 关联的工作区配置ID | 非空 |
| model_config_id | str | 关联的模型配置ID | 非空 |
| tool_config_ids | List[str] | 关联的工具配置ID列表 | 可选 |
| status | str | 项目状态（active/archived） | 默认active |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.2 WorkspaceConfig（工作区配置）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| config_id | str | 配置唯一标识 | 非空，唯一 |
| name | str | 配置名称 | 非空 |
| root_path | str | 工作区根路径 | 非空 |
| type | str | 工作区类型（local/remote） | 默认local |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.3 ModelConfig（模型配置）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| config_id | str | 配置唯一标识 | 非空，唯一 |
| name | str | 配置名称 | 非空 |
| model_name | str | 模型名称 | 非空 |
| api_type | str | API类型（openai/anthropic/baidu等） | 非空 |
| api_address | str | API地址 | 非空 |
| api_key | str | API密钥（加密存储） | 非空 |
| parameters | Dict | 模型参数（temperature等） | 可选 |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.4 持久化数据格式

L2a 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.4.1 Project
- **存储位置**：`src/data/{env_type}/project.json`
- **存储内容**：
```json
[
  {
    "project_id": "proj-001",
    "name": "我的项目",
    "description": "项目描述",
    "workspace_config_id": "ws-config-001",
    "model_config_id": "model-config-001",
    "status": "active",
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.4.2 WorkspaceConfig
- **存储位置**：`src/data/{env_type}/workspace_config.json`
- **存储内容**：
```json
[
  {
    "config_id": "ws-config-001",
    "name": "本地工作区",
    "root_path": "/workspace/project",
    "type": "local",
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.4.3 ModelConfig
- **存储位置**：`src/data/{env_type}/model_config.json`
- **存储内容**：
```json
[
  {
    "config_id": "model-config-001",
    "name": "Qwen 模型配置",
    "model_name": "Qwen/Qwen3.5-397B-A17B",
    "api_type": "openai",
    "api_address": "https://api.example.com/v1",
    "api_key": "encrypted:xxx",
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 2000
    },
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

---

## 3. 关键方法定义

### 3.1 ProjectService（项目管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_project(name, description, workspace_config_id, model_config_id) | 创建项目 | name: str, description: str, workspace_config_id: str, model_config_id: str | Project |
| get_project(project_id) | 获取项目 | project_id: str | Optional[Project] |
| update_project(project_id, **kwargs) | 更新项目 | project_id: str, 字段名=值 | Optional[Project] |
| delete_project(project_id) | 删除项目 | project_id: str | bool |
| archive_project(project_id) | 归档项目 | project_id: str | bool |
| list_projects(status=None) | 列出项目 | status: Optional[str] | List[Project] |
| validate_project_config(project_id) | 验证项目配置有效性 | project_id: str | bool |

### 3.2 WorkspaceConfigService（工作区配置管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_workspace_config(name, root_path, **kwargs) | 创建工作区配置 | name: str, root_path: str | WorkspaceConfig |
| get_workspace_config(config_id) | 获取工作区配置 | config_id: str | Optional[WorkspaceConfig] |
| update_workspace_config(config_id, **kwargs) | 更新工作区配置 | config_id: str, 字段名=值 | Optional[WorkspaceConfig] |
| delete_workspace_config(config_id) | 删除工作区配置 | config_id: str | bool |
| list_workspace_configs() | 列出工作区配置 | 无 | List[WorkspaceConfig] |

### 3.3 ModelConfigService（模型配置管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_model_config(name, model_name, api_type, api_address, api_key, **kwargs) | 创建模型配置 | name: str, model_name: str, api_type: str, api_address: str, api_key: str | ModelConfig |
| get_model_config(config_id) | 获取模型配置 | config_id: str | Optional[ModelConfig] |
| update_model_config(config_id, **kwargs) | 更新模型配置 | config_id: str, 字段名=值 | Optional[ModelConfig] |
| delete_model_config(config_id) | 删除模型配置 | config_id: str | bool |
| list_model_configs() | 列出模型配置 | 无 | List[ModelConfig] |

 

### 3.5 ConfigValidationService（配置验证服务）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| validate_configs(workspace_id, model_config_id, tool_config_ids) | 验证配置ID有效性 | workspace_id: str, model_config_id: str, tool_config_ids: List[str] | bool |

---

## 4. 与其他组件的关系

### 4.1 依赖关系

| 组件 | 关系类型 | 说明 |
|-----|---------|------|
| L1b 持久化服务 | 依赖 | 用于存储和读取配置数据 |
| L1d 事件系统 | 依赖 | 发布配置变更事件 |

### 4.2 被调用关系

| 组件 | 调用方式 | 说明 |
|-----|---------|------|
| L2b 记忆与状态管理服务 | 读取 | 获取项目配置信息 |
| L3a 通用任务协调服务 | 读写 | 创建和管理项目 |
| L3c UI操作场景服务 | 读写 | 配置管理界面操作 |

### 4.3 协作流程示例

**创建项目流程：**
```
L3层请求                    L2a                    L1b                    L1d
        |                    |                      |                      |
        |--- create_project -->|                      |                      |
        |                    |                      |                      |
        |                    |--- validate_configs -->|                      |
        |                    |                      |                      |
        |                    |<--- valid ------------|                      |
        |                    |                      |                      |
        |                    |--- save_project ----->|                      |
        |                    |                      |                      |
        |                    |<--- success ----------|                      |
        |                    |                      |                      |
        |                    |--- publish_event ---->|                      |
        |                    |                      |                      |
        |<--- Project --------|                      |                      |
```

---

## 5. 容错与恢复

### 5.1 数据完整性保障
- 使用事务确保操作原子性
- 验证配置引用的有效性
- 维护项目与配置的关系完整性

### 5.2 错误处理
- 捕获并处理持久化异常
- 返回有意义的错误信息
- 发布错误事件

### 5.3 恢复策略
- 支持软删除，可恢复已删除实体
- 支持归档状态，可恢复已归档项目
- 记录操作历史，支持回滚

---

## 6. 安全与权限

### 6.1 访问控制
- 项目级权限管理
- 配置级权限管理

### 6.2 数据保护
- API密钥加密存储
- 敏感信息脱敏处理

### 6.3 审计日志
- 记录配置变更
- 记录项目操作