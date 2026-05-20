# L1d 事件管理基础设施

## 1. 组件概念

**L1d 事件管理基础设施** 是系统的事件总线服务，负责实现事件的发布-订阅机制，为上层组件提供解耦的通信方式。事件数据通过 L1b 持久化组件存储到 JSON 文件，支持环境隔离和序列存储。

### 1.1 核心职责
- 提供事件发布与订阅能力
- 管理事件缓存与持久化（通过L1b）
- 支持事件追踪与回放
- 实现请求链路的关联追踪
- **事件持久化**：通过L1b将事件存储到JSON文件，支持数组格式和序列存储

### 1.2 设计理念
- **解耦性**：事件生产者和消费者完全解耦，通过事件总线进行通信
- **可追踪性**：通过 correlation_id 追踪完整请求链路
- **可靠性**：事件通过L1b持久化到磁盘，支持故障恢复
- **实时性**：支持事件的实时推送
- **序列支持**：事件按时间顺序存储，支持有序查询和回放

---

## 2. 数据类定义

### 2.1 Event（事件基类）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| event_id | str | 事件唯一标识 | 用于事件的唯一识别和去重 | 事件总线自动生成 |
| event_type | str | 事件类型 | 标识事件的类别，用于订阅过滤 | 事件发布者指定 |
| timestamp | datetime | 事件时间戳 | 记录事件发生的时间 | 事件总线自动生成 |
| payload | Dict[str, Any] | 事件载荷 | 包含事件的具体数据 | 事件发布者填充 |
| source_component | str | 发起组件 | 标识事件来源的组件层级 | 事件发布者指定 |
| source_service | str | 发起服务 | 标识事件来源的具体服务 | 事件发布者指定 |

### 2.2 EventRecord（事件记录）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| record_id | str | 记录唯一标识 | 用于存储记录的唯一识别 | 事件总线自动生成 |
| event_id | str | 关联事件ID | 关联到原始事件 | 从Event继承 |
| event_type | str | 事件类型 | 标识事件类别 | 从Event继承 |
| timestamp | str | 事件时间戳（字符串） | 便于持久化存储 | 从Event转换 |
| payload | Dict[str, Any] | 事件载荷 | 事件数据 | 从Event继承 |
| stored_at | str | 存储时间戳 | 记录实际存储时间 | 事件总线自动生成 |
| source_component | str | 发起组件 | 事件来源组件 | 从Event继承 |
| source_service | str | 发起服务 | 事件来源服务 | 从Event继承 |
| correlation_id | str | 关联ID | 用于追踪请求链路 | 事件总线自动生成或外部传入 |

### 2.3 EventTypes（事件类型常量）

| 事件类型 | 含义 | 使用场景 |
|---------|------|---------|
| project.created | 项目创建 | SC002 创建新项目 |
| project.updated | 项目更新 | SC003 项目配置 |
| project.deleted | 项目删除 | 删除项目 |
| session.created | 会话创建 | SC008 创建新会话 |
| session.updated | 会话更新 | 更新会话状态 |
| session.deleted | 会话删除 | SC012 删除会话 |
| message.created | 消息创建 | SC013 输入用户问题 |
| message.updated | 消息更新 | SC021 编辑历史消息 |
| message.deleted | 消息删除 | 删除消息 |
| llm.request_sent | LLM请求发送 | LLM调用开始 |
| llm.response_received | LLM响应接收 | LLM调用完成 |
| llm.stream_chunk | 流式分片 | 流式输出过程 |
| llm.error | LLM错误 | LLM调用失败 |
| tool.execution_started | 工具执行开始 | 工具调用开始 |
| tool.execution_completed | 工具执行完成 | 工具调用完成 |
| tool.execution_failed | 工具执行失败 | 工具调用失败 |
| round.started | 轮次开始 | 对话轮次开始 |
| round.completed | 轮次完成 | 对话轮次结束 |

---

## 3. 支持的场景

### 3.1 直接支持的场景

| 场景编号 | 场景名称 | 场景描述 |
|---------|---------|---------|
| SC013 | 输入用户问题 | 用户发送消息时发布 message.created 事件 |
| SC014 | 查看流式文本输出 | 接收 llm.stream_chunk 事件并推送 |
| SC015 | 查看思考过程 | 接收 think 类型的事件并展示 |
| SC016 | 查看工具调用 | 接收 tool.execution_started 事件 |
| SC017 | 查看工具执行 | 接收 tool.execution_completed 事件 |
| SC018 | 查看任务执行过程 | 接收 task.* 系列事件 |

### 3.2 作为下层组件支持的场景

几乎所有上层场景都依赖事件系统进行通信和状态同步：
- L2层：领域实体变更通知
- L3层：场景流程协调
- L4层：WebSocket消息推送
- L5层：UI状态更新

---

## 4. 数据流与控制流

### 4.1 事件发布流程

```
事件发布者                    EventBus                    事件订阅者
    |                            |                            |
    |--- publish(event) -------->|                            |
    |                            |                            |
    |                            |--- 创建 EventRecord -------->|
    |                            |                            |
    |                            |--- 存入内存缓存 ------------>|
    |                            |                            |
    |                            |--- 写入磁盘文件 ------------>|
    |                            |                            |
    |                            |--- 通知订阅者(callback)---->|
    |                            |                            |
    |<--- correlation_id --------|                            |
    |                            |                            |
```

### 4.2 事件订阅流程

```
订阅者                        EventBus                    事件发布者
    |                            |                            |
    |--- subscribe(type, cb) ---->|                            |
    |                            |                            |
    |                            |<--- publish(event) ---------|
    |                            |                            |
    |<--- callback(event) --------|                            |
    |                            |                            |
```

