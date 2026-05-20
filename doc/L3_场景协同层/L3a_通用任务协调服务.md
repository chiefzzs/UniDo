# L3a 通用任务协调服务目录

## 概述

**L3a 通用任务协调服务目录** 是任务编排的核心层，包含9个独立服务，每个服务只负责一件事：

| 服务名 | 职责 | 调用下层 |
|-------|------|---------|
| **DialogueService** | 对话管理，调用基础执行服务 | BaseExecutionService |
| **IntentService** | 意图分析，选择执行路径 | DialogueBasedLLMService |
| **BaseExecutionService** | 任务编排核心入口，协调执行 | IntentService + ToolTaskExecutor + TaskGroupExecutor |
| **ToolTaskExecutor** | 工具任务执行服务 | L2c工具执行服务 + CheckTaskService + AdjustTaskService |
| **CheckTaskService** | 工具任务检测服务 | BaseExecutionService（递归） |
| **AdjustTaskService** | 工具任务调整服务 | BaseExecutionService（递归） |
| **TaskExecutionService** | 任务执行服务 | BaseExecutionService（递归） |
| **TaskGroupExecutor** | 任务组执行服务 | TaskExecutionService |
| **DialogueBasedLLMService** | 基于对话的LLM调用服务 | L2d LLM执行服务 + L2b记忆服务 + L2f工具管理服务 |

---

对话主要流程：
前置流程：
    会话对象创建 ，存在session对象：
    用户输入对话，发起请求， 系统对话对象创建,构造好历史数据， 发起基础执行服务：**BaseExecutionService** 
         

本流程： 
   1） **BaseExecutionService** :  依据对话对象，调用意图服务对象进行分析意图
   2） **IntentService** :  
         + 调用DialogueBasedLLMService 进行大模型调用，得到三种类型（ 对话类型, 任务组工具选择类型，其他工具选择类型）
         + 发布意图分析完成消息（填充哪种类型） 
         + 对话类型：  调用messageManager：发布助手历史消息，   返回任务结束。 
         + 任务组类型： 依据信息创建任务组执行器，   调用TaskGroupExecutor：执行任务组，   返回任务结束。 
         + 其他工具选择类型： ,依据信息创建工具执行器,  调用ToolTaskExecutor：执行其他工具，   返回任务结束。 

   
   3） 调用DialogueBasedLLMService 进行大模型调用
        + 构造request  :  
          + 依据 Session对象 , 得到本Session的大模型信息
          + 读取Session对象的历史消息，构造messages列表
          + 读取工具管理的工具信息，得到Tools信息
          + 发布LLM请求构造完毕消息
        + 调用L2d LLM执行服务执行实际的LLM调用，得到LLM响应
        +  得到三种类型的反应
           +  文本对话返回
           +  选中任务组工具类型
           +  其他工具选择类型
   
   4） TaskGroupExecutor： 
     + 创建（ 依据对话对象， 任务组工具选择信息）
        + 直接生成一组任务执行器，挂接到本任务组执行器下
        + 发布任务组创建消息。
     +  依次调用任务组中的任务组执行器，执行
     +  完成人物组执行
    
    5） 任务执行器，执行
     + 创建： 依据任务信息创建任务
     + 执行：
       +  发布任务开始执行消息
       +  以任务内容为输入，构造系统历史消息 ？
       +  递归基础执行服务： BaseExecutionService
       +  发布任务执行完成消息
        
            
   6） 调用ToolTaskExecutor：执行其他工具，   返回任务结束。 
     + 执行工具
        +  利用大模型返回的信息，调用L2 工具执行服务 ，得到工具执行返回信息
        +  发布工具执行完成消息
        +  添加工具执行结果消息到对话历史中
    +  检查任务： 可选 （当前不实现）
    +  调整任务： 可选（当前不实现）





## 9. DialogueBasedLLMService（基于对话的LLM调用服务）

### 9.1 核心职责

- 通过历史记录构造标准格式的messages
- 通过工具管理服务获取工具定义并转换为LLM格式
- 调用L2d LLM执行服务执行实际的LLM调用
- 为意图分析层提供LLM调用能力
- 为任务规划提供LLM调用能力

### 9.2 依赖关系

| 依赖服务 | 层级 | 作用 |
|---------|------|------|
| **L2d LLM执行服务** | L2层 | 执行实际的LLM调用 |
| **L2b 记忆服务** | L2层 | 获取对话历史记录 |
| **L2f 工具管理服务** | L2层 | 获取工具定义列表 |

### 9.3 核心数据结构

```python
@dataclass
class DialogueMessage:
    role: str                    # system/user/assistant/tool
    content: str                 # 消息内容
    tool_call: Optional[Dict]    # 工具调用（可选）
    tool_result: Optional[Dict]  # 工具结果（可选）

@dataclass
class LLMRequest:
    session_id: str              # 会话ID
    messages: List[Dict]         # 消息列表
    model_config_id: str         # 模型配置ID
    max_tokens: int              # 最大token数
    temperature: float           # 温度参数
    tools: Optional[List[Dict]]  # 工具定义列表
    stream: bool                 # 是否流式输出

@dataclass
class LLMResponse:
    success: bool                # 是否成功
    content: str                 # 响应内容
    tool_calls: Optional[List]   # 工具调用列表
    usage: Optional[Dict]        # token使用情况
    error: Optional[str]         # 错误信息
```

