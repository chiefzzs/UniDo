# L2e 请求构造服务

## 1. 服务定位

**L2e 请求构造服务** 是 L2 领域记忆与执行层的核心组件之一，负责构建和格式化LLM请求，包括prompt构建、上下文管理和参数配置。

### 1.1 核心职责
- **Prompt构建**：构建LLM请求的prompt
- **上下文格式化**：格式化上下文信息
- **工具描述集成**：从L2f获取工具和技能的描述信息
- **参数配置**：配置LLM请求参数

### 1.2 设计原则
- **模板化**：支持可配置的prompt模板
- **上下文感知**：根据会话状态构建合适的上下文
- **工具集成**：自动集成可用工具和技能

---

## 2. 数据结构定义

### 2.1 PromptTemplate（Prompt模板）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| template_id | str | 模板唯一标识 | 非空，唯一 |
| name | str | 模板名称 | 非空 |
| content | str | 模板内容（支持占位符） | 非空 |
| type | str | 模板类型（system/user/assistant） | 非空 |
| parameters | List[str] | 参数列表 | 可选 |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.2 LLMRequest（LLM请求）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| messages | List[Dict] | 消息列表 | 非空 |
| model | str | 模型名称 | 非空 |
| temperature | float | 温度参数 | 默认0.7 |
| max_tokens | int | 最大token数 | 默认2048 |
| tools | List[Dict] | 工具描述列表 | 可选 |
| tool_choice | str | 工具选择策略 | 默认auto |
| stream | bool | 是否流式响应 | 默认true |

### 2.3 持久化数据格式

L2e 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.3.1 PromptTemplate
- **存储位置**：`src/data/{env_type}/prompt_template.json`
- **存储内容**：
```json
[
  {
    "template_id": "template-001",
    "name": "系统Prompt模板",
    "content": "你是一个{{role}}，帮助用户完成{{task}}",
    "type": "system",
    "parameters": ["role", "task"],
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.3.2 LLMRequest
- **存储位置**：`src/data/{env_type}/llm_request.json`
- **存储内容**：
```json
[
  {
    "messages": [
      {"role": "system", "content": "你是一个有帮助的助手"},
      {"role": "user", "content": "你好"}
    ],
    "model": "Qwen/Qwen3.5-397B-A17B",
    "temperature": 0.7,
    "max_tokens": 2000,
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "SearchCodebase",
          "description": "搜索代码库中的相关代码",
          "parameters": {
            "type": "object",
            "properties": {
              "information_request": {
                "type": "string",
                "description": "需要查找的信息描述"
              }
            },
            "required": ["information_request"]
          }
        }
      }
    ],
    "tool_choice": "auto",
    "stream": true
  }
]
```

#### 2.3.3 RequestConfiguration
- **存储位置**：`src/data/{env_type}/request_configuration.json`
- **存储内容**：
```json
[
  {
    "config_id": "req-config-001",
    "name": "默认请求配置",
    "model": "Qwen/Qwen3.5-397B-A17B",
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": true,
    "default_tools": ["SearchCodebase", "Read", "Write"]
  }
]
```

---

## 3. 关键方法定义

### 3.1 PromptBuilder（Prompt构建器）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| build_system_prompt(session_id, template_id=None) | 构建系统prompt | session_id: str, template_id: Optional[str] | str |
| build_user_prompt(message) | 构建用户prompt | message: Message | str |
| build_agent_info() | 构建agent信息 | 无 | str |

### 3.2 ContextBuilder（上下文构建器）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| build_context(session_id, max_tokens=None) | 构建上下文 | session_id: str, max_tokens: Optional[int] | List[Dict] |
| truncate_context(messages, max_tokens) | 截断上下文 | messages: List[Dict], max_tokens: int | List[Dict] |
| format_memory(memory) | 格式化记忆 | memory: Any | List[Dict] |

 

### 3.4 RequestBuilder（请求构建器）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| build_request(session_id, messages, **kwargs) | 构建LLM请求 | session_id: str, messages: List[Dict], **kwargs | LLMRequest |
| build_stream_request(session_id, messages, **kwargs) | 构建流式请求 | session_id: str, messages: List[Dict], **kwargs | LLMRequest |
| build_batch_request(session_id, messages, **kwargs) | 构建批量请求 | session_id: str, messages: List[Dict], **kwargs | LLMRequest |
| validate_request(request) | 验证请求 | request: LLMRequest | bool |

---

## 4. 与其他组件的关系

### 4.1 依赖关系

| 组件 | 关系类型 | 说明 |
|-----|---------|------|
| L2b 记忆与状态管理服务 | 依赖 | 获取会话上下文和消息 |
| L2a 项目与配置管理服务 | 依赖 | 获取项目和模型配置 |
| L2f 工具管理服务 | 依赖 | 获取工具和技能描述 |

### 4.2 被调用关系

| 组件 | 调用方式 | 说明 |
|-----|---------|------|
| L2d LLM执行服务 | 读取 | 获取构造好的请求 |
| L3a 通用任务协调服务 | 读取 | 获取请求配置 |

### 4.3 协作流程示例

**构建请求流程：**
```
L2d请求构建                 L2e                    L2b                    L2f                    L2a
        |                    |                      |                      |                      |
        |--- build_request -->|                      |                      |                      |
        |                    |                      |                      |                      |
        |                    |--- get_context ------>|                      |                      |
        |                    |                      |                      |                      |
        |                    |<--- messages ----------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- get_tools --------->|                      |                      |
        |                    |                      |                      |                      |
        |                    |<--- tools -------------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- get_config -------->|                      |
        |                    |                      |                      |                      |
        |                    |<--- config ------------|                      |
        |                    |                      |                      |                      |
        |                    |--- build_prompt ----->|                      |                      |
        |                    |                      |                      |                      |
        |<--- LLMRequest ------|                      |                      |                      |
```

---

## 5. Prompt模板机制

### 5.1 模板格式
支持占位符替换，例如：
```
你是一个专业的助手，擅长{domain}领域。
当前工作区：{workspace}
```

### 5.2 模板变量
| 变量名 | 说明 | 来源 |
|-------|------|------|
| {workspace} | 工作区路径 | L2a |
| {model} | 当前模型 | L2a |
| {domain} | 领域类型 | L2a |
| {date} | 当前日期 | 系统 |
| {time} | 当前时间 | 系统 |

---

## 6. 容错与恢复

### 6.1 错误处理
- 处理上下文获取失败
- 处理工具描述获取失败
- 返回有意义的错误信息

### 6.2 默认策略
- 使用默认模板
- 使用默认参数
- 跳过不可用的工具