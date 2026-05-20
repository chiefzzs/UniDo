# L2g 技能管理服务

## 1. 服务定位

**L2g 技能管理服务** 是 L2 领域记忆与执行层的核心组件之一，负责管理技能的定义、组合和调用链编排，并将技能封装为工具格式供其他组件使用。

### 1.1 核心职责
- **技能定义**：定义技能（组合多个工具调用）
- **技能组合**：组合多个技能形成复杂能力
- **技能调用链编排**：编排技能执行顺序
- **技能工具化**：将技能封装为工具格式，供L2f集成

### 1.2 设计原则
- **可组合性**：技能可以组合形成更复杂的技能
- **可复用性**：技能可以在不同场景中复用
- **可扩展性**：支持动态添加新技能

---

## 2. 数据结构定义

### 2.1 Skill（技能）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| skill_id | str | 技能唯一标识 | 非空，唯一 |
| name | str | 技能名称 | 非空 |
| description | str | 技能描述 | 非空 |
| steps | List[SkillStep] | 技能步骤列表 | 非空 |
| parameters | Dict | 参数JSON Schema | 非空 |
| return_type | str | 返回类型 | 非空 |
| enabled | bool | 是否启用 | 默认true |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.2 SkillStep（技能步骤）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|-------|
| step_id | str | 步骤唯一标识 | 非空，唯一 |
| type | str | 步骤类型（tool/skill/condition/loop） | 非空 |
| tool_id | str | 工具ID（type=tool时） | 可选 |
| skill_id | str | 技能ID（type=skill时） | 可选 |
| parameters | Dict | 步骤参数 | 可选 |
| condition | str | 条件表达式（type=condition时） | 可选 |
| loop_count | int | 循环次数（type=loop时） | 可选 |
| next_step_id | str | 下一步骤ID | 可选 |
| on_success_step_id | str | 成功时下一步骤ID | 可选 |
| on_failure_step_id | str | 失败时下一步骤ID | 可选 |

### 2.3 SkillExecutionContext（技能执行上下文）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| execution_id | str | 执行唯一标识 | 非空，唯一 |
| skill_id | str | 关联的技能ID | 非空 |
| dialog_id | str | 关联的对话ID | 非空 |
| current_step_id | str | 当前步骤ID | 可选 |
| variables | Dict | 执行变量 | 可选 |
| status | str | 执行状态（running/completed/failed） | 默认running |
| created_at | datetime | 创建时间 | 自动生成 |
| updated_at | datetime | 更新时间 | 自动更新 |

### 2.4 持久化数据格式

L2g 使用 L1b 持久化服务进行数据存储，数据以 JSON 数组格式保存在 `src/data/{env_type}/{entity_type}.json` 文件中。

#### 2.4.1 Skill
- **存储位置**：`src/data/{env_type}/skill.json`
- **存储内容**：
```json
[
  {
    "skill_id": "skill-001",
    "name": "代码审查",
    "description": "对代码进行审查并提出改进建议",
    "steps": [
      {
        "step_id": "step-001",
        "type": "tool",
        "tool_id": "tool-read",
        "parameters": {"path": "${input.path}"},
        "next_step_id": "step-002"
      },
      {
        "step_id": "step-002",
        "type": "tool",
        "tool_id": "tool-llm",
        "parameters": {"prompt": "审查以下代码：${step-001.output}"},
        "next_step_id": null
      }
    ],
    "parameters": {
      "type": "object",
      "properties": {
        "path": {"type": "string", "description": "代码文件路径"}
      },
      "required": ["path"]
    },
    "return_type": "string",
    "enabled": true,
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:00:00"
  }
]
```

#### 2.4.2 SkillExecutionContext
- **存储位置**：`src/data/{env_type}/skill_execution_context.json`
- **存储内容**：
```json
[
  {
    "execution_id": "exec-001",
    "skill_id": "skill-001",
    "dialog_id": "dialog-001",
    "current_step_id": "step-002",
    "variables": {
      "path": "/workspace/code.py",
      "review_result": "代码结构良好..."
    },
    "status": "running",
    "created_at": "2026-05-18T10:00:00",
    "updated_at": "2026-05-18T10:05:00"
  }
]
```

#### 2.4.3 SkillStep
- **存储位置**：`src/data/{env_type}/skill_step.json`
- **存储内容**：
```json
[
  {
    "step_id": "step-001",
    "type": "tool",
    "tool_id": "tool-read",
    "skill_id": null,
    "parameters": {"path": "${input.path}"},
    "condition": null,
    "loop_count": null,
    "next_step_id": "step-002",
    "on_success_step_id": "step-002",
    "on_failure_step_id": null
  }
]
```