### 9.4 关键方法

#### 9.4.1 build_messages_from_history()

```python
def build_messages_from_history(self, session_id: str, user_input: str) -> List[Dict[str, Any]]:
    """
    从历史记录构造messages
    
    输入: 会话ID + 用户输入
    输出: 构造好的messages列表（包含系统消息、历史消息、当前用户输入）
    """
    # 1. 添加系统消息
    # 2. 从L2b记忆服务获取历史消息
    # 3. 处理工具调用和工具结果消息
    # 4. 添加当前用户输入
```

#### 9.4.2 get_tools_for_llm()

```python
def get_tools_for_llm(self) -> List[Dict[str, Any]]:
    """
    获取工具定义并转换为LLM所需格式
    
    输入: 无
    输出: 工具定义列表（LLM格式）
    
    转换示例:
    ToolDefinition → {
        "type": "function",
        "function": {
            "name": "工具名称",
            "description": "工具描述",
            "parameters": {...}
        }
    }
    """
```

#### 9.4.3 call_llm()

```python
def call_llm(self, session_id: str, user_input: str, **kwargs) -> LLMResponse:
    """
    调用LLM执行服务
    
    输入: 会话ID + 用户输入 + 可选参数
    输出: LLMResponse对象
    
    流程:
    1. 构造LLMRequest（调用build_messages_from_history + get_tools_for_llm）
    2. 调用L2d LLM执行服务
    3. 解析响应并返回LLMResponse
    """
```

#### 9.4.4 analyze_intent()

```python
def analyze_intent(self, session_id: str, user_input: str) -> Dict[str, Any]:
    """
    基于LLM进行意图分析（为意图服务提供能力）
    
    输入: 会话ID + 用户输入
    输出: 意图分析结果
    
    输出格式:
    {
        "intent_type": "direct_completion|single_tool|task_group",
        "confidence": 0.0-1.0,
        "reasoning": "分析理由",
        "tool_info": {...},    # single_tool时包含
        "task_info": {...}     # task_group时包含
    }
    """
```

#### 9.4.5 generate_task_plan()

```python
def generate_task_plan(self, session_id: str, user_input: str) -> Dict[str, Any]:
    """
    生成任务规划（为任务组执行提供能力）
    
    输入: 会话ID + 用户输入
    输出: 任务规划
    
    输出格式:
    {
        "plan_name": "任务名称",
        "execution_mode": "sequential|parallel|dependency_based",
        "tasks": [{
            "task_id": "任务ID",
            "name": "任务名称",
            "description": "任务描述",
            "task_type": "direct|single_tool|task_group",
            "tool_name": "工具名称",
            "parameters": {...},
            "dependencies": ["依赖任务ID"]
        }],
        "summary": "任务规划摘要"
    }
    """
```

### 9.5 服务协作关系

```
用户请求
    │
    ↓
┌─────────────────────────────────┐
│   IntentService                │ ← 意图分析服务调用
│   analyze_intent()             │
└───────────┬─────────────────────┘
            │ 调用
            ↓
┌─────────────────────────────────┐
│   DialogueBasedLLMService      │ ← 基于对话的LLM调用服务
│   analyze_intent()             │
├─────────────────────────────────┤
│  ┌───────────────────────────┐  │
│  │ 1. build_messages_from_history │ ← 构造messages
│  │    → 调用 L2b 记忆服务    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ 2. get_tools_for_llm()   │  │ ← 获取工具定义
│  │    → 调用 L2f 工具管理    │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ 3. call_llm()            │  │ ← 执行LLM调用
│  │    → 调用 L2d LLM执行服务 │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
            │ 返回结果
            ↓
┌─────────────────────────────────┐
│   IntentService                │
│   继续处理意图分析结果         │
└─────────────────────────────────┘
```

### 9.6 数据流说明

1. **输入**：会话ID + 用户输入
2. **历史消息获取**：调用L2b记忆服务获取对话历史
3. **消息构造**：组合系统消息、历史消息、当前用户输入
4. **工具定义获取**：调用L2f工具管理服务获取工具定义
5. **格式转换**：将ToolDefinition转换为LLM工具格式
6. **LLM调用**：调用L2d LLM执行服务
7. **响应解析**：解析LLM响应为结构化的LLMResponse
8. **输出**：返回意图分析结果或任务规划

### 9.7 与意图服务的协作

DialogueBasedLLMService为IntentService提供核心的LLM调用能力：

| IntentService方法 | 调用的DialogueBasedLLMService方法 |
|------------------|----------------------------------|
| analyze_intent() | analyze_intent() + call_llm() |
| _analyze_with_llm() | call_llm() |

---
