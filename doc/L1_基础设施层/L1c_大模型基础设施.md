# L1c 大模型基础设施

## 1. 组件概念

**L1c 大模型基础设施** 是系统与大语言模型（LLM）交互的核心组件，负责封装LLM API调用、支持流式响应处理，并提供请求构造和响应解析能力。LLM调用过程通过L1b持久化组件进行记录存储。

### 1.1 核心职责
- 封装LLM API调用接口
- 支持多种LLM服务提供商（Qwen、OpenAI、Claude等）
- 实现流式响应处理
- 提供请求构造和响应解析
- 支持模拟模式用于测试
- **调用记录持久化**：通过L1b将LLM调用记录存储到JSON文件

### 1.2 设计理念
- **抽象层**：屏蔽不同LLM服务的差异，提供统一接口
- **流式支持**：原生支持流式响应，提升用户体验
- **可测试性**：提供模拟模式，无需真实API即可测试
- **可扩展性**：支持新增LLM服务提供商
- **可追溯性**：所有LLM调用过程通过L1b持久化，支持后续审计和分析

---

## 2. 数据类定义

### 2.1 LLMRequest（LLM请求）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| model_name | str | 模型名称 | 指定要调用的LLM模型 | 用户配置 |
| messages | List[Dict[str, str]] | 消息列表 | 对话历史上下文 | 上层构造 |
| temperature | float | 温度参数 | 控制输出随机性（0-1） | 用户配置 |
| max_tokens | int | 最大token数 | 响应长度限制 | 用户配置 |
| stream | bool | 是否流式 | 是否启用流式响应 | 调用方指定 |
| api_type | str | API类型 | qwen/openai/claude | 用户配置 |
| api_address | str | API地址 | LLM服务端点 | 用户配置 |
| api_key | str | API密钥 | 认证凭证 | 用户配置 |

### 2.2 LLMResponse（LLM响应）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| content | str | 响应内容 | LLM返回的文本 | LLM API |
| finish_reason | str | 结束原因 | stop/length/timeout等 | LLM API |
| model_name | str | 模型名称 | 实际调用的模型 | LLM API |
| usage | Dict[str, int] | 使用统计 | 包含token使用量 | LLM API |

### 2.3 StreamChunk（流式响应分片）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| chunk_id | str | 分片ID | 分片唯一标识 | 服务自动生成 |
| delta | str | 分片内容 | 本次返回的文本片段 | LLM API |
| chunk_type | str | 分片类型 | text/think/tool_call | 服务识别 |
| finish_reason | Optional[str] | 结束原因 | 最后一个分片的结束原因 | LLM API |
| index | int | 分片索引 | 分片在序列中的位置 | 服务自动生成 |

### 2.4 LLMCallRecord（LLM调用记录）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| call_id | str | 调用ID | LLM调用唯一标识 | 服务自动生成 |
| session_id | str | 会话ID | 关联的会话 | 调用时指定 |
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

### 2.5 RequestConstructor（请求构造器配置）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| model_config | Dict[str, Any] | 模型配置 | 包含模型参数的字典 | 用户配置 |

---

## 3. 支持的场景

### 3.1 直接支持的场景

| 场景编号 | 场景名称 | 场景描述 |
|---------|---------|---------|
| SC013 | 输入用户问题 | 构造并发送LLM请求 |
| SC014 | 查看流式文本输出 | 处理流式响应分片 |
| SC015 | 查看思考过程 | 识别并处理think类型分片 |
| SC016 | 查看工具调用 | 识别并处理tool_call类型分片 |

### 3.2 作为下层组件支持的场景

所有需要LLM调用的上层场景都依赖 L1c：
- L2d LLM执行服务
- L3b 四大对话场景（SC04/SC05/SC16/SC17）
- L3a 通用任务协调

---

## 4. 数据流与控制流

### 4.1 非流式调用流程

```
上层服务                    L1c LLM基础设施                    LLM API                    L1b
        |                                    |                      |                      |
        |--- execute(request) -------------->|                      |                      |
        |                                    |                      |                      |
        |                                    |--- HTTP POST -------->|                      |
        |                                    |                      |                      |
        |                                    |<--- Response ---------|                      |
        |                                    |                      |                      |
        |                                    |--- 解析响应 ---------->|                      |
        |                                    |                      |                      |
        |                                    |--- 保存调用记录 ------->|                      |
        |                                    |                      |                      |
        |<--- LLMResponse -------------------|                      |                      |
        |                                    |                      |                      |
```

