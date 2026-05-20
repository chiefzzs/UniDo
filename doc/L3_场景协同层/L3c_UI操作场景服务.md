# L3c UI操作场景目录

## 概述

**L3c UI操作场景目录** 是一个包含UI操作相关组件的目录，按用户界面操作的类型进行组织。

---

## 目录结构

```
L3c_UI操作场景/
├── ProjectManager/           # 项目管理组件
│   ├── __init__.py
│   ├── CreateProject.py      # 创建项目
│   ├── UpdateProject.py      # 更新项目
│   ├── DeleteProject.py      # 删除项目
│   └── ListProjects.py       # 项目列表
├── SessionManager/           # 会话管理组件
│   ├── __init__.py
│   ├── CreateSession.py      # 创建会话
│   ├── UpdateSession.py      # 更新会话
│   ├── DeleteSession.py      # 删除会话
│   ├── ArchiveSession.py     # 归档会话
│   └── ListSessions.py      # 会话列表
├── DialogueOutputManager/    # 对话输出管理组件
│   ├── __init__.py
│   ├── StreamOutput.py       # 流式输出
│   ├── ThinkBlock.py         # 思考块展示
│   ├── ToolCall.py           # 工具调用展示
│   └── MessageDisplay.py     # 消息展示
└── ConfigManager/            # 配置管理组件
    ├── __init__.py
    ├── WorkspaceConfig.py    # 工作区配置
    ├── ModelConfig.py        # 模型配置

```

---

## 组件说明

### 1. ProjectManager（项目管理组件）

**职责**：处理项目的增删改查操作

| 组件 | 职责 |
|-----|------|
| CreateProject | 创建新项目 |
| UpdateProject | 更新项目配置 |
| DeleteProject | 删除项目 |
| ListProjects | 获取项目列表 |

**调用下层**：
- L2a 领域实体管理服务

支持场景：
  + 新建项目
  + 更新项目配置
  + 删除项目
  + 获取项目列表

主要流程：
  1） 用户创建项目 ，输入项目名称、选择workspace关联 , 选择模型配置关联
  2） 用户提交 ，后台自动保存project对象 

  结果：
    src/data/{env_name}/projects.json中多了一个project对象，包含项目名称、workspace关联、模型配置关联等信息
    src/data/{env_name}/events.json中多了一个event对象，包含项目创建事件、项目ID等信息
---

### 2. SessionManager（会话管理组件）

**职责**：处理会话的增删改查操作

| 组件 | 职责 |
|-----|------|
| CreateSession | 创建新会话 |
| UpdateSession | 更新会话状态 |
| DeleteSession | 删除会话 |
| ArchiveSession | 归档会话 |
| ListSessions | 获取会话列表 |

**调用下层**：
- L2a 领域实体管理服务
- L2b 记忆与状态管理服务

---
支持场景：
  1、 会话创建 
        1） 新建session对象：
        2） 初始化此session对象包含的会话对象
        3） 给第一个会话对象增加system message，用于引导对话方向。

      结果：
        src/data/{env_name}/sessions.json中多了一个session对象，包含会话ID、项目ID、 对话id等信息
        src/data/{env_name}/events.json中多了一个event对象，包含会话创建事件、会话ID、项目ID、 对话id等信息
        src/data/{env_name}/dialogs.json中多了一个dialog对象，包含对话ID、会话ID、 对话名称、 对话状态、 对话消息等信息
        src/data/{env_name}/messages.json中多了一个message对象，包含消息ID、对话ID、用户输入、系统回复等信息


   2、新建对话对象：
          1） 如果是第一次，返回session对象的第一个会话对象
          2） 如果不是第一次，session对象新建一个对话对象，并放到自己的队列中，返回新对话对象

   3、 得到历史消息

       非压缩式获得：
          1） 从session对象中获取所有对话对象
          2） 从每个对话对象中获取所有消息对象
          3） 合并所有消息对象，返回给用户
       压缩式获得：
          当历史消息 > 设定的上限， 
            1、最近的会话对象，读取所有消息
            2、历史对话，读取压缩消息
   4、 得到大模型信息
       依据本Session 关联的Project ，得到关联的大模型信息，返回大模型信息
       
