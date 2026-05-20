# L2f 工具管理服务

## 1. 服务定位

**L2f 工具管理服务** 是 L2 领域记忆与执行层的核心组件之一，负责管理工具的注册、描述生成、能力评估，以及将技能作为工具纳入统一管理。

### 1.1 核心职责
- **工具注册**：注册新工具（支持自动注册机制）
- **工具描述生成**：生成工具的JSON Schema描述
- **工具能力评估**：评估工具能力
- **技能集成**：将技能作为工具纳入统一管理（支持技能自动注册）
- **工具列表聚合**：聚合原生工具和技能，提供统一的工具列表

### 1.2 设计原则
- **统一接口**：工具和技能提供统一的调用接口
- **动态发现**：支持运行时工具注册和自动发现
- **能力评估**：评估工具的适用性
- **自动注册**：支持工具和技能的自动注册机制

---

## 2. 数据结构定义

### 2.1 Tool（工具）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| tool_id | str | 工具唯一标识 | 非空，唯一 |
| name | str | 工具名称 | 非空 |
| description | str | 工具描述 | 非空 |
| function_name | str | 函数名称（工具实现函数名） | 非空 |
| parameters | Dict | 参数JSON Schema | 非空 |
| return_type | str | 返回类型 | 可选 |
| type | str | 工具类型（native/skill） | 默认native |
| skill_id | str | 关联的技能ID（type=skill时） | 可选 |
| category | str | 工具分类 | 默认general |
| enabled | bool | 是否启用 | 默认true |
| timeout | int | 超时时间（秒） | 默认30 |
| retry_count | int | 重试次数 | 默认0 |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.4 ToolCategory（工具分类）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| category | str | 分类名称 | 非空，唯一 |
| description | str | 分类描述 | 可选 |
| icon | str | 分类图标 | 可选 |

### 2.2 ToolCapability（工具能力）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| tool_id | str | 关联的工具ID | 非空 |
| category | str | 能力类别 | 非空 |
| score | float | 能力评分(0-1) | 默认0.5 |
| description | str | 能力描述 | 可选 |

### 2.3 AutoRegistrationConfig（自动注册配置）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| config_id | str | 配置唯一标识 | 非空，唯一 |
| enabled | bool | 是否启用自动注册 | 默认true |
| scan_interval | int | 扫描间隔（秒） | 默认300 |
| tool_discovery_paths | List[str] | 工具发现路径列表 | 可选 |
| skill_auto_register | bool | 是否自动注册技能 | 默认true |
| auto_enable_new_tools | bool | 是否自动启用新工具 | 默认true |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.5 持久化数据格式

