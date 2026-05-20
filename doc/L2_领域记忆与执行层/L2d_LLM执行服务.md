# L2d LLM执行服务

## 1. 组件概念

**L2d LLM执行服务** 是 L2 领域层的核心组件，负责执行LLM调用、处理流式响应、解析工具调用并协调工具执行。

### 1.1 核心职责
- 执行LLM请求（从L2e获取构造好的请求）
- 处理流式响应
- 解析工具调用
- 管理LLM执行状态
- 生成对话响应

### 1.2 设计理念
- **抽象层**：屏蔽底层LLM服务差异
- **流式优先**：原生支持流式响应
- **工具调用集成**：自动解析和执行工具调用
- **事件驱动**：发布LLM相关事件

---

## 2. 数据类定义

### 2.1 LLMExecutionRequest（LLM执行请求）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| dialog_id | str | 对话ID | 关联的对话 | 调用方提供 |
| messages | List[Dict] | 消息列表 | 对话历史 | L2b提供 |
| model_config_id | str | 模型配置ID | 使用的模型配置 | 调用方提供 |
| stream | bool | 是否流式 | 是否启用流式响应 | 调用方指定 |
| max_tokens | int | 最大token数 | 响应长度限制 | 配置提供 |
| temperature | float | 温度参数 | 控制输出随机性 | 配置提供 |

### 2.2 LLMExecutionResponse（LLM执行响应）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| request_id | str | 请求ID | 请求唯一标识 | 服务自动生成 |
| dialog_id | str | 对话ID | 关联的对话 | 服务设置 |
| content | str | 响应内容 | LLM返回的文本 | LLM生成 |
| finish_reason | str | 结束原因 | stop/length/tool_call等 | LLM返回 |
| tool_calls | List[Dict] | 工具调用列表 | 解析出的工具调用 | 服务解析 |
| usage | Dict[str, int] | 使用统计 | token使用量 | LLM返回 |
| status | str | 执行状态 | completed/failed/streaming | 服务管理 |

### 2.3 StreamProcessor（流式处理器状态）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| request_id | str | 请求ID | 关联的请求 | 服务设置 |
| dialog_id | str | 对话ID | 关联的对话 | 服务设置 |
| state | str | 处理状态 | collecting/parsing/tool_call/completed | 服务管理 |
| collected_content | str | 已收集内容 | 当前收集的文本 | 服务管理 |
| current_tool_call | Optional[Dict] | 当前工具调用 | 正在解析的工具调用 | 服务管理 |
| chunks | List[Dict] | 分片列表 | 所有收到的分片 | 服务管理 |

### 2.4 ToolCallContext（工具调用上下文）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| tool_call_id | str | 工具调用ID | 调用唯一标识 | 服务自动生成 |
| request_id | str | 请求ID | 关联的LLM请求 | 服务设置 |
| dialog_id | str | 对话ID | 关联的对话 | 服务设置 |
| tool_name | str | 工具名称 | 调用的工具 | LLM指定 |
| parameters | Dict[str, Any] | 工具参数 | 工具调用参数 | LLM生成 |
| status | str | 调用状态 | pending/executing/completed/failed | 服务管理 |
| result | Optional[str] | 执行结果 | 工具返回结果 | L2c返回 |

### 2.5 LLMCallRecord（LLM调用记录）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| call_id | str | 调用ID | LLM调用唯一标识 | 服务自动生成 |
| dialog_id | str | 对话ID | 关联的对话 | 调用时指定 |
| model_config_id | str | 模型配置ID | 使用的模型配置 | 调用时指定 |
| request | Dict | 请求对象 | 完整的LLM请求参数 | 服务构建 |
| response | Dict | 响应对象 | 完整的LLM响应 | LLM返回 |
| status | str | 状态 | completed/failed/in_progress | 服务管理 |
| duration_ms | int | 耗时（毫秒） | 调用耗时 | 服务计算 |
| created_at | str | 创建时间 | 调用开始时间 | 服务自动生成 |

**request 对象结构**：
| 字段名 | 类型 | 含义 |
|-------|------|------|
| messages | List[Dict] | 消息列表 |
| model | str | 模型名称 |
| temperature | float | 温度参数 |
| max_tokens | int | 最大token数 |
| stream | bool | 是否流式 |

