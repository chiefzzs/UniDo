# L1b 持久化与IO基础设施

## 1. 组件概念

**L1b 持久化与IO基础设施** 是系统的**底层核心数据存储层**，是L1层的基石，负责管理配置、LLM调用过程、事件等所有数据的持久化操作。

### 1.1 核心职责
- 提供统一的数据持久化接口，支持配置管理、LLM调用过程、事件的持久化
- 管理文件系统IO操作
- 支持数据查询和索引
- 实现数据的增删改查（CRUD）
- **环境隔离**：通过环境变量实现开发与测试环境分离
- **序列支持**：保证关键数据序列的有序存储

### 1.2 设计理念
- **统一接口**：所有实体使用相同的CRUD模式
- **文件存储**：使用JSON格式存储，便于调试和迁移
- **分层存储**：按实体类型组织目录结构
- **事务性**：保证操作的原子性
- **环境隔离**：通过 `STORAGE_ENV` 环境变量隔离开发与测试环境
- **单文件存储**：每种类型的信息使用一个独立的JSON文件
- **数组存储**：多个数据采用数组格式存储
- **完美JSON**：格式化输出，便于人工核查

---

## 2. 通用存储接口

**核心原则**：L1b 不定义业务实体的具体数据结构，只提供通用的存储能力。业务实体由 L2 层定义，L1b 负责持久化。

### 2.1 通用实体接口

所有实体存储时必须包含的基础字段：

| 字段名 | 类型 | 含义描述 | 职责说明 |
|-------|------|---------|---------|
| entity_id | str | 实体唯一标识 | 用于实体的唯一识别，由服务自动生成UUID |
| created_at | str | 创建时间戳 | 记录实体创建时间，ISO 8601格式 |
| updated_at | str | 更新时间戳 | 记录实体最后更新时间，ISO 8601格式 |

### 2.2 核心存储接口

| 方法 | 功能 | 参数 | 返回值 | 说明 |
|-----|------|------|-------|------|
| `save(entity_type, data)` | 保存实体 | `entity_type: str`, `data: dict` | `entity_id: str` | 保存或更新实体，自动生成entity_id |
| `load(entity_type, entity_id)` | 加载实体 | `entity_type: str`, `entity_id: str` | `Optional[dict]` | 根据ID加载单个实体 |
| `list(entity_type, filters=None)` | 列出实体 | `entity_type: str`, `filters: dict` | `List[dict]` | 条件查询实体列表 |
| `delete(entity_type, entity_id)` | 删除实体 | `entity_type: str`, `entity_id: str` | `bool` | 软删除或硬删除 |
| `exists(entity_type, entity_id)` | 检查实体是否存在 | `entity_type: str`, `entity_id: str` | `bool` | 检查实体是否存在 |

### 2.3 实体类型定义

| 实体类型 | 存储文件 | 定义层级 | 说明 |
|---------|---------|---------|------|
| projects | projects.json | L2a | 项目实体 |
| sessions | sessions.json | L2b | 会话实体（内嵌messages） |
| llm_calls | llm_calls.json | L2d | LLM调用记录 |
| events | events.json | L1d | 事件记录 |
| prompts | prompts.json | L2d | 提示词模板 |
| workspace_configs | workspace_configs.json | L1a | 工作区配置 |
| model_configs | model_configs.json | L1a | 模型配置 |

### 2.4 存储约束

- **entity_id 前缀规范**：
  - `proj-` → Project
  - `sess-` → Session
  - `llm-` → LLMCallRecord
  - `evt-` → Event
  - `prompt-` → Prompt
  - `ws-` → WorkspaceConfig
  - `model-` → ModelConfig

- **数组格式存储**：同一类型的所有实体存储在单个JSON数组文件中
- **完美JSON格式**：4空格缩进，驼峰命名，ISO 8601日期格式

### 3.1 直接支持的场景

