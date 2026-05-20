# L2b 记忆与状态管理服务

## 1. 服务定位

**L2b 记忆与状态管理服务** 是 L2 领域记忆与执行层的核心组件之一，负责管理会话、消息、任务组和任务的状态，以及记忆系统的维护。

### 1.1 核心职责
- **Session管理**：会话的创建、查询、更新、删除、列出（按项目过滤），Session聚合多个Dialog
- **Dialog管理**：对话的创建、查询、更新、删除，Dialog聚合多个Message，管理入口TaskGroup
- **Message管理**：消息的创建、查询、更新、删除
- **TaskGroup管理**：任务组的创建、查询、更新、删除，Group管理一组Task
- **Task管理**：任务的创建、查询、更新、删除
- **状态机管理**：会话状态流转
- **记忆管理**：短期记忆、长期记忆、记忆压缩

### 1.2 设计原则
- **事件驱动**：通过事件总线进行状态同步
- **分层记忆**：区分短期记忆和长期记忆
- **状态一致性**：维护会话状态的一致性

---

## 2. 数据结构定义

### 2.1 Session（会话）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| session_id | str | 会话唯一标识 | 非空，唯一 |
| project_id | str | 关联的项目ID | 非空 |
| name | str | 会话名称 | 非空 |
| dialog_ids | List[str] | 关联的对话ID列表 | 可选 |
| status | str | 会话状态（active/closed/archived） | 默认active |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.2 Dialog（对话）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| dialog_id | str | 对话唯一标识 | 非空，唯一 |
| session_id | str | 关联的会话ID | 非空 |
| name | str | 对话名称 | 可选 |
| message_ids | List[str] | 关联的消息ID列表 | 可选 |
| entry_task_group_id | str | 入口任务组ID | 可选 |
| status | str | 对话状态（active/closed） | 默认active |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.3 Message（消息）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| message_id | str | 消息唯一标识 | 非空，唯一 |
| dialog_id | str | 关联的对话ID | 非空 |
| role | str | 角色（system/user/assistant/tool） | 非空 |
| content | str \| List[Dict] | 消息内容，支持纯文本或多部分内容数组 | 非空 |
| content[].type | str | 内容类型（text） | 非空 |
| content[].text | str | 文本内容 | 非空 |
| tool_calls | List[Dict] | 工具调用列表 | 可选 |
| tool_call_id | str | 工具调用ID（用于工具返回消息） | 可选 |
| created_at | datetime | 创建时间 | 自动生成 |

### 2.4 TaskGroup（任务组）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| task_group_id | str | 任务组唯一标识 | 非空，唯一 |
| dialog_id | str | 关联的对话ID | 非空 |
| name | str | 任务组名称 | 非空 |
| status | str | 任务组状态（pending/running/completed/failed） | 默认pending |
| task_ids | List[str] | 子任务ID列表 | 可选 |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.5 Task（任务）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| task_id | str | 任务唯一标识 | 非空，唯一 |
| task_group_id | str | 关联的任务组ID | 可选 |
| dialog_id | str | 关联的对话ID | 非空 |
| name | str | 任务名称 | 非空 |
| type | str | 任务类型（tool/external/llm） | 非空 |
| status | str | 任务状态（pending/running/completed/failed） | 默认pending |
| input_data | Dict | 输入数据 | 可选 |
| output_data | Dict | 输出数据 | 可选 |
| error_message | str | 错误信息 | 可选 |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |
| started_at | datetime | 开始执行时间 | 可选 |
| completed_at | datetime | 完成时间 | 可选 |

### 2.5 SessionState（会话状态）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| session_id | str | 关联的会话ID | 非空 |
| state | str | 当前状态（idle/thinking/executing/error） | 默认idle |
| current_task_id | str | 当前执行的任务ID | 可选 |
| context | Dict | 当前上下文信息 | 可选 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.6 ShortTermMemory（短期记忆）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| session_id | str | 关联的会话ID | 非空 |
| messages | List[Message] | 消息列表 | 非空 |
| last_accessed_at | datetime | 最后访问时间 | 自动更新 |

### 2.7 LongTermMemory（长期记忆）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| session_id | str | 关联的会话ID | 非空 |
| summaries | List[str] | 总结列表 | 可选 |
| key_points | List[str] | 关键点列表 | 可选 |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.8 持久化数据格式