**response 对象结构**：
| 字段名 | 类型 | 含义 |
|-------|------|------|
| choices | List[Dict] | 响应选项 |
| usage | Dict | token使用统计 |
| model | str | 实际使用的模型 |

### 2.6 持久化数据格式

L2d 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.6.1 LLMExecutionRequest
- **存储位置**：`src/data/{env_type}/llm_execution_request.json`
- **存储内容**：
```json
[
  {
    "dialog_id": "dialog-001",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "model_config_id": "model-config-001",
    "stream": true,
    "max_tokens": 2000,
    "temperature": 0.7
  }
]
```

#### 2.6.2 LLMExecutionResponse
- **存储位置**：`src/data/{env_type}/llm_execution_response.json`
- **存储内容**：
```json
[
  {
    "request_id": "req-001",
    "dialog_id": "dialog-001",
    "content": "你好！有什么可以帮助你的吗？",
    "finish_reason": "stop",
    "tool_calls": null,
    "usage": {
      "prompt_tokens": 100,
      "completion_tokens": 50,
      "total_tokens": 150
    },
    "status": "completed"
  }
]
```

#### 2.6.3 LLMCallRecord
- **存储位置**：`src/data/{env_type}/llm_call_record.json`
- **存储内容**：
```json
[
  {
    "call_id": "call-001",
    "dialog_id": "dialog-001",
    "model_config_id": "model-config-001",
    "request": {
      "messages": [{"role": "user", "content": "你好"}],
      "model": "Qwen/Qwen3.5-397B-A17B",
      "temperature": 0.7,
      "max_tokens": 2000,
      "stream": true
    },
    "response": {
      "choices": [{"message": {"content": "你好！"}}],
      "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
      "model": "Qwen/Qwen3.5-397B-A17B"
    },
    "status": "completed",
    "duration_ms": 1500,
    "created_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.6.4 ToolCallContext
- **存储位置**：`src/data/{env_type}/tool_call_context.json`
- **存储内容**：
```json
[
  {
    "tool_call_id": "tc-001",
    "request_id": "req-001",
    "dialog_id": "dialog-001",
    "tool_name": "SearchCodebase",
    "parameters": {"information_request": "查找文件"},
    "status": "completed",
    "result": "找到3个文件"
  }
]
```

---

## 3. 支持的场景

### 3.1 直接支持的场景

| 场景编号 | 场景名称 | 场景描述 |
|---------|---------|---------|
| SC013 | 输入用户问题 | 执行LLM调用生成响应 |
| SC014 | 查看流式文本输出 | 处理流式响应并推送 |
| SC015 | 查看思考过程 | 解析并显示思考内容 |
| SC016 | 查看工具调用 | 解析LLM输出中的工具调用 |
| SC017 | 查看工具执行 | 调用工具执行服务 |

### 3.2 作为下层组件支持的场景

所有需要LLM调用的上层场景都依赖 L2d：
- L3b 四大对话场景
- L3a 通用任务协调

---

## 4. 数据流与控制流

### 4.1 非流式LLM调用流程

```
调用方                    L2d                    L1c                    L1d
|                         |                      |                      |
|--- execute() ----------->|                      |                      |
|                         |                      |                      |
|                         |--- 构建请求 ----------|                      |
|                         |                      |                      |
|                         |--- 发送请求 ----------|                      |
|                         |                      |                      |
|                         |<--- 响应 -------------|                      |
|                         |                      |                      |
|                         |--- 解析响应 ----------|                      |
|                         |                      |                      |
|                         |--- 发布事件 ----------|                      |
|                         |                      |                      |
|<--- LLMResponse --------|                      |                      |
```

### 4.2 流式LLM调用流程

```
调用方                    L2d                    L1c                    L1d
|                         |                      |                      |
|--- execute_stream() ---->|                      |                      |
|                         |                      |                      |
|                         |--- 构建请求 ----------|                      |
|                         |                      |                      |
|                         |--- 发送请求 ----------|                      |
|                         |                      |                      |
|                         |<--- Chunk 1 ----------|                      |
|                         |                      |                      |
|<--- on_chunk(chunk1) ----|                      |                      |
|                         |                      |                      |
|                         |<--- Chunk 2 ----------|                      |
|                         |                      |                      |
|<--- on_chunk(chunk2) ----|                      |                      |
|                         |                      |                      |
|                         |<--- 结束 -------------|                      |
|                         |                      |                      |
|<--- LLMResponse --------|                      |                      |
```

### 4.3 工具调用解析与执行流程

```
L2d                    L2c                    L2a                    L1d
|                      |                      |                      |
|--- 解析工具调用 --------|                      |                      |
|                      |                      |                      |
|                      |--- execute_tool() ---->|                      |
|                      |                      |                      |
|                      |<--- ToolResult --------|                      |
|                      |                      |                      |
|                      |--- 更新任务状态 ------|                      |
|                      |                      |                      |
|                      |--- 发布事件 ----------|                      |
|                      |                      |                      |
|<--- 工具执行结果 --------|                      |                      |
|                      |                      |                      |
|--- 继续LLM调用 --------->|                      |                      |
```

---

## 5. 如何使用下层组件

### 5.1 依赖的组件

| 组件 | 作用 | 使用方式 |
|-----|------|---------|
| L1c LLM基础设施 | 发送LLM请求 | llm_client.send_request() |
| L2e 请求构造服务 | 获取构造好的请求（含工具/技能描述） | request_builder.build_request() |
| L2b 记忆与状态管理 | 获取对话历史 | memory_manager.build_context() |
| L2c 工具执行服务 | 执行工具调用 | tool_executor.execute_tool() |
| L2a 领域实体管理 | 更新任务状态 | task_service.update_task() |
| L1d 事件系统 | 发布LLM事件 | event_bus.publish() |

### 5.2 作为下层组件被使用

L2d 被上层组件以下列方式使用：

```python
# 1. 获取服务实例
from L2d_llm_execution import LLMExecutionService