```
@dataclass
class Session:
    session_id: str              # 会话唯一标识
    project_id: str              # 所属项目
    name: str                    # 会话名称
    status: str                  # active/inactive
    dialogs: List["Dialog"]      # 包含的对话列表 ，持久化的时候，只保存对话id
    created_at: datetime
    updated_at: datetime

@dataclass  
class Dialog:
    dialog_id: str               # 对话唯一标识
    session_id: str              # 所属会话
    name: str                    # 对话名称
    messages: List["Message"]    # 包含的消息列表 ，持久化的时候，只保存消息id
    status: str                  # ongoing/finished
    created_at: datetime

@dataclass
class Message:
    message_id: str              # 消息唯一标识
    dialog_id: str               # 所属对话（而非直接属于Session）
    role: str                    # user/assistant/tool/system
    content: str                 # 消息内容
    metadata: Dict[str, Any]     # 附加元数据（如工具调用信息）
    created_at: datetime

```


### 3. DialogueOutputManager（对话输出管理组件）

**职责**：管理对话区的消息展示、流式输出等

| 组件 | 职责 |
|-----|------|
| StreamOutput | 处理流式文本输出 |
| ThinkBlock | 展示LLM思考过程 |
| ToolCall | 展示工具调用信息 |
| MessageDisplay | 展示消息内容 |

**调用下层**：
- L1d 事件管理基础设施（订阅流式事件）


支持场景：
  + 处理用户的一次对话 ： 新建对话对象，处理用户输入 ，调用通用任务协调流程
  
  主要流程：
      1、 向 session 对象得到一个新的 dialog 对象
      2、 生成一个用户输入的message 对象， 保存到次dialog对象的消息列表中 ，包含用户输入， 包含环境信息（操作系统， 当前工作区目录）
      3、 调用通用任务协调流程 
      4、 结束会话，启动对话压缩历史
          1） 压缩本对话的所有消息，生成压缩消息对象
          2） 保存压缩消息对象

  状态：
    1、 idle   :  首次创建的对象
    2、 ongoing ： 对话进行中
    3、 finished ： 对话结束
---


### 4. MessageManager（消息管理组件）
  支持创建历史消息对象
  可创建 
  
  1、system message 用于引导对话方向
  2、user message 用于用户输入
  3、assistant message 用于系统回复
  4、tool message 用于工具调用结果

 
 提供接口支持不同的客户调用次服务来创建不同的类型的消息对象

#### 4.1 四种消息类型报文格式

##### 4.1.1 System Message（系统消息）

```json
{
  "message_id": "msg-xxx",
  "dialog_id": "dialog-xxx",
  "role": "system",
  "content": "你是一个智能助手，能够帮助用户完成各种任务。",
  "metadata": {
    "type": "system",
    "source": "system_prompt"
  },
  "created_at": "2026-05-19T10:00:00Z"
}
```

**用途**：用于引导对话方向，设置助手行为模式和角色定位。

##### 4.1.2 User Message（用户消息）

```json
{
  "message_id": "msg-xxx",
  "dialog_id": "dialog-xxx",
  "role": "user",
  "content": "帮我分析一下这个项目的结构",
  "metadata": {
    "type": "user_input",
    "source": "ui"
  },
  "created_at": "2026-05-19T10:01:00Z"
}
```

参考内容：

