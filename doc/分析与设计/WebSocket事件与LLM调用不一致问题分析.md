# WebSocket事件与LLM调用不一致问题分析

## 1. 问题描述

### 1.1 问题现象
用户发送消息 `"请完成一个todolist 的工具需求分析，并保存到doc/需求分析目录下"` 后：
- LLM 调用了 2 次
- 第 1 次返回 `LS` 工具调用（列出工作目录）
- 第 2 次返回 `Write` 工具调用（写入文档到 `doc/需求分析/todolist 需求分析.md`）
- 但前端只收到 1 次 `message_response` 事件
- `doc/需求分析/todolist 需求分析.md` 文件未被创建

### 1.2 数据对比

| 数据源 | 工具调用 | 说明 |
|--------|----------|------|
| `llm_calls.json` | 2 次 LLM 调用 | 1. LS 工具 → 2. Write 工具 |
| `websocket_messages.json` | 1 次 message_response | 只包含 LS 结果 |
| `workspace` 目录 | 无文档文件 | Write 工具未被执行 |

---

## 2. 问题根因分析

### 2.1 核心问题：缺少递归 LLM 调用机制

当前的执行流程中，当 LLM 返回 `tool_calls` 时，系统执行工具后直接返回结果，没有将工具结果添加到 `messages[]` 并再次调用 LLM。

---

## 3. 修改方案

### 3.1 遵循的原则

1. **服务职责不变**：保持现有服务的职责边界不变
2. **最小侵入性**：只在必要的地方添加代码
3. **MECE 原则**：各修改点职责清晰，不重不漏
4. **面向对象设计**：遵循单一职责、开闭原则

### 3.2 架构职责边界

| 服务 | 原有职责 | 修改后职责 |
|------|----------|-----------|
| **DialogueService** | 对话生命周期管理 | 保持不变，调用新方法 |
| **BaseExecutionService** | 任务执行分发 | 新增：协调 LLM 调用和工具执行的循环 |
| **ToolTaskExecutor** | 单工具任务执行 | 保持不变 |
| **DialogueBasedLLMService** | LLM 调用和消息构造 | 保持不变 |
| **ToolExecutor** | 执行单个工具 | 保持不变 |

### 3.3 修改内容

#### 3.3.1 BaseExecutionService 新增方法

**文件**: `src/services/L3_scenario_coordination/L3a_task_coordination/base_execution_service.py`

新增 `execute_with_recursive_llm()` 方法，职责：
- 协调 LLM 调用和工具执行的循环
- 管理 `messages[]` 数组的累积
- 调用 `DialogueBasedLLMService` 执行 LLM
- 调用 `ToolExecutor` 执行工具
- 返回最终回复

```python
def execute_with_recursive_llm(self, task: Task, session_id: str, user_input: str) -> Task:
    """
    使用递归 LLM 调用执行任务

    流程：
    1. 调用 DialogueBasedLLMService.call_llm() 获取 LLM 响应
    2. 如果返回 tool_calls：
       a. 解析工具调用信息
       b. 执行工具
       c. 将结果转换为 role=tool 消息，添加到 messages
       d. 再次调用 LLM（带新的 messages）
       e. 重复直到 finish_reason=stop
    3. 返回最终回复
    """
```

#### 3.3.2 DialogueService 调用新方法

**文件**: `src/services/L3_scenario_coordination/L3a_task_coordination/dialogue_service.py`

修改 `process_dialogue()` 方法，调用 `execute_with_recursive_llm()` 替代 `execute_task()`。

```python
# 使用递归 LLM 调用执行任务（支持多轮工具调用）
execution_result = self.execution_service.execute_with_recursive_llm(
    task=task,
    session_id=session_id,
    user_input=user_input
)
```

---

## 4. 执行流程