llm_service = LLMExecutionService()

# 2. 执行非流式LLM调用
response = llm_service.execute(
    session_id="sess-123",
    model_config_id="model-456",
    messages=[{'role': 'user', 'content': 'Hello'}],
    stream=False
)

# 3. 执行流式LLM调用
def on_chunk(chunk):
    print(chunk['delta'], end='')

response = llm_service.execute_stream(
    session_id="sess-123",
    model_config_id="model-456",
    messages=[{'role': 'user', 'content': 'Hello'}],
    on_chunk=on_chunk
)

# 4. 处理工具调用
if response.tool_calls:
    for tool_call in response.tool_calls:
        result = llm_service.execute_tool_call(
            session_id="sess-123",
            tool_call=tool_call
        )
```

---

## 6. 关键方法说明

### 6.1 LLMExecutionService

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| execute(session_id, model_config_id, messages, stream) | 执行LLM调用 | session_id, model_config_id, messages, stream | LLMExecutionResponse |
| execute_stream(session_id, model_config_id, messages, on_chunk) | 执行流式LLM调用 | session_id, model_config_id, messages, on_chunk | LLMExecutionResponse |
| execute_tool_call(session_id, tool_call) | 执行工具调用 | session_id, tool_call | ToolCallResult |
| parse_tool_calls(content) | 解析工具调用 | content: str | List[Dict] |
| build_request(session_id, model_config_id, messages) | 构建LLM请求 | session_id, model_config_id, messages | LLMRequest |
| get_execution_status(request_id) | 获取执行状态 | request_id: str | ExecutionStatus |

### 6.2 StreamProcessor

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| process_chunk(chunk) | 处理分片 | chunk: StreamChunk | None |
| is_complete() | 检查是否完成 | 无 | bool |
| get_content() | 获取已收集内容 | 无 | str |
| get_tool_call() | 获取工具调用 | 无 | Optional[Dict] |

---

## 7. 与其他L2组件的关系

### 7.1 与 L2b 记忆与状态管理

L2d 从 L2b 获取对话历史：
- 使用 build_context() 获取消息列表
- 更新会话状态（thinking -> idle）

### 7.2 与 L2c 工具执行服务

L2d 调用 L2c 执行工具：
- 解析出工具调用后调用 L2c
- 获取工具执行结果后继续对话

### 7.3 与 L2a 领域实体管理

L2d 创建消息实体：
- 将LLM响应保存为消息
- 更新任务状态

---

## 8. 工具调用解析

### 8.1 工具调用格式

```json
{
  "thought": "我需要搜索最新的Python教程",
  "tool_calls": [
    {
      "tool_name": "web_search",
      "parameters": {
        "query": "Python教程 2024",
        "max_results": 5
      }
    }
  ]
}
```

### 8.2 解析流程

1. 监听LLM输出中的工具调用标记
2. 使用JSON解析工具调用内容
3. 验证工具调用格式
4. 返回工具调用列表

### 8.3 工具调用执行

```python
def execute_tool_call(self, session_id: str, tool_call: Dict) -> ToolCallResult:
    """执行工具调用"""
    tool_name = tool_call.get('tool_name')
    parameters = tool_call.get('parameters', {})
    
    # 调用工具执行服务
    result = self.tool_executor.execute_tool(
        tool_name=tool_name,
        session_id=session_id,
        task_id=None,
        params=parameters
    )
    
    # 发布工具调用完成事件
    self.event_bus.publish(Event(
        event_type=EventTypes.TOOL_CALL_COMPLETED,
        payload={
            'tool_name': tool_name,
            'success': result.success,
            'result': result.result
        }
    ))
    
    return result