| 场景编号 | 场景名称 | 场景描述 |
|---------|---------|---------|
| SC002 | 创建新项目 | 创建Project实体并保存 |
| SC003 | 项目配置 | 更新Project实体 |
| SC008 | 创建新会话 | 创建Session实体 |
| SC009 | 打开历史会话 | 读取Session实体 |
| SC012 | 删除会话 | 删除Session实体 |
| SC013 | 输入用户问题 | 创建Message实体（内嵌到Session） |
| SC021 | 编辑历史消息 | 更新Message实体 |

### 3.2 作为下层组件支持的场景

所有需要数据持久化的上层场景都依赖 L1b：
- L2a 领域实体管理
- L2b 记忆与状态管理
- L2d 提示词管理
- L3c UI操作场景
- L3b 四大对话场景

---

## 4. 数据流与控制流

### 4.1 项目创建流程

```
用户                    L3c                    L2a                    L1b
|                       |                      |                      |
|--- 创建项目 ---------->|                      |                      |
|                       |--- create_project() ->|                      |
|                       |                      |--- save_project() --->|
|                       |                      |                      |
|                       |                      |<--- project_id ------|
|                       |<--- Project ----------|                      |
|                       |--- 发布事件 ---------->|                      |
|                       |                      |                      |
|<--- 成功消息 ----------|                      |                      |
```

### 4.2 消息创建流程

```
用户                    L3b                    L2a                    L1b
|                       |                      |                      |
|--- 发送消息 ---------->|                      |                      |
|                       |--- create_message() ->|                      |
|                       |                      |--- 添加到Session ---->|
|                       |                      |                      |
|                       |                      |--- save_session() --->|
|                       |                      |                      |
|                       |<--- Message ----------|                      |
|                       |--- 发布事件 ---------->|                      |
|                       |                      |                      |
|<--- 消息已发送 --------|                      |                      |
```

### 4.3 文件存储结构

#### 4.3.1 环境隔离目录结构

```
data/
├── dev/                    # STORAGE_ENV=dev 开发环境
│   ├── projects.json       # 所有项目数据（数组格式）
│   ├── sessions.json       # 所有会话数据（数组格式，内嵌messages）
│   ├── llm_calls.json      # 所有LLM调用记录（数组格式）
│   ├── events.json         # 所有事件数据（数组格式）
│   ├── prompts.json        # 所有提示词数据（数组格式）
│   ├── workspace_configs.json  # 所有工作区配置（数组格式）
│   └── model_configs.json  # 所有模型配置（数组格式）
└── test/                   # STORAGE_ENV=test 测试环境
    ├── projects.json
    ├── sessions.json
    ├── llm_calls.json
    ├── events.json
    ├── prompts.json
    ├── workspace_configs.json
    └── model_configs.json
```

**说明**：
- Message 内嵌于 Session，不独立存储（符合 DDD 聚合根原则）
- 提示词通过 `prompts.json` 独立存储，支持复用

#### 4.3.2 存储格式规范

- **单文件存储**：每种类型的信息使用一个独立的JSON文件
- **数组格式**：多个数据采用数组存储
- **完美JSON**：4空格缩进，驼峰命名，ISO 8601日期格式

#### 4.3.3 环境变量配置

| 环境变量 | 值 | 存储路径 |
|---------|-----|---------|
| STORAGE_ENV | dev | ./data/dev/ |
| STORAGE_ENV | test | ./data/test/ |
| STORAGE_ENV | (未设置) | ./data/dev/ |

---

## 5. 如何使用下层组件

### 5.1 依赖的组件

| 组件 | 作用 | 使用方式 |
|-----|------|---------|
| 文件系统 | 数据持久化存储 | 使用 Path 操作目录和文件 |
| json 模块 | 数据序列化 | 使用 json.dump/json.load |
| uuid 模块 | 生成唯一ID | 使用 uuid.uuid4() |
| datetime 模块 | 时间戳处理 | 使用 datetime.now().isoformat() |

### 5.2 作为下层组件被使用

L1b 被上层组件以下列方式使用（通用接口示例）：