```json
  {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": "<system-reminder>\n\nThis is a reminder that your todo list is currently empty. DO NOT mention this to the user explicitly because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this message to the user.\n\n</system-reminder>\n\n"
            },
            {
              "type": "text",
              "text": "\n<system-reminder>\nAs you answer the user's questions, you can use the following context:\n\nHere is useful information about the environment you are running in:\n<env>\nOperating system: windows\nWorking directories:\nd:\\learnning\\llm_ctrl\nToday's date: 2026-05-12\n</env>\n\n# important-instruction-reminders\nDo what has been asked; nothing more, nothing less.\nNEVER create files unless they're absolutely necessary for achieving your goal.\nALWAYS prefer editing an existing file to creating a new one.\nNEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.\n\n    IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context or otherwise consider it in your response unless it is highly relevant to your task. Most of the time, it is not relevant.\n\n</system-reminder>\n\n\n\n"
            },
            {
              "type": "text",
              "text": "\n<system-reminder>\n\n# Response Language Settings\nYou MUST follow these language requirements when responding to the user:\n- Always use the same language as the user's latest message unless user explicitly asks.\n- For code comments, follow the same language rule unless explicitly instructed otherwise\n- Maintain consistency in language throughout the conversation\n\n</system-reminder>\n\n"
            },
            {
              "type": "text",
              "text": "\n<user_input>\ndo'cdoc\n</user_input>\n\n<system-reminder>\n- Before starting any task, first review the Skill tool description to check if any skill in its <available_skills> is relevant to the <user_input> intent. When a skill is relevant, you must invoke the Skill tool IMMEDIATELY as your first action.\n</system-reminder>\n\n\n\n"
            }
          ]
        }
```

**用途**：用于封装用户输入内容。

##### 4.1.3 Assistant Message（助手消息）

```json
{
  "message_id": "msg-xxx",
  "dialog_id": "dialog-xxx",
  "role": "assistant",
  "content": "好的，我来帮您分析项目结构。首先让我查看一下目录结构。",
  "tool_calls": [
    {
      "id": "call-xxx",
      "type": "function",
      "function": {
        "name": "LS",
        "parameters": {
          "path": "/workspace/project"
        }
      }
    }
  ],
  "metadata": {
    "type": "assistant_response",
    "source": "llm"
  },
  "created_at": "2026-05-19T10:02:00Z"
}
```

**用途**：用于系统回复，可包含工具调用指令。

##### 4.1.4 Tool Message（工具消息）

```json
{
  "message_id": "msg-xxx",
  "dialog_id": "dialog-xxx",
  "role": "tool",
  "content": "{\"files\": [\"README.md\", \"src/\", \"tests/\"], \"directories\": [\"src\", \"tests\"]}",
  "metadata": {
    "type": "tool_result",
    "source": "tool_executor",
    "call_id": "call-xxx",
    "tool_name": "LS",
    "success": true
  },
  "created_at": "2026-05-19T10:03:00Z"
}
```

**用途**：用于工具调用结果返回。

#### 4.2 消息创建接口

| 接口方法 | 参数 | 返回值 | 说明 |
|---------|------|--------|------|
| `create_system_message()` | content, dialog_id | Message | 创建系统消息 |
| `create_user_message()` | content, dialog_id | Message | 创建用户消息 |
| `create_assistant_message()` | content, dialog_id, tool_calls=None | Message | 创建助手消息 |
| `create_tool_message()` | content, dialog_id, call_id, tool_name, success=True | Message | 创建工具消息 |





### 5. ConfigManager（配置管理组件）

**职责**：处理各类配置的增删改查

| 组件 | 职责 |
|-----|------|
| WorkspaceConfig | 工作区配置管理 |
| ModelConfig | 模型配置管理 |


**调用下层**：
- L1a 统一配置管理服务

---

## 数据流

```
L5 UI操作 → L3c组件 → L2服务/L1服务 → L1b持久化 → 存储
                ↓
         发布UI更新事件
                ↓
         L5 UI响应更新
```

---

## 与L3a的关系

L3c负责UI操作，L3a负责对话执行。两者协作完成完整用户体验：

```
用户输入 → L3c输入组件 → L3a DialogueService → L2/L1服务
                ↑                           ↓
                └───── L1d事件 ←────────────┘
                                    ↓
                            L3c输出组件 → L5 UI展示
```