L2f 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.5.1 Tool
- **存储位置**：`src/data/{env_type}/tool.json`
- **存储内容**：
```json
[
  {
    "tool_id": "tool-001",
    "name": "文件读取",
    "description": "读取指定路径的文件内容",
    "function_name": "read_file",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string",
          "description": "文件路径"
        }
      },
      "required": ["path"]
    },
    "return_type": "string",
    "type": "native",
    "skill_id": null,
    "category": "file_operation",
    "enabled": true,
    "timeout": 30,
    "retry_count": 0,
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.5.2 ToolCategory
- **存储位置**：`src/data/{env_type}/tool_category.json`
- **存储内容**：
```json
[
  {
    "category": "file_operation",
    "description": "文件操作相关工具",
    "icon": "file-icon"
  }
]
```

#### 2.5.3 ToolCapability
- **存储位置**：`src/data/{env_type}/tool_capability.json`
- **存储内容**：
```json
[
  {
    "tool_id": "tool-001",
    "category": "文件处理",
    "score": 0.9,
    "description": "擅长文件读取和处理"
  }
]
```

#### 2.5.4 AutoRegistrationConfig
- **存储位置**：`src/data/{env_type}/auto_registration_config.json`
- **存储内容**：
```json
[
  {
    "config_id": "auto-reg-001",
    "enabled": true,
    "scan_interval": 300,
    "tool_discovery_paths": ["/workspace/tools", "/workspace/plugins"],
    "skill_auto_register": true,
    "auto_enable_new_tools": true,
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

---

## 3. 关键方法定义

### 3.1 ToolRegistry（工具注册）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| register_tool(name, description, function_name, parameters, **kwargs) | 注册工具 | name: str, description: str, function_name: str, parameters: Dict | Tool |
| unregister_tool(tool_id) | 注销工具 | tool_id: str | bool |
| get_tool(tool_id) | 获取工具 | tool_id: str | Optional[Tool] |
| update_tool(tool_id, **kwargs) | 更新工具配置 | tool_id: str, 字段名=值 | Optional[Tool] |
| list_tools(project_id=None, enabled=True) | 列出工具 | project_id: Optional[str], enabled: bool | List[Tool] |
| list_tools_by_category(category) | 按分类列出工具 | category: str | List[Tool] |
| enable_tool(tool_id) | 启用工具 | tool_id: str | bool |
| disable_tool(tool_id) | 禁用工具 | tool_id: str | bool |
| register_category(category, description=None, icon=None) | 注册工具分类 | category: str, description: Optional[str], icon: Optional[str] | ToolCategory |
| list_categories() | 列出所有分类 | 无 | List[ToolCategory] |

提供判定： 本工具是否创建任务组的工具

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| is_task_group_tool(tool_id) | 判断工具是否为任务组工具 | tool_id: str | bool |

#### 3.1.5 任务组工具判定机制

**判定逻辑**：
1. 优先检查内存中已注册的工具定义（`ToolDefinition.is_task_group_tool`）
2. 若内存中未找到，尝试从工具描述符文件（JSON）中读取 `is_task_group_tool` 字段
3. 支持通过工具ID或工具名称进行查询

**工具注册标记**：
在调用 `register_tool()` 时可通过 `is_task_group_tool` 参数标识工具类型：

```python
tool_mgmt = ToolManagementService()
tool_mgmt.register_tool(
    tool_name="TodoWrite",
    category="Task",
    description="Create todo list for tracking progress",
    is_task_group_tool=True  # 标记为任务组工具
)
```

**工具描述符标记**：
在工具描述符JSON文件中添加 `is_task_group_tool` 字段：

```json
{
  "tool_id": "T16",
  "name": "TodoWrite",
  "category": "Task",
  "is_task_group_tool": true,
  "parameters": {...}
}
```

**典型任务组工具**：
- **TodoWrite**：创建和管理任务列表
- **TaskManager**：任务编排和调度
- **WorkflowBuilder**：工作流构建器
  
### 3.2 ToolDescriptionGenerator（工具描述生成器）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| generate_description(tool) | 生成工具描述 | tool: Tool | str |
| generate_parameters_schema(tool) | 生成参数Schema | tool: Tool | Dict |
| format_for_llm(tools) | 格式化为LLM可用格式 | tools: List[Tool] | List[Dict] |

### 3.3 ToolCapabilityEvaluator（工具能力评估器）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| evaluate_capability(tool, task_description) | 评估工具能力 | tool: Tool, task_description: str | float |
| rank_tools(task_description, top_n=5) | 按能力排序工具 | task_description: str, top_n: int | List[Tool] |
| categorize_tool(tool) | 分类工具 | tool: Tool | str |

### 3.4 SkillIntegration（技能集成）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| integrate_skill(skill) | 将技能作为工具集成 | skill: Skill | Tool |
| update_skill_tool(skill_id, skill) | 更新技能工具 | skill_id: str, skill: Skill | Tool |
| remove_skill_tool(skill_id) | 移除技能工具 | skill_id: str | bool |
| list_skill_tools() | 列出技能工具 | 无 | List[Tool] |

### 3.5 AutoRegistration（自动注册）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| configure_auto_registration(config) | 配置自动注册 | config: AutoRegistrationConfig | bool |
| get_auto_registration_config() | 获取自动注册配置 | 无 | AutoRegistrationConfig |
| start_auto_registration() | 启动自动注册服务 | 无 | bool |
| stop_auto_registration() | 停止自动注册服务 | 无 | bool |
| scan_and_register_tools() | 扫描并注册工具 | 无 | List[Tool] |
| auto_register_skills() | 自动注册技能 | 无 | List[Tool] |
| handle_new_skill_event(event) | 处理新技能事件 | event: Event | bool |
| handle_new_tool_event(event) | 处理新工具事件 | event: Event | bool |

---

## 4. 与其他组件的关系

### 4.1 依赖关系

| 组件 | 关系类型 | 说明 |
|-----|---------|------|
| L1b 持久化服务 | 依赖 | 存储工具信息 |
| L2g 技能管理服务 | 依赖 | 获取技能信息 |

### 4.2 被调用关系

| 组件 | 调用方式 | 说明 |
|-----|---------|------|
| L2e 请求构造服务 | 读取 | 获取工具描述（工具描述和技能描述统一由L2e获取后传递给L2d） |
| L2c 工具执行服务 | 读取 | 获取工具配置和实现，判断工具类型（native/skill），调度到对应执行路径 |
| L3a 通用任务协调服务 | 读写 | 管理工具 |

### 4.3 协作流程示例

**工具调用流程：**
```
L2e获取工具描述             L2f                    L2g
        |                    |                      |
        |--- get_tools ----->|                      |
        |                    |                      |
        |                    |--- get_skills -------->|
        |                    |                      |
        |                    |<--- skills ------------|
        |                    |                      |
        |                    |--- integrate_skills --|
        |                    |                      |
        |                    |--- format_for_llm ---->|
        |                    |                      |
        |<--- tools ----------|                      |
```

---

## 5. 工具与技能的统一

### 5.1 集成策略
技能被封装为工具格式，具有统一的：
- 工具ID
- 描述格式
- 参数Schema
- 调用接口

### 5.2 执行路径
```
LLM调用工具                   L2c                    L2f                    L2g
        |                    |                      |                      |
        |--- execute_tool -->|                      |                      |
        |                    |                      |                      |
        |                    |--- get_tool -------->|                      |
        |                    |                      |                      |
        |                    |<--- tool -------------|                      |
        |                    |                      |                      |
        |                    |--- 判断类型 --------->|                      |
        |                    |                      |                      |
        |                    |--- native工具 ------->|                      |
        |                    |                      |                      |
        |                    |--- skill工具 -------->|                      |
        |                    |                      |                      |
        |<--- result ---------|                      |                      |
```

---

## 6. 容错与恢复

### 6.1 错误处理
- 处理工具不存在
- 处理技能集成失败
- 返回有意义的错误信息

### 6.2 默认策略
- 使用默认工具列表
- 跳过不可用的工具