```python
# 1. 获取持久化服务实例
from L1b_persistence import get_persistence_service
persistence = get_persistence_service()

# 2. 保存项目（通用接口）
project_data = {
    "name": "My Project",
    "workspace_id": "ws-123",
    "model_config_id": "model-456"
}
entity_id = persistence.save("projects", project_data)

# 3. 获取项目
project = persistence.load("projects", entity_id)

# 4. 更新项目
project["name"] = "Updated Project"
persistence.save("projects", project)

# 5. 删除项目
persistence.delete("projects", entity_id)

# 6. 列出所有项目
projects = persistence.list("projects")

# 7. 按条件查询
active_projects = persistence.list("projects", filters={"status": "active"})

# 8. 保存会话（包含内嵌消息）
session_data = {
    "project_id": "proj-123",
    "name": "New Session",
    "messages": [{
        "message_id": "msg-1",
        "order_index": 0,
        "role": "user",
        "content": "Hello"
    }]
}
session_id = persistence.save("sessions", session_data)

# 9. 保存LLM调用记录
llm_call_data = {
    "session_id": "sess-123",
    "model_config_id": "model-456",
    "request": {"messages": [...], "model": "qwen-turbo", "temperature": 0.7},
    "response": {"choices": [...], "usage": {...}},
    "status": "completed",
    "duration_ms": 1500
}
persistence.save("llm_calls", llm_call_data)
```

---

## 6. 通用存储接口详解

### 6.1 save(entity_type, data)

| 项目 | 说明 |
|-----|------|
| 功能 | 保存或更新实体 |
| 参数 | `entity_type: str` 实体类型, `data: dict` 实体数据 |
| 返回值 | `entity_id: str` 实体ID |
| 自动行为 | 若data中无entity_id，生成带前缀的UUID；若存在则更新 |

### 6.2 load(entity_type, entity_id)

| 项目 | 说明 |
|-----|------|
| 功能 | 根据ID加载单个实体 |
| 参数 | `entity_type: str` 实体类型, `entity_id: str` 实体ID |
| 返回值 | `Optional[dict]` 实体数据，不存在返回None |

### 6.3 list(entity_type, filters)

| 项目 | 说明 |
|-----|------|
| 功能 | 条件查询实体列表 |
| 参数 | `entity_type: str` 实体类型, `filters: Optional[dict]` 过滤条件 |
| 返回值 | `List[dict]` 实体列表 |
| 过滤示例 | `{"status": "active"}`, `{"project_id": "proj-123"}` |

### 6.4 delete(entity_type, entity_id)

| 项目 | 说明 |
|-----|------|
| 功能 | 删除实体 |
| 参数 | `entity_type: str` 实体类型, `entity_id: str` 实体ID |
| 返回值 | `bool` 是否成功 |

### 6.5 exists(entity_type, entity_id)

| 项目 | 说明 |
|-----|------|
| 功能 | 检查实体是否存在 |
| 参数 | `entity_type: str` 实体类型, `entity_id: str` 实体ID |
| 返回值 | `bool` 是否存在 |

---

## 7. 与其他L1组件的关系

### 7.1 与 L1d 事件系统的关系

L1b 在保存实体后可以发布事件，通知其他组件数据已变更。

```python
# 在 save_project 后发布事件
event = Event(
    event_type=EventTypes.PROJECT_CREATED,
    payload={'project_id': project_id}
)
event_bus.publish(event)
```

### 7.2 与 L1a 配置管理的关系

L1b 可以读取 L1a 的配置来确定存储路径等参数。

### 7.3 与 L1c LLM基础设施的关系

L1c 不直接依赖 L1b，但 L2d（LLM执行服务）会将 LLM 调用记录保存到 L1b。

---

## 8. 容错与恢复

### 8.1 文件操作容错

- 使用 try-except 捕获文件操作异常
- 确保目录存在后再进行文件操作
- 原子写入：先写入临时文件，再重命名

### 8.2 数据完整性

- 每次写入都包含完整的实体数据
- 支持 JSON 格式验证
- 提供数据修复工具

### 8.3 备份策略

- 支持定期自动备份
- 备份文件按时间戳命名
- 保留多个历史版本

---

## 9. 性能考虑

### 9.1 文件组织

- 按实体类型分文件存储（单文件数组格式）
- 避免多文件目录结构带来的开销