### 4.2 流式调用流程

```
上层服务                    L1c LLM基础设施                    LLM API                    L1b
        |                                    |                      |                      |
        |--- execute_stream(request) -------->|                      |                      |
        |                                    |                      |                      |
        |                                    |--- HTTP POST(stream)-->|                      |
        |                                    |                      |                      |
        |<--- on_chunk(chunk1) ---------------|<-- Chunk 1 -----------|                      |
        |<--- on_chunk(chunk2) ---------------|<-- Chunk 2 -----------|                      |
        |<--- on_chunk(chunk3) ---------------|<-- Chunk 3 -----------|                      |
        |                                    |                      |                      |
        |<--- LLMResponse -------------------|<-- 结束 --------------|                      |
        |                                    |                      |                      |
        |                                    |--- 保存调用记录 ------->|                      |
        |                                    |                      |                      |
```

### 4.3 请求构造流程

```
上层服务                    RequestConstructor                    LLMRequest
        |                                    |                      |
        |--- build(messages, config) -------->|                      |
        |                                    |                      |
        |                                    |--- 验证消息格式 ------->|
        |                                    |                      |
        |                                    |--- 应用模型配置 ------->|
        |                                    |                      |
        |                                    |--- 获取提示词内容 ------|
        |                                    |                      |
        |                                    |--- 构造请求对象 ------->|
        |                                    |                      |
        |<--- LLMRequest --------------------|                      |
        |                                    |                      |
```

---

## 5. 如何使用下层组件

### 5.1 依赖的组件

| 组件 | 作用 | 使用方式 |
|-----|------|---------|
| requests/httpx | HTTP请求 | 发送API请求 |
| json 模块 | 数据序列化 | 请求/响应JSON处理 |
| uuid 模块 | 生成唯一ID | 生成chunk_id和call_id |
| datetime 模块 | 时间戳处理 | 记录请求时间 |
| L1b 持久化服务 | 调用记录存储 | 保存LLMCallRecord |

### 5.2 作为下层组件被使用

L1c 被上层组件以下列方式使用：

```python
# 1. 获取LLM客户端
from L1c_llm_infrastructure import get_llm_client
llm_client = get_llm_client()

# 2. 构造请求
request = LLMRequest(
    model_name="qwen-turbo",
    messages=[{'role': 'user', 'content': 'Hello'}],
    temperature=0.7,
    max_tokens=4096,
    stream=True
)

# 3. 非流式调用（自动保存调用记录）
response = llm_client.send_request(request, session_id="sess-123", model_config_id="model-456")
print(response.content)

# 4. 流式调用（自动保存调用记录）
def on_chunk(chunk):
    print(chunk.delta, end='')

response = llm_client.send_stream_request(
    request, 
    on_chunk=on_chunk,
    session_id="sess-123", 
    model_config_id="model-456"
)

# 5. 使用RequestConstructor
from L1c_llm_infrastructure import RequestConstructor

config = {'model_name': 'qwen-turbo', 'temperature': 0.7, 'prompt_id': 'prompt-123'}
constructor = RequestConstructor(config)
request = constructor.build([{'role': 'user', 'content': 'Hello'}])
```

---

## 6. 关键方法说明

### 6.1 LLMAPIClient

#### send_request(request, session_id=None, model_config_id=None)

**功能**：发送非流式LLM请求，并自动保存调用记录

**参数**：
- request: LLMRequest 对象
- session_id: 可选的会话ID，用于关联调用记录
- model_config_id: 可选的模型配置ID，用于关联调用记录

**返回**：LLMResponse

**处理流程**：
1. 验证请求数据
2. 根据api_type选择请求方式
3. 记录开始时间
4. 发送HTTP请求
5. 解析响应
6. 计算耗时
7. 保存LLMCallRecord到L1b
8. 返回LLMResponse

#### send_stream_request(request, on_chunk, session_id=None, model_config_id=None)

**功能**：发送流式LLM请求，并自动保存调用记录

**参数**：
- request: LLMRequest 对象
- on_chunk: 分片回调函数
- session_id: 可选的会话ID，用于关联调用记录
- model_config_id: 可选的模型配置ID，用于关联调用记录

**返回**：LLMResponse

**处理流程**：
1. 验证请求数据
2. 发送流式HTTP请求
3. 逐块接收响应
4. 调用on_chunk回调
5. 组装完整响应
6. 保存LLMCallRecord到L1b
7. 返回LLMResponse

### 6.2 RequestConstructor

#### build(messages, **kwargs)