L2b 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.8.1 Session
- **存储位置**：`src/data/{env_type}/session.json`
- **存储内容**：
```json
[
  {
    "session_id": "sess-001",
    "project_id": "proj-001",
    "name": "我的会话",
    "dialog_ids": ["dialog-001", "dialog-002"],
    "status": "active",
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.8.2 Dialog
- **存储位置**：`src/data/{env_type}/dialog.json`
- **存储内容**：messages数组直接存储消息内容，支持多种消息类型
```json
[
  {
    "dialog_id": "dialog-001",
    "session_id": "sess-001",
    "name": "第一个对话",
    "messages": [
      {
        "message_id": "msg-001",
        "role": "system",
        "content": "你是一个有用的助手",
        "type": "system_prompt",
        "created_at": "2026-05-18T10:00:00"
      },
      {
        "message_id": "msg-002",
        "role": "user",
        "content": "查询今天北京的天气",
        "type": "text",
        "created_at": "2026-05-18T10:01:00"
      },
      {
        "message_id": "msg-003",
        "role": "assistant",
        "content": "",
        "type": "think",
        "reasoning_content": "用户想查询天气，我需要调用天气查询工具",
        "created_at": "2026-05-18T10:02:00"
      },
      {
        "message_id": "msg-004",
        "role": "assistant",
        "content": "",
        "type": "tool_call",
        "tool_calls": [
          {
            "name": "weather",
            "parameters": {"city": "北京", "date": "today"}
          }
        ],
        "created_at": "2026-05-18T10:02:30"
      },
      {
        "message_id": "msg-005",
        "role": "tool_result",
        "name": "weather",
        "content": "北京今天天气晴朗，温度25°C",
        "type": "tool_result",
        "created_at": "2026-05-18T10:03:00"
      },
      {
        "message_id": "msg-006",
        "role": "assistant",
        "content": "北京今天天气晴朗，温度25°C，适合户外活动。",
        "type": "text",
        "created_at": "2026-05-18T10:03:30"
      },
      {
        "message_id": "msg-007",
        "role": "system",
        "content": "{\"task_id\": \"task-001\", \"task_name\": \"读取文件任务\"}",
        "type": "task_context",
        "created_at": "2026-05-18T10:04:00"
      }
    ],
    "entry_task_group_id": "tg-001",
    "status": "active",
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

**Message字段说明**：
| 字段 | 类型 | 说明 |
|-----|------|------|
| role | string | 角色：system, user, assistant, tool_result |
| type | string | 消息类型：system_prompt, text, think, tool_call, tool_result, task_context |
| content | string | 消息内容文本 |
| reasoning_content | string | Think信息（type=think时使用） |
| tool_calls | array | 工具调用列表（type=tool_call时使用） |
| name | string | 工具名称（role=tool_result时使用） |

#### 2.8.3 TaskGroup
- **存储位置**：`src/data/{env_type}/task_group.json`
- **存储内容**：
```json
[
  {
    "task_group_id": "tg-001",
    "dialog_id": "dialog-001",
    "name": "文件处理任务组",
    "status": "completed",
    "task_ids": ["task-001", "task-002"],
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:05:00"
  }
]
```

#### 2.8.5 Task
- **存储位置**：`src/data/{env_type}/task.json`
- **存储内容**：
```json
[
  {
    "task_id": "task-001",
    "task_group_id": "tg-001",
    "dialog_id": "dialog-001",
    "name": "读取文件任务",
    "type": "tool",
    "status": "completed",
    "input_data": {"path": "/workspace/file.txt"},
    "output_data": {"content": "文件内容..."},
    "error_message": null,
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:01:00",
    "started_at": "2026-05-18T10:00:30",
    "completed_at": "2026-05-18T10:01:00"
  }
]
```

#### 2.8.6 SessionState
- **存储位置**：`src/data/{env_type}/session_state.json`
- **存储内容**：
```json
[
  {
    "session_id": "sess-001",
    "state": "idle",
    "current_task_id": null,
    "context": {},
    "updated_at": "2026-05-18T10:05:00"
  }
]
```

#### 2.8.7 ShortTermMemory
- **存储位置**：`src/data/{env_type}/short_term_memory.json`
- **存储内容**：
```json
[
  {
    "session_id": "sess-001",
    "messages": [
      {
        "message_id": "msg-001",
        "role": "user",
        "content": "用户输入",
        "created_at": "2026-05-18T10:00:00"
      }
    ],
    "last_accessed_at": "2026-05-18T10:05:00"
  }
]
```

#### 2.8.8 LongTermMemory
- **存储位置**：`src/data/{env_type}/long_term_memory.json`
- **存储内容**：
```json
[
  {
    "session_id": "sess-001",
    "summaries": ["用户询问了关于文件操作的问题"],
    "key_points": ["用户需要读取文件", "用户需要写入文件"],
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:10:00"
  }
]
```

---

## 3. 关键方法定义

### 3.1 SessionService（会话管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_session(project_id, name) | 创建会话 | project_id: str, name: str | Session |
| get_session(session_id) | 获取会话 | session_id: str | Optional[Session] |
| update_session(session_id, **kwargs) | 更新会话 | session_id: str, 字段名=值 | Optional[Session] |
| delete_session(session_id) | 删除会话 | session_id: str | bool |
| list_sessions(project_id=None, status=None) | 列出会话（支持按项目过滤） | project_id: Optional[str], status: Optional[str] | List[Session] |
| close_session(session_id) | 关闭会话 | session_id: str | bool |
| archive_session(session_id) | 归档会话 | session_id: str | bool |

### 3.2 DialogService（对话管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_dialog(session_id, name=None) | 创建对话 | session_id: str, name: Optional[str] | Dialog |
| get_dialog(dialog_id) | 获取对话 | dialog_id: str | Optional[Dialog] |
| update_dialog(dialog_id, **kwargs) | 更新对话 | dialog_id: str, 字段名=值 | Optional[Dialog] |
| delete_dialog(dialog_id) | 删除对话 | dialog_id: str | bool |
| list_dialogs(session_id=None, status=None) | 列出会话下的对话 | session_id: Optional[str], status: Optional[str] | List[Dialog] |
| close_dialog(dialog_id) | 关闭对话 | dialog_id: str | bool |
| set_entry_task_group(dialog_id, task_group_id) | 设置入口任务组 | dialog_id: str, task_group_id: str | bool |

### 3.3 MessageService（消息管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_message(dialog_id, role, content, **kwargs) | 创建消息 | dialog_id: str, role: str, content: str | Message |
| get_message(message_id) | 获取消息 | message_id: str | Optional[Message] |
| update_message(message_id, **kwargs) | 更新消息 | message_id: str, 字段名=值 | Optional[Message] |
| delete_message(message_id) | 删除消息 | message_id: str | bool |
| list_messages(dialog_id, limit=None, offset=None) | 列出对话消息 | dialog_id: str, limit: Optional[int], offset: Optional[int] | List[Message] |

### 3.4 TaskGroupService（任务组管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_task_group(dialog_id, name, task_ids=None) | 创建任务组 | dialog_id: str, name: str, task_ids: Optional[List[str]] | TaskGroup |
| get_task_group(task_group_id) | 获取任务组 | task_group_id: str | Optional[TaskGroup] |
| update_task_group(task_group_id, **kwargs) | 更新任务组 | task_group_id: str, 字段名=值 | Optional[TaskGroup] |
| delete_task_group(task_group_id) | 删除任务组 | task_group_id: str | bool |
| list_task_groups(dialog_id=None, status=None) | 列出任务组 | dialog_id: Optional[str], status: Optional[str] | List[TaskGroup] |
| add_task_to_group(task_group_id, task_id) | 向任务组添加任务 | task_group_id: str, task_id: str | bool |
| remove_task_from_group(task_group_id, task_id) | 从任务组移除任务 | task_group_id: str, task_id: str | bool |

### 3.5 TaskService（任务管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_task(dialog_id, name, type, **kwargs) | 创建任务 | dialog_id: str, name: str, type: str | Task |
| get_task(task_id) | 获取任务 | task_id: str | Optional[Task] |
| update_task(task_id, **kwargs) | 更新任务 | task_id: str, 字段名=值 | Optional[Task] |
| delete_task(task_id) | 删除任务 | task_id: str | bool |
| list_tasks(dialog_id=None, task_group_id=None, status=None) | 列出任务 | dialog_id: Optional[str], task_group_id: Optional[str], status: Optional[str] | List[Task] |
| start_task(task_id) | 开始执行任务 | task_id: str | bool |
| complete_task(task_id, output_data) | 完成任务 | task_id: str, output_data: Dict | bool |
| fail_task(task_id, error_message) | 任务失败 | task_id: str, error_message: str | bool |

### 3.5 MemoryService（记忆管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| add_to_short_term_memory(session_id, message) | 添加到短期记忆 | session_id: str, message: Message | bool |
| get_short_term_memory(session_id, limit=None) | 获取短期记忆 | session_id: str, limit: Optional[int] | List[Message] |
| compress_memory(session_id) | 压缩记忆（生成总结） | session_id: str | bool |
| add_to_long_term_memory(session_id, summary, key_points=None) | 添加到长期记忆 | session_id: str, summary: str, key_points: Optional[List[str]] | bool |
| get_long_term_memory(session_id) | 获取长期记忆 | session_id: str | Optional[LongTermMemory] |
| build_context(session_id, max_tokens=None) | 构建上下文 | session_id: str, max_tokens: Optional[int] | str |

### 3.6 StateService（状态管理）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| get_session_state(session_id) | 获取会话状态 | session_id: str | Optional[SessionState] |
| update_session_state(session_id, state, **kwargs) | 更新会话状态 | session_id: str, state: str | bool |
| set_current_task(session_id, task_id) | 设置当前任务 | session_id: str, task_id: str | bool |
| clear_current_task(session_id) | 清除当前任务 | session_id: str | bool |

---

## 4. 与其他组件的关系

### 4.1 依赖关系

| 组件 | 关系类型 | 说明 |
|-----|---------|------|
| L1b 持久化服务 | 依赖 | 用于存储和读取实体数据 |
| L1d 事件系统 | 依赖 | 发布状态变更事件 |
| L2a 项目与配置管理服务 | 依赖 | 获取项目配置信息 |
| L2d LLM执行服务 | 依赖 | 生成记忆总结 |

### 4.2 被调用关系

| 组件 | 调用方式 | 说明 |
|-----|---------|------|
| L2e 请求构造服务 | 读取 | 获取上下文数据 |
| L2c 工具执行服务 | 读写 | 更新任务状态 |
| L3a 通用任务协调服务 | 读写 | 创建和管理会话、任务 |
| L3b 四大对话场景 | 读写 | 创建消息和会话 |
| L3c UI操作场景服务 | 读写 | 会话管理界面操作 |

### 4.3 协作流程示例

**创建会话流程：**
```
L3层请求                    L2b                    L2a                    L1b                    L1d
        |                    |                      |                      |                      |
        |--- create_session -->|                      |                      |                      |
        |                    |                      |                      |                      |
        |                    |--- get_project ------>|                      |                      |
        |                    |                      |                      |                      |
        |                    |<--- Project ----------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- save_session ----->|                      |                      |
        |                    |                      |                      |                      |
        |                    |<--- success ----------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- publish_event ---->|                      |                      |
        |                    |                      |                      |                      |
        |<--- Session --------|                      |                      |                      |
```

**工具执行状态更新流程：**
```
L2c工具执行                  L2b                    L1b                    L1d
        |                    |                      |                      |
        |--- update_task --->|                      |                      |
        |                    |                      |                      |
        |                    |--- save_task ------->|                      |                      |
        |                    |                      |                      |                      |
        |                    |<--- success ----------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- update_session_state -->|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- publish_event ---->|                      |                      |
        |                    |                      |                      |                      |
        |<--- success --------|                      |                      |                      |
```

---

## 5. 记忆压缩机制

### 5.1 触发条件
- 短期记忆消息数量超过阈值
- 会话空闲时间超过阈值
- 手动触发

### 5.2 压缩流程
```
L2b检测压缩条件              L2d                    L1b
        |                    |                      |
        |--- 检测压缩条件 ---->|                      |
        |                    |                      |
        |<--- 需要压缩 --------|                      |
        |                    |                      |
        |--- generate_summary ->|                      |
        |                    |                      |
        |                    |--- 调用LLM生成总结 ---->|                      |
        |                    |                      |                      |
        |                    |<--- summary ----------|                      |
        |                    |                      |                      |
        |<--- summary --------|                      |
        |                    |                      |
        |--- 保存到长期记忆 ---->|                      |
        |                    |                      |                      |
        |<--- success ----------|                      |
        |                    |                      |
        |--- 清理短期记忆 ---->|                      |
        |                    |                      |                      |
        |<--- success ----------|                      |
```

---

## 6. 容错与恢复

### 6.1 数据完整性保障
- 使用事务确保操作原子性
- 验证实体引用的有效性
- 维护关系完整性

### 6.2 错误处理
- 捕获并处理持久化异常
- 返回有意义的错误信息
- 发布错误事件

### 6.3 恢复策略
- 支持软删除，可恢复已删除实体
- 支持归档状态，可恢复已归档会话
- 记录操作历史，支持回滚

---

## 7. 安全与权限

### 7.1 访问控制
- 会话级权限管理
- 项目级权限过滤

### 7.2 数据保护
- 敏感信息脱敏处理

### 7.3 审计日志
- 记录会话变更
- 记录任务执行