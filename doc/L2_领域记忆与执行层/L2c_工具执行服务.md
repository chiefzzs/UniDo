# L2c 工具执行服务

## 1. 组件概念

**L2c 工具执行服务** 是 L2 领域层的核心组件，负责统一的工具执行调度和结果返回。

### 1.1 核心职责
- 执行工具调用（同步/异步）
- 处理工具返回结果
- 管理工具执行状态
- 提供工具调用记录
- 调度到具体的工具实现

### 1.2 设计理念
- **统一执行入口**：所有工具通过统一接口调用
- **异步执行**：支持同步和异步工具调用
- **错误处理**：完善的错误处理和重试机制
- **调度转发**：将工具调用转发到具体的工具实现

---

## 2. 数据类定义

### 2.1 ToolCall（工具调用记录）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| call_id | str | 调用ID | 调用唯一标识 | 服务自动生成 |
| tool_id | str | 工具ID | 被调用的工具 | 服务设置 |
| tool_name | str | 工具名称 | 工具名称 | 服务设置 |
| dialog_id | str | 对话ID | 所属对话 | 服务设置 |
| task_id | str | 任务ID | 关联任务 | 服务设置 |
| input_params | Dict[str, Any] | 输入参数 | 工具调用参数 | 调用方提供 |
| output_result | Optional[str] | 输出结果 | 工具执行结果 | 工具返回 |
| status | str | 执行状态 | pending/executing/completed/failed | 服务管理 |
| error_message | Optional[str] | 错误信息 | 执行失败时的错误信息 | 服务设置 |
| start_time | str | 开始时间 | 执行开始时间 | 服务自动生成 |
| end_time | str | 结束时间 | 执行结束时间 | 服务自动生成 |
| duration | float | 执行时长 | 执行耗时（秒） | 服务自动计算 |

### 2.2 ToolResult（工具执行结果）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| toolcall_status | string | 执行的状态 | 取值：done/failed/timeout/cancelled/error/invalid_params/partial_done | 服务设置 |
| result | string | 执行结果 | 工具返回的数据 | 工具返回 |
| call_id | str | 调用ID | 关联的调用记录 | 服务设置 |

### 2.3 持久化数据格式

L2c 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.3.1 ToolCall
- **存储位置**：`src/data/{env_type}/tool_call.json`
- **存储内容**：
```json
[
  {
    "call_id": "call-abc123",
    "tool_id": "tool-file-read",
    "tool_name": "文件读取",
    "dialog_id": "dialog-001",
    "task_id": "task-001",
    "input_params": {"path": "/workspace/file.txt"},
    "result": ToolResult(
      success=True,
      result="文件内容..."
    ),
    
    "start_time": "2026-05-18T10:30:00",
    "end_time": "2026-05-18T10:30:01",
    "duration": 1.2
  }
]
```

#### 2.3.2 ToolResult
- **存储位置**：`src/data/{env_type}/tool_result.json`
- **存储内容**：
```json
[
  {
  "role": "tool",
  "content": "<toolcall_status>failed</toolcall_status>\n<toolcall_result>\n执行失败：文件路径不存在或权限不足\n</toolcall_result>",
  "tool_call_id": "call_3IjNPsVkqo6wEi2wCv8BhMEL1"
  },{
  "role": "tool",
  "content": "<toolcall_status>done</toolcall_status>\n<toolcall_result>\n执行成功</toolcall_result>",
  "tool_call_id": "call_3IjNPsVkqo6wEi2wCv8BhMEL2"
  }
]
```

##### 支持的类型：
```
done：执行成功（你现有）
failed：执行失败（常规错误）
timeout：工具调用超时
cancelled：主动取消调用
error：系统异常 / 未知错误
invalid_params：参数不合法
partial_done：部分执行成功
```

---

## 3. 支持的场景

### 3.1 直接支持的场景

| 场景编号 | 场景名称 | 场景描述 |
|---------|---------|---------|
| SC017 | 查看工具执行 | 执行工具并返回结果 |
| SC018 | 查看任务执行过程 | 执行任务相关工具 |

### 3.2 作为下层组件支持的场景

所有需要工具调用的上层场景都依赖 L2c：
- L3b 四大对话场景（代码开发、任务执行等）
- L3a 通用任务协调
- L2d LLM执行服务（工具调用解析后执行）

---

## 4. 数据流与控制流

### 4.1 工具调用流程

```
调用方                    L2c                    L2f                     工具实现                    L1d
|                         |                      |                      |                      |
|--- execute_tool() ------>|                      |                      |                      |
|                         |                      |                      |                      |
|                         |--- get_tool -------->|                      |                      |
|                         |                      |                      |                      |
|                         |<--- tool -------------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 验证参数 ----------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 创建调用记录 ------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 调度执行 ----------|                      |                      |
|                         |                      |                      |--- 执行工具 --------->|
|                         |                      |                      |                      |
|                         |                      |                      |<--- 结果 ------------|
|                         |                      |                      |                      |
|                         |<--- 执行结果 ----------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 更新调用记录 ------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 发布事件 ----------|                      |                      |
|                         |                      |                      |                      |
|<--- ToolResult ---------|                      |                      |                      |
```

### 4.2 异步工具调用流程