**功能**：构建LLM请求

**参数**：
- messages: 消息历史列表
- **kwargs: 额外参数（可覆盖配置）

**返回**：LLMRequest

**处理流程**：
1. 从配置或kwargs获取参数
2. 验证消息格式
3. 如果配置中有prompt_id，获取提示词内容并添加到消息列表
4. 构造消息列表
5. 返回LLMRequest对象

### 6.3 ChunkStreamProcessor

#### process(chunk)

**功能**：处理单个分片

**参数**：
- chunk: StreamChunk 对象

**处理流程**：
1. 保存分片到列表
2. 累积内容
3. 更新当前类型

#### get_full_content()

**功能**：获取完整内容

**返回**：str（所有分片内容的拼接）

---

## 7. 与其他L1组件的关系

### 7.1 与 L1d 事件系统的关系

L1c 在关键节点发布事件：
- llm.request_sent: 请求发送时
- llm.response_received: 响应接收时
- llm.stream_chunk: 流式分片到达时
- llm.error: 错误发生时

### 7.2 与 L1b 持久化服务的关系

L1c 将LLM调用记录保存到 L1b：
- 调用完成后，自动创建 LLMCallRecord 对象
- 通过 L1b 的 `save_llm_call()` 方法保存到 `llm_calls.json`
- 支持环境隔离，根据 `STORAGE_ENV` 环境变量存储到不同目录

### 7.3 与 L1a 配置管理的关系

L1c 从 L1a 获取模型配置（API地址、密钥等）。

---

## 8. 容错与恢复

### 8.1 错误处理

- 捕获HTTP请求异常
- 处理API错误响应
- 支持重试机制
- 提供错误事件通知
- 错误时仍保存调用记录（status=failed）

### 8.2 超时处理

- 设置连接超时和读取超时
- 流式响应设置最大等待时间
- 超时后发布错误事件
- 记录超时调用记录

### 8.3 降级策略

- 支持模拟模式作为降级方案
- 提供默认响应
- 记录降级日志
- 模拟模式下仍保存调用记录

---

## 9. 性能考虑

### 9.1 连接池

- 使用HTTP连接池复用连接
- 配置连接池大小
- 设置连接超时

### 9.2 流式优化

- 尽快开始处理第一个分片
- 避免阻塞后续分片处理
- 支持异步处理

### 9.3 请求缓存

- 缓存相同请求的响应
- 设置缓存过期时间
- 提供缓存管理接口

---

## 10. 安全考虑

### 10.1 API密钥管理

- 不在日志中记录API密钥
- 使用环境变量存储密钥
- 支持密钥轮换

### 10.2 请求验证

- 验证请求参数
- 限制请求大小
- 防止恶意请求

### 10.3 数据传输

- 使用HTTPS传输
- 验证服务器证书
- 支持代理配置

---

## 附录：API类型支持

### 支持的LLM服务

| API类型 | 服务提供商 | 示例模型 |
|---------|----------|---------|
| qwen | 阿里云通义千问 | qwen-turbo, qwen-plus |
| openai | OpenAI | gpt-3.5-turbo, gpt-4 |
| claude | Anthropic | claude-3-sonnet, claude-3-opus |

### 配置示例

```python
# 模型配置示例
model_config = {
    'model_name': 'qwen-turbo',
    'api_type': 'qwen',
    'api_address': 'https://api.qwen.xfyun.cn/v1/chat/completions',
    'api_key': 'your-api-key',
    'temperature': 0.7,
    'max_tokens': 4096,
    'prompt_id': 'prompt-123'  # 关联提示词
}
```

### 模拟模式

```python
# 创建模拟模式客户端
client = LLMAPIClient(mock_mode=True)

# 模拟模式下不调用真实API，返回预设响应
response = client.send_request(request)
# 返回: "这是一个模拟响应。您的问题是：xxx..."
```

### LLMCallRecord 存储示例

```python
# LLM调用记录自动保存示例
# 调用后自动生成并保存到 llm_calls.json
{
    "call_id": "llm-123",
    "session_id": "sess-123",
    "model_config_id": "model-456",
    "request": {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "qwen-turbo",
        "temperature": 0.7,
        "max_tokens": 4096,
        "stream": false
    },
    "response": {
        "choices": [{"message": {"role": "assistant", "content": "Hi!"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3},
        "model": "qwen-turbo"
    },
    "status": "completed",
    "duration_ms": 1200,
    "created_at": "2026-05-18T10:00:00"
}
```