```

---

## 9. 流式响应处理

### 9.1 分片类型

| 类型 | 描述 | 处理方式 |
|-----|------|---------|
| text | 普通文本 | 直接输出 |
| think | 思考过程 | 标记为思考内容 |
| tool_call | 工具调用 | 解析并执行 |
| finish | 结束标记 | 结束流处理 |

### 9.2 流式处理流程

```
Chunk Received
    ↓
判断分片类型
    ↓
┌───────────────────────────────────────┐
│  text       │  think     │  tool_call │
├─────────────┼────────────┼────────────┤
│ 收集内容    │ 收集思考   │ 解析工具    │
│ 推送回调    │ 推送回调   │ 执行调用    │
└─────────────┴────────────┴────────────┘
    ↓
检查是否结束
    ↓
继续或完成
```

### 9.3 状态管理

```python
# 流式处理器状态
stream_states = {
    'collecting': '收集文本内容',
    'parsing': '解析工具调用',
    'tool_call': '执行工具调用',
    'completed': '处理完成'
}
```

---

## 10. 错误处理

### 10.1 错误类型

| 错误类型 | 描述 | 处理方式 |
|---------|------|---------|
| API错误 | LLM服务返回错误 | 返回错误响应 |
| 超时错误 | 请求超时 | 返回超时错误 |
| 解析错误 | 工具调用解析失败 | 返回原始响应 |
| 工具错误 | 工具执行失败 | 返回工具错误信息 |

### 10.2 重试机制

- 设置最大重试次数
- 支持指数退避
- 记录重试日志

---

## 附录：执行流程示例

### 完整对话流程

```
用户                    L3b                    L2d                    L2b                    L1c                    L1d
|                       |                      |                      |                      |                      |
|--- 发送消息 ---------->|                      |                      |                      |                      |
|                       |--- execute() -------->|                      |                      |                      |
|                       |                      |--- build_context() -->|                      |                      |
|                       |                      |                      |                      |                      |
|                       |                      |<--- messages ----------|                      |                      |
|                       |                      |--- send_request() ---->|                      |                      |
|                       |                      |                      |                      |                      |
|                       |                      |<--- response ----------|                      |                      |
|                       |                      |--- 解析工具调用 --------|                      |                      |
|                       |                      |                      |                      |                      |
|                       |                      |--- execute_tool() ---->|                      |                      |
|                       |                      |                      |                      |                      |
|                       |                      |<--- tool_result --------|                      |                      |
|                       |                      |--- 继续LLM调用 -------->|                      |                      |
|                       |                      |                      |                      |                      |
|                       |<--- response ----------|                      |                      |                      |
|                       |--- 发布事件 ---------->|                      |                      |                      |
|                       |                      |                      |                      |                      |
|<--- 响应消息 ----------|                      |                      |                      |                      |
```

### LLMExecutionResponse 示例

```json
{
  "request_id": "req-abc123",
  "session_id": "sess-123",
  "content": "我已经完成了搜索，找到了几个不错的Python教程。",
  "finish_reason": "stop",
  "tool_calls": [],
  "usage": {
    "prompt_tokens": 128,
    "completion_tokens": 56,
    "total_tokens": 184
  },
  "status": "completed"
}
```

### ToolCallContext 示例

```json
{
  "tool_call_id": "tc-abc123",
  "request_id": "req-abc123",
  "session_id": "sess-123",
  "tool_name": "web_search",
  "parameters": {"query": "Python教程 2024", "max_results": 5},
  "status": "completed",
  "result": "[搜索结果...]"
}
```