---

## 3. 关键方法定义

### 3.1 SkillDefinition（技能定义）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| define_skill(name, description, steps, parameters, return_type) | 定义技能 | name: str, description: str, steps: List[SkillStep], parameters: Dict, return_type: str | Skill |
| get_skill(skill_id) | 获取技能 | skill_id: str | Optional[Skill] |
| update_skill(skill_id, **kwargs) | 更新技能 | skill_id: str, 字段名=值 | Optional[Skill] |
| delete_skill(skill_id) | 删除技能 | skill_id: str | bool |
| list_skills(enabled=True) | 列出技能 | enabled: bool | List[Skill] |
| enable_skill(skill_id) | 启用技能 | skill_id: str | bool |
| disable_skill(skill_id) | 禁用技能 | skill_id: str | bool |

### 3.2 SkillComposition（技能组合）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| compose_skills(name, description, skill_ids, parameters, return_type) | 组合技能 | name: str, description: str, skill_ids: List[str], parameters: Dict, return_type: str | Skill |
| decompose_skill(skill_id) | 分解技能 | skill_id: str | List[Skill] |
| validate_composition(skill_ids) | 验证组合有效性 | skill_ids: List[str] | bool |

### 3.3 SkillOrchestration（技能编排）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_execution_context(skill_id, dialog_id, input_data) | 创建执行上下文 | skill_id: str, dialog_id: str, input_data: Dict | SkillExecutionContext |
| execute_step(execution_id) | 执行下一步骤 | execution_id: str | SkillExecutionContext |
| execute_skill(skill_id, dialog_id, input_data) | 执行技能 | skill_id: str, dialog_id: str, input_data: Dict | Dict |
| cancel_execution(execution_id) | 取消执行 | execution_id: str | bool |
| get_execution_status(execution_id) | 获取执行状态 | execution_id: str | SkillExecutionContext |

### 3.4 SkillToolWrapper（技能工具封装）

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| wrap_as_tool(skill) | 将技能封装为工具 | skill: Skill | Tool |
| unwrap_from_tool(tool) | 从工具中解封装技能 | tool: Tool | Skill |
| update_tool_wrapper(skill_id) | 更新工具封装 | skill_id: str | bool |

---

## 4. 与其他组件的关系

### 4.1 依赖关系

| 组件 | 关系类型 | 说明 |
|-----|---------|------|
| L1b 持久化服务 | 依赖 | 存储技能信息 |
| L2f 工具管理服务 | 依赖 | 获取工具能力 |
| L2c 工具执行服务 | 依赖 | 执行工具步骤 |

### 4.2 被调用关系

| 组件 | 调用方式 | 说明 |
|-----|---------|------|
| L2f 工具管理服务 | 读取 | 获取技能信息进行集成 |
| L3a 通用任务协调服务 | 读写 | 管理和执行技能 |

### 4.3 协作流程示例

**技能执行流程：**
```
L3层调用技能                 L2g                    L2f                    L2c                    L2b
        |                    |                      |                      |                      |
        |--- execute_skill -->|                      |                      |                      |
        |                    |                      |                      |                      |
        |                    |--- create_context -->|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- get_next_step ---->|                      |                      |
        |                    |                      |                      |                      |
        |                    |<--- step -------------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- execute_step ---->|                      |                      |
        |                    |                      |                      |                      |
        |                    |                      |--- execute_tool ---->|                      |
        |                    |                      |                      |                      |
        |                    |                      |<--- result ----------|                      |
        |                    |<--- result -----------|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- update_context --->|                      |                      |
        |                    |                      |                      |                      |
        |                    |--- check_complete ---->|                      |                      |
        |                    |                      |                      |                      |
        |<--- result ---------|                      |                      |                      |
```

---

## 5. 技能执行引擎

### 5.1 执行流程
1. 创建执行上下文
2. 解析技能步骤
3. 执行当前步骤
4. 更新上下文变量
5. 决定下一步骤
6. 重复直到完成

### 5.2 步骤类型
- **tool**：调用工具
- **skill**：调用子技能（递归）
- **condition**：条件分支
- **loop**：循环执行

### 5.3 错误处理
- 步骤失败时可配置重试策略
- 支持失败时跳转到指定步骤
- 支持整体失败回滚

---

## 6. 容错与恢复

### 6.1 错误处理
- 处理步骤执行失败
- 处理工具调用失败
- 提供重试机制

### 6.2 恢复策略
- 支持断点续执行
- 记录执行历史
- 支持失败重试