### 4.1 修改后的执行流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 用户: "请完成todolist需求分析并保存到doc目录"                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ DialogueService.process_dialogue()                                     │
│   - 保存用户消息                                                       │
│   - 调用 execute_with_recursive_llm()                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ BaseExecutionService.execute_with_recursive_llm()                      │
│                                                                             │
│ 迭代 1:                                                                 │
│   - 调用 DialogueBasedLLMService.call_llm()                            │
│   - LLM 返回 tool_calls=[{name: "LS", ...}]                          │
│   - 执行 LS 工具                                                        │
│   - 添加 role=tool 消息到 messages[]                                   │
│                                                                             │
│ 迭代 2:                                                                 │
│   - 再次调用 DialogueBasedLLMService.call_llm()                        │
│   - LLM 返回 tool_calls=[{name: "Write", ...}]                        │
│   - 执行 Write 工具 → 文件被创建                                       │
│   - 添加 role=tool 消息到 messages[]                                   │
│                                                                             │
│ 迭代 3:                                                                 │
│   - 再次调用 DialogueBasedLLMService.call_llm()                        │
│   - LLM 返回 content="已完成..." (finish_reason=stop)                  │
│   - 返回最终回复                                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ WebSocket 发送: message_response                                      │
│   - content: "已完成todolist需求分析文档..."                           │
│   - tool_calls: [LS结果, Write结果]                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 messages 数组累积过程

```
Step 1 - 初始 messages:
messages = [
    {role: "system", content: "..."},
    {role: "user", content: "请完成..."}
]

Step 2 - LLM 返回 tool_calls:
messages = [
    {role: "system", content: "..."},
    {role: "user", content: "请完成..."},
    {role: "assistant", content: "", tool_calls: [{name: "LS", ...}]}
]

Step 3 - 执行 LS 后，添加 tool 消息:
messages = [
    {role: "system", content: "..."},
    {role: "user", content: "请完成..."},
    {role: "assistant", content: "", tool_calls: [{name: "LS", ...}]},
    {role: "tool", content: "{entries: [...]}", tool_call_id: "call-xxx"}
]

Step 4 - LLM 返回 Write tool_calls:
messages = [
    ...,
    {role: "assistant", content: "", tool_calls: [{name: "Write", ...}]}
]

Step 5 - 执行 Write 后:
messages = [
    ...,
    {role: "tool", content: "文件已保存", tool_call_id: "call-yyy"}
]

Step 6 - LLM 返回最终回复:
messages = [
    ...,
    {role: "assistant", content: "已完成todolist需求分析文档..."}
]
```

---

## 5. 职责边界说明

### 5.1 各服务职责

| 服务 | 职责 | 不做 |
|------|------|------|
| **DialogueBasedLLMService** | LLM 调用、消息构造、响应解析 | 工具执行、循环控制 |
| **ToolExecutor** | 执行单个工具 | LLM 调用、多工具协调 |
| **ToolTaskExecutor** | 单工具任务执行（含检查/调整） | LLM 循环 |
| **BaseExecutionService** | 协调 LLM 调用和工具执行的循环 | - |
| **DialogueService** | 对话生命周期管理 | 具体执行逻辑 |

### 5.2 新增方法职责

**`execute_with_recursive_llm()`** 方法职责：
1. 构建初始 `messages[]`
2. 调用 `DialogueBasedLLMService.call_llm()`
3. 检查响应是否有 `tool_calls`
4. 如果有：
   - 记录 assistant 消息（含 tool_calls）
   - 执行每个工具调用
   - 将工具结果转换为 `role=tool` 消息
   - 添加到 `messages[]`
   - 继续循环
5. 如果没有：
   - 记录 final assistant 消息
   - 返回结果

---

## 6. 影响范围

### 6.1 修改的文件

| 文件路径 | 修改类型 | 说明 |
|----------|----------|------|
| `base_execution_service.py` | 新增方法 | `execute_with_recursive_llm()` 协调 LLM 调用和工具执行的循环，并保存消息到 MessageService |
| `dialogue_service.py` | 修改方法 | `process_dialogue()` 调用新方法 |
| `dialogue_based_llm_service.py` | 修改方法 | `build_messages_from_history()` 从 MessageService 获取对话历史 |

### 6.2 保持不变的文件

| 服务 | 文件 | 说明 |
|------|------|------|
| ToolTaskExecutor | `tool_task_executor.py` | 职责未变 |
| IntentService | `intent_service.py` | 职责未变 |
| ToolExecutor | `L2c_tool_execution/__init__.py` | 职责未变 |
| MessageService | `message_service.py` | 职责未变 |