```
调用方                    L2c                    L2f                     工具实现                    L1d
|                         |                      |                      |                      |
|--- execute_async() ---->|                      |                      |                      |
|                         |                      |                      |                      |
|                         |--- get_tool -------->|                      |                      |
|                         |                      |                      |                      |
|                         |<--- tool -------------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 创建调用记录 ------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 启动异步执行 ------|                      |                      |
|                         |                      |                      |                      |
|                         |<--- call_id ----------|                      |                      |
|                         |                      |                      |                      |
|                         |[异步执行]            |                      |                      |
|                         |                      |                      |--- 执行工具 --------->|
|                         |                      |                      |                      |
|                         |                      |                      |<--- 结果 ------------|
|                         |                      |                      |                      |
|                         |<--- 执行结果 ----------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 更新状态 ----------|                      |                      |
|                         |                      |                      |                      |
|                         |--- 发布事件 ----------|                      |                      |
|                         |                      |                      |                      |
```

---

## 5. 如何使用下层组件

### 5.1 依赖的组件

| 组件 | 作用 | 使用方式 |
|-----|------|---------|
| L1d 事件系统 | 发布工具调用事件 | event_bus.publish() |
| L2a 领域实体管理 | 更新任务状态 | task_service.update_task() |
| L2f 工具管理服务 | 获取工具定义和配置 | tool_service.get_tool() |

### 5.2 作为下层组件被使用

L2c 被上层组件以下列方式使用：

```python
# 1. 获取服务实例
from L2c_tool_execution import ToolExecutor

tool_executor = ToolExecutor()

# 2. 执行工具（同步）- 工具需预先在L2f注册
result = tool_executor.execute_tool(
    tool_name="文件读取",
    dialog_id="dialog-123",
    task_id="task-456",
    params={"path": "/path/to/file.txt"}
)

# 3. 执行工具（异步）
call_id = tool_executor.execute_async(
    tool_name="文件读取",
    dialog_id="dialog-123",
    task_id="task-456",
    params={"path": "/path/to/file.txt"}
)

# 5. 查询执行状态
status = tool_executor.get_call_status(call_id)

# 6. 获取工具列表
tools = tool_executor.list_tools(category="文件操作")
```

---

## 6. 关键方法说明

### 6.1 ToolExecutor

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| execute_tool(tool_name, dialog_id, task_id, params) | 同步执行工具 | tool_name: str, dialog_id: str, task_id: str, params: Dict | ToolResult |
| execute_async(tool_name, dialog_id, task_id, params) | 异步执行工具 | tool_name: str, dialog_id: str, task_id: str, params: Dict | call_id: str |
| get_call_status(call_id) | 获取调用状态 | call_id: str | ToolCall |
| cancel_call(call_id) | 取消调用 | call_id: str | bool |
| list_calls(dialog_id) | 列出调用记录 | dialog_id: str | List[ToolCall] |

---

## 7. 与其他L2组件的关系

### 7.1 与 L2a 领域实体管理

L2c 更新任务状态：
- 工具执行开始时更新任务为 executing
- 工具执行完成时更新任务为 completed 或 failed

### 7.2 与 L2b 记忆与状态管理

L2c 更新会话状态：
- 工具执行期间更新会话为 executing
- 工具执行完成后更新会话状态

### 7.3 与 L2d LLM执行服务

L2d 解析工具调用后调用 L2c：
- L2d 将工具调用请求转发给 L2c
- L2c 返回结果给 L2d

### 7.4 与 L2f 工具管理服务

L2c 依赖 L2f 获取工具定义：
- 执行工具前从 L2f 获取工具配置和实现
- 通过 L2f 判断工具类型（native/skill）并调度到对应执行路径

---

## 8. 错误处理与重试

### 8.1 错误类型

| 错误类型 | 描述 | 处理方式 |
|---------|------|---------|
| 参数错误 | 参数缺失或格式错误 | 返回错误信息，不重试 |
| 超时错误 | 工具执行超时 | 根据配置重试 |
| 网络错误 | 网络连接失败 | 根据配置重试 |
| 权限错误 | 权限不足 | 返回错误信息，不重试 |
| 业务错误 | 工具执行逻辑错误 | 根据配置决定是否重试 |

### 8.2 重试策略

```python
# 重试配置示例
retry_config = {
    'max_retries': 3,
    'retry_delay': 1.0,  # 初始延迟（秒）
    'retry_backoff': 2.0,  # 延迟倍数
    'retry_on_errors': ['timeout', 'network_error']
}
```

### 8.3 超时处理

- 设置工具级别超时时间（从L2f获取）
- 设置全局超时时间
- 超时后取消执行并返回错误

---

## 9. 性能优化

### 9.1 异步执行

- 支持异步工具调用
- 使用线程池或进程池
- 避免阻塞主线程

### 9.2 连接池

- HTTP工具使用连接池
- 复用网络连接
- 配置连接池大小

---

## 附录：工具调用示例

### ToolCall 示例

```json
{
  "call_id": "call-abc123",
  "tool_id": "tool-file-read",
  "tool_name": "文件读取",
  "dialog_id": "dialog-123",
  "task_id": "task-456",
  "input_params": {"path": "/home/user/documents/note.txt"},
  "output_result": "文件内容...",
  "status": "completed",
  "error_message": null,
  "start_time": "2026-05-18T10:30:00",
  "end_time": "2026-05-18T10:30:01",
  "duration": 1.2
}
```

### ToolResult 示例

```json
{
  "success": true,
  "result": "Hello, World!",
  "error": null,
  "call_id": "call-abc123"
}