### 9.2 索引优化

- 维护索引文件加速查询
- 支持按时间、状态等字段索引
- 定期重建索引

### 9.3 缓存策略

- 在内存中缓存常用实体
- 实现 LRU 缓存淘汰策略
- 缓存失效机制

---

## 10. 安全考虑

### 10.1 路径安全

- 验证用户输入的路径
- 防止路径遍历攻击
- 使用 Path 对象进行路径操作

### 10.2 数据加密

- 敏感配置（如 API Key）加密存储
- 使用环境变量管理密钥
- 提供数据加密/解密接口

### 10.3 访问控制

- 文件权限设置
- 目录访问限制
- 审计日志记录

---

## 附录：文件格式示例

### projects.json 格式（数组存储）

```json
[
  {
    "entity_id": "proj-123456",
    "name": "My Project",
    "description": "A test project",
    "status": "active",
    "workspace_id": "ws-abcdef",
    "model_config_id": "model-xyz",
    "sessions": ["sess-1", "sess-2"],
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:30:00"
  },
  {
    "entity_id": "proj-789012",
    "name": "Another Project",
    "description": "Another test project",
    "status": "active",
    "workspace_id": "ws-ghijkl",
    "model_config_id": "model-abc",
    "sessions": [],
    "created_at": "2026-05-18T12:00:00",
    "updated_at": "2026-05-18T12:00:00"
  }
]
```

### sessions.json 格式（数组存储，内嵌messages）

```json
[
  {
    "entity_id": "sess-123",
    "project_id": "proj-123456",
    "name": "New Session",
    "status": "active",
    "messages": [
      {
        "message_id": "msg-abc",
        "order_index": 0,
        "role": "user",
        "content": "Hello, world!",
        "type": "text",
        "tool_call_id": null,
        "tool_name": null,
        "tool_input": null,
        "tool_output": null,
        "created_at": "2026-05-18T11:01:00"
      },
      {
        "message_id": "msg-def",
        "order_index": 1,
        "role": "assistant",
        "content": "Hi! How can I help you?",
        "type": "text",
        "tool_call_id": null,
        "tool_name": null,
        "tool_input": null,
        "tool_output": null,
        "created_at": "2026-05-18T11:01:30"
      }
    ],
    "task_group_id": null,
    "created_at": "2026-05-18T11:00:00",
    "updated_at": "2026-05-18T11:01:30"
  }
]
```

### llm_calls.json 格式（LLM调用记录）

```json
[
  {
    "call_id": "llm-123",
    "session_id": "sess-123",
    "model_config_id": "model-xyz",
    "request": {
      "messages": [{"role": "user", "content": "Hello, world!"}],
      "model": "qwen-turbo",
      "temperature": 0.7,
      "max_tokens": 4096,
      "stream": false
    },
    "response": {
      "choices": [{"message": {"role": "assistant", "content": "Hi! How can I help you?"}}],
      "usage": {"prompt_tokens": 10, "completion_tokens": 12, "total_tokens": 22},
      "model": "qwen-turbo"
    },
    "status": "completed",
    "duration_ms": 1500,
    "created_at": "2026-05-18T11:01:00"
  }
]
```

### prompts.json 格式（提示词存储）

```json
[
  {
    "prompt_id": "prompt-123",
    "name": "客服助手提示词",
    "category": "customer_service",
    "content": "你是一个专业的客服助手，需要帮助用户解决问题...",
    "version": "1.0",
    "variables": ["product_name", "user_name"],
    "is_active": true,
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

### events.json 格式（事件记录）

```json
[
  {
    "event_id": "evt-123",
    "event_type": "MESSAGE_CREATED",
    "payload": {"message_id": "msg-abc", "session_id": "sess-123"},
    "timestamp": "2026-05-18T11:01:00",
    "processed": false
  },
  {
    "event_id": "evt-456",
    "event_type": "LLM_CALL_COMPLETED",
    "payload": {"call_id": "llm-123", "session_id": "sess-123"},
    "timestamp": "2026-05-18T11:01:30",
    "processed": false
  }
]
```