---

## 7. 历史消息问题修复

### 7.1 问题发现

分析 `llm_calls.json` 发现每次 LLM 调用只有 2 条消息：
- `[0] role=system`
- `[1] role=user`

缺少了：
- `assistant` 消息（包含 tool_calls）
- `tool` 消息（工具执行结果）

### 7.2 问题根因

`DialogueBasedLLMService.build_messages_from_history()` 使用 `MemoryService.get_short_term_memory()` 获取历史，但对话消息实际存储在 `MessageService` 管理的 `messages` 存储中。

```
MemoryService.get_short_term_memory() → short_term_memory 存储（空）
MessageService.list_messages()        → messages 存储（有数据）
```

### 7.3 修复方案

1. **修改 `DialogueBasedLLMService`**：
   - 添加 `MessageService` 和 `DialogService` 实例
   - 新增 `_get_dialog_history()` 方法从 `MessageService` 获取对话历史
   - 修改 `build_messages_from_history()` 调用新方法

2. **修改 `BaseExecutionService.execute_with_recursive_llm()`**：
   - 在执行工具后，将 `assistant` 消息（包含 tool_calls）保存到 `MessageService`
   - 将 `tool` 消息保存到 `MessageService`

### 7.4 修复后的消息流

```
用户输入 → MessageService 保存 user 消息
     ↓
LLM 返回 tool_calls → MessageService 保存 assistant 消息（含 tool_calls）
     ↓
执行工具 → MessageService 保存 tool 消息（含 tool_call_id）
     ↓
再次调用 LLM → build_messages_from_history() 从 MessageService 获取完整历史
     ↓
LLM 返回最终回复 → MessageService 保存 assistant 消息
```

---

## 8. 测试验证

### 8.1 单元测试

所有现有测试通过：
- L2c_tool_execution: 9 passed, 1 xfailed
- L3_scenario_coordination: 27 passed

### 8.2 验证场景

1. **单工具调用**：用户请求只需一个工具完成 → 验证 LLM 调用 2 次（1 工具 + 1 最终回复）
2. **多工具调用**：用户请求需要多个工具 → 验证 LLM 调用 N+1 次（N 工具 + 1 最终回复）
3. **直接完成**：用户请求无需工具 → 验证 LLM 调用 1 次

---

## 9. 附录：代码片段

### 8.1 execute_with_recursive_llm 核心逻辑

```python
def execute_with_recursive_llm(self, task: Task, session_id: str, user_input: str) -> Task:
    from .dialogue_based_llm_service import DialogueBasedLLMService

    max_iterations = 10
    iteration = 0
    messages = []

    llm_service = DialogueBasedLLMService()
    messages = llm_service.build_messages_from_history(session_id, user_input, llm_service.get_tools_for_llm())

    while iteration < max_iterations:
        iteration += 1

        # 调用 LLM
        llm_response = llm_service.call_llm(session_id=session_id, user_input=user_input)

        if not llm_response.success:
            task.status = TaskStatus.FAILED
            task.error_message = llm_response.error
            break

        # 检查是否有工具调用
        tool_calls = llm_response.tool_calls
        if tool_calls and len(tool_calls) > 0:
            # 记录 assistant 消息
            messages.append({
                "role": "assistant",
                "content": llm_response.content or "",
                "tool_calls": tool_calls
            })

            # 执行每个工具调用
            for tool_call in tool_calls:
                tool_result = self._execute_single_tool_call(tool_call, session_id)

                # 添加 role=tool 消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.get('id', ''),
                    "content": str(tool_result.get('result', ''))
                })

            continue

        # 如果没有工具调用，检查是否是最终回复
        if llm_response.content:
            messages.append({"role": "assistant", "content": llm_response.content})

            task.status = TaskStatus.COMPLETED
            task.output_data = {"result": llm_response.content, "iterations": iteration}
            task.completed_at = datetime.now()
            break

    return task
```

---

*文档版本：v2.0*
*创建日期：2026-05-21*
*作者：AI Assistant*