### 4.3 事件查询流程

```
查询者                        EventBus                    存储层
    |                            |                            |
    |--- get_events_by_correlation(id) --->|                 |
    |                            |                            |
    |                            |--- 从内存缓存查询 ---------->|
    |                            |                            |
    |                            |--- 从磁盘加载（可选）------>|
    |                            |                            |
    |<--- List[EventRecord] ------|                            |
    |                            |                            |
```

---

## 5. 如何使用下层组件

L1d 事件管理基础设施是 L1 层的最底层组件之一，不依赖其他业务组件。其依赖关系如下：

### 5.1 依赖的组件

| 组件 | 作用 | 使用方式 |
|-----|------|---------|
| 文件系统 | 事件持久化存储 | 使用 Path 和 json 模块写入文件 |
| uuid 模块 | 生成唯一ID | 使用 uuid.uuid4() 生成 event_id 和 correlation_id |
| datetime 模块 | 时间戳处理 | 使用 datetime.now() 获取当前时间 |

### 5.2 作为下层组件被使用

L1d 被上层组件以下列方式使用：

```python
# 1. 获取事件总线实例
from L1d_event_system import get_event_bus
event_bus = get_event_bus()

# 2. 发布事件
event = Event(
    event_type=EventTypes.MESSAGE_CREATED,
    payload={'message_id': 'msg-123', 'content': 'Hello'}
)
correlation_id = event_bus.publish(event)

# 3. 订阅事件
def handle_message(event):
    print(f"收到消息: {event.payload}")

event_bus.subscribe(EventTypes.MESSAGE_CREATED, handle_message)

# 4. 查询事件
events = event_bus.get_events_by_correlation(correlation_id)
```

---

## 6. 关键方法说明

### 6.1 publish(event, correlation_id=None)

**功能**：发布事件到事件总线

**参数**：
- event: Event 对象
- correlation_id: 可选的关联ID，用于链路追踪

**返回**：correlation_id

**处理流程**：
1. 生成/使用 correlation_id
2. 创建 EventRecord
3. 添加到内存缓存
4. 持久化到磁盘
5. 通知所有订阅者

### 6.2 subscribe(event_type, callback)

**功能**：订阅指定类型的事件

**参数**：
- event_type: 事件类型，支持通配符 "*"
- callback: 回调函数，接收 event 参数

### 6.3 get_events_by_correlation(correlation_id)

**功能**：根据关联ID获取所有相关事件

**参数**：
- correlation_id: 关联ID

**返回**：List[EventRecord]

### 6.4 get_events_by_type(event_type)

**功能**：根据事件类型获取所有事件

**参数**：
- event_type: 事件类型

**返回**：List[EventRecord]

---

## 7. 与其他L1组件的关系

### 7.1 与 L1b 持久化服务的关系

L1d 通过 L1b 进行事件持久化存储：
- 事件发布后，通过 L1b 的 `save_events()` 方法存储到 `events.json` 文件
- 事件查询通过 L1b 的 `get_events()` 方法从文件读取
- 支持环境隔离，根据 `STORAGE_ENV` 环境变量存储到不同目录
- 事件以数组格式存储，支持序列查询和回放

### 7.2 与 L1c LLM基础设施的关系

L1c 在 LLM 调用过程中会发布事件（llm.request_sent, llm.response_received等），L1d 负责传递这些事件给订阅者，并通过 L1b 持久化记录。

### 7.3 与 L1a 配置管理的关系

L1d 不依赖 L1a，但可以订阅配置变更事件来动态调整自身行为，如调整缓存大小、清理策略等。

---

## 8. 容错与恢复

### 8.1 事件持久化策略

- **内存缓存**：所有事件首先存入内存，保证快速访问
- **磁盘持久化**：异步写入 JSONL 文件，按日期分片存储
- **格式**：每行一个 JSON 对象，便于逐行读取

### 8.2 故障恢复

```
系统启动时
    |
    |--- 加载当天的事件文件
    |
    |--- 重建内存缓存
    |
    |--- 恢复订阅关系
    |
    |--- 继续处理新事件
```

### 8.3 数据清理

- 定期清理过期的事件文件（如超过30天）
- 提供手动清理接口
- 支持按时间范围删除

---

## 9. 性能考虑

### 9.1 异步持久化

事件写入磁盘采用异步方式，避免阻塞事件发布流程。

### 9.2 内存管理

- 实现 LRU 缓存策略
- 定期清理内存中的旧事件
- 提供缓存大小配置

### 9.3 订阅优化

- 支持按事件类型过滤
- 避免重复通知
- 支持批量事件处理

---

## 10. 安全考虑

### 10.1 事件过滤

订阅者可以通过事件类型进行过滤，避免接收无关事件。

### 10.2 敏感数据处理

事件载荷中的敏感数据（如 API Key）应在发布前进行脱敏处理。

### 10.3 访问控制

虽然 L1d 本身不提供访问控制，但上层组件可以在发布前进行权限验证。

---

## 附录：事件类型完整列表

### 项目事件
- project.created
- project.updated
- project.deleted

### 会话事件
- session.created
- session.updated
- session.deleted
- session.joined
- session.left

### 消息事件
- message.created
- message.updated
- message.deleted

### LLM事件
- llm.request_sent
- llm.response_received
- llm.stream_started
- llm.stream_chunk
- llm.stream_finished
- llm.error

### 工具事件
- tool.call_selected
- tool.execution_started
- tool.execution_progress
- tool.execution_completed
- tool.execution_failed

### 任务事件
- task.group_created
- task.group_completed
- task.created
- task.started
- task.completed
- task.failed

### 轮次事件
- round.started
- round.completed

### 错误事件
- error.occurred
