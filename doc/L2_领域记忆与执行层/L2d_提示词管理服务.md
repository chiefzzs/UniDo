# L2d 提示词管理服务

## 1. 组件概念

**L2d 提示词管理服务** 是 L2 领域层的核心组件，负责管理各种公共提示词模板，支持版本控制、变量替换和模板复用。

### 1.1 核心职责
- 提示词模板的 CRUD 操作
- 提示词版本管理
- 提示词模板变量替换
- 通过 L1b 持久化到 `prompts.json`
- 为 ModelConfig 提供提示词关联

### 1.2 设计理念
- **模板化**：将提示词作为模板，支持变量替换
- **版本控制**：支持提示词版本管理，便于追溯和回滚
- **复用性**：多个 ModelConfig 可关联同一提示词
- **分类管理**：支持按类别组织提示词

---

## 2. 数据类定义

### 2.1 Prompt（提示词模板）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| prompt_id | str | 提示词ID | 提示词唯一标识 | 服务自动生成 |
| name | str | 提示词名称 | 前端显示用 | 用户提供 |
| category | str | 类别 | 提示词分类（customer_service/coding/analysis等） | 用户设置 |
| content | str | 提示词内容 | 提示词模板正文 | 用户提供 |
| version | str | 版本号 | 语义化版本（x.y.z） | 服务自动管理 |
| variables | List[str] | 变量列表 | 提示词中支持的变量 | 服务解析 |
| is_active | bool | 是否激活 | 是否启用此提示词 | 用户设置 |
| created_at | str | 创建时间 | 创建时间 | 服务自动生成 |
| updated_at | str | 更新时间 | 最后更新时间 | 服务自动更新 |

### 2.2 PromptVersion（提示词版本）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| version_id | str | 版本ID | 版本唯一标识 | 服务自动生成 |
| prompt_id | str | 提示词ID | 关联的提示词 | 服务设置 |
| version | str | 版本号 | 版本标识 | 服务自动生成 |
| content | str | 版本内容 | 该版本的提示词内容 | 用户提供 |
| change_description | str | 变更描述 | 版本变更说明 | 用户提供 |
| created_at | str | 创建时间 | 版本创建时间 | 服务自动生成 |
| created_by | str | 创建者 | 版本创建者 | 服务自动生成 |

### 2.3 PromptVariable（提示词变量）

| 字段名 | 类型 | 含义描述 | 职责说明 | 创建者 |
|-------|------|---------|---------|-------|
| name | str | 变量名 | 变量标识符 | 解析得出 |
| default_value | Optional[str] | 默认值 | 变量的默认值 | 用户设置 |
| description | str | 变量描述 | 变量的用途说明 | 用户设置 |
| required | bool | 是否必需 | 变量是否必须提供 | 用户设置 |

---

## 3. 支持的场景

### 3.1 直接支持的场景

| 场景编号 | 场景名称 | 场景描述 |
|---------|---------|---------|
| SC027 | 创建提示词 | 创建新的提示词模板 |
| SC028 | 编辑提示词 | 修改提示词内容 |
| SC029 | 删除提示词 | 软删除提示词 |
| SC030 | 查看提示词列表 | 列出所有提示词 |
| SC031 | 预览提示词 | 预览变量替换后的提示词 |
| SC032 | 管理提示词版本 | 查看历史版本和回滚 |

### 3.2 作为下层组件支持的场景

- L2d LLM执行服务：通过 prompt_id 获取提示词内容
- L1a 配置管理：ModelConfig 关联 prompt_id
- L3 层场景服务：使用提示词模板

---

## 4. 数据流与控制流

### 4.1 提示词创建流程

```
用户                    L2d                    L1b                    L1d
|                       |                      |                      |
|--- create_prompt() --->|                      |                      |
|                       |                      |                      |
|                       |--- 解析变量 ---------->|                      |
|                       |                      |                      |
|                       |--- 保存提示词 -------->|                      |
|                       |                      |                      |
|                       |--- 发布事件 ---------->|                      |
|                       |                      |                      |
|<--- Prompt ----------|                      |                      |
```

### 4.2 提示词获取与变量替换流程

```
L2d LLM执行服务          L2d                    L1b
|                       |                      |
|--- get_prompt() ------>|                      |
|                       |                      |
|                       |--- 加载提示词 -------->|                      |
|                       |                      |                      |
|                       |<--- Prompt ----------- |                      |
|                       |                      |
|                       |--- 替换变量 ----------|
|                       |                      |
|<--- 替换后的内容 -------|                      |
```

### 4.3 提示词版本更新流程

```
用户                    L2d                    L1b
|                       |                      |
|--- update_prompt() --->|                      |
|                       |                      |
|                       |--- 保存新版本 -------->|                      |
|                       |                      |
|                       |--- 更新当前版本 ------|
|                       |                      |
|                       |--- 发布事件 ---------->|
|                       |                      |
|<--- Prompt(v2) --------|                      |
```

---

## 5. 如何使用下层组件

### 5.1 依赖的组件

| 组件 | 作用 | 使用方式 |
|-----|------|---------|
| L1b 持久化服务 | 提示词持久化 | save/get/list/delete 操作 |
| L1d 事件系统 | 发布提示词事件 | event_bus.publish() |

### 5.2 作为下层组件被使用

L2d 被上层组件以下列方式使用：

```python
# 1. 获取服务实例
from L2d_prompt_management import PromptManagementService

prompt_service = PromptManagementService()

# 2. 创建提示词
prompt = prompt_service.create_prompt(
    name="客服助手提示词",
    category="customer_service",
    content="你是一个专业的{{role}}助手，帮助用户解决{{problem_type}}问题。"
)

# 3. 获取提示词
prompt = prompt_service.get_prompt("prompt-123")

# 4. 替换变量获取内容
content = prompt_service.render_prompt(
    prompt_id="prompt-123",
    variables={"role": "售后", "problem_type": "退货"}
)

# 5. 更新提示词（自动创建新版本）
prompt_service.update_prompt(
    prompt_id="prompt-123",
    content="新内容..."
)

# 6. 获取历史版本
versions = prompt_service.get_versions("prompt-123")

# 7. 回滚到指定版本
prompt_service.rollback("prompt-123", "1.0")
```

---

## 6. 关键方法说明

### 6.1 PromptManagementService

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| create_prompt(name, category, content, **kwargs) | 创建提示词 | name, category, content | Prompt |
| get_prompt(prompt_id) | 获取提示词 | prompt_id: str | Optional[Prompt] |
| update_prompt(prompt_id, content, **kwargs) | 更新提示词 | prompt_id, content | Optional[Prompt] |
| delete_prompt(prompt_id) | 删除提示词 | prompt_id: str | bool |
| list_prompts(category, include_inactive) | 列出提示词 | category, include_inactive | List[Prompt] |
| render_prompt(prompt_id, variables) | 渲染提示词 | prompt_id, variables | str |
| get_versions(prompt_id) | 获取版本历史 | prompt_id: str | List[PromptVersion] |
| rollback(prompt_id, version) | 回滚版本 | prompt_id, version | bool |

### 6.2 变量替换规则

```python
# 变量格式：{{variable_name}}
# 示例：{{user_name}}, {{product_name}}

# 替换逻辑
def render_prompt(self, prompt_id: str, variables: Dict[str, str]) -> str:
    prompt = self.get_prompt(prompt_id)
    content = prompt.content

    for var_name, var_value in variables.items():
        content = content.replace(f"{{{{{var_name}}}}}", var_value)

    # 检查未替换的变量
    remaining = re.findall(r'\{\{(\w+)\}\}', content)
    if remaining:
        raise ValueError(f"未提供的变量: {remaining}")

    return content
```

---

## 7. 与其他L2组件的关系

### 7.1 与 L2d LLM执行服务

L2d LLM执行服务 通过 prompt_id 获取提示词：
- 执行LLM调用前获取提示词内容
- 将提示词作为 system_message 加入消息列表

### 7.2 与 L1a 配置管理

ModelConfig 通过 prompt_id 关联提示词：
- ModelConfig 不再包含 system_prompt 字段
- 执行时通过 prompt_id 动态获取提示词

### 7.3 与 L2a 领域实体管理

提示词可关联项目：
- 项目可指定默认提示词
- 支持项目级别的提示词定制

---

## 8. 事件发布

### 8.1 发布的事件类型

| 事件类型 | 触发时机 |
|---------|---------|
| prompt.created | 提示词创建成功 |
| prompt.updated | 提示词更新成功 |
| prompt.deleted | 提示词删除成功 |
| prompt.version_created | 新版本创建 |
| prompt.rollback | 版本回滚 |

### 8.2 事件载荷示例

```python
# prompt.created 事件载荷
{
    'prompt_id': 'prompt-123',
    'name': '客服助手提示词',
    'category': 'customer_service',
    'version': '1.0'
}

# prompt.updated 事件载荷
{
    'prompt_id': 'prompt-123',
    'old_version': '1.0',
    'new_version': '1.1'
}
```

---

## 9. 存储结构

### 9.1 prompts.json 结构

```json
{
  "prompts": [
    {
      "prompt_id": "prompt-123",
      "name": "客服助手提示词",
      "category": "customer_service",
      "content": "你是一个专业的{{role}}助手...",
      "version": "1.1",
      "variables": ["role", "problem_type"],
      "is_active": true,
      "created_at": "2026-05-18T10:00:00",
      "updated_at": "2026-05-18T11:00:00"
    }
  ]
}
```

### 9.2 prompt_versions.json 结构

```json
{
  "versions": [
    {
      "version_id": "ver-abc123",
      "prompt_id": "prompt-123",
      "version": "1.0",
      "content": "原始内容...",
      "change_description": "初始版本",
      "created_at": "2026-05-18T10:00:00",
      "created_by": "system"
    },
    {
      "version_id": "ver-def456",
      "prompt_id": "prompt-123",
      "version": "1.1",
      "content": "更新内容...",
      "change_description": "优化表述",
      "created_at": "2026-05-18T11:00:00",
      "created_by": "admin"
    }
  ]
}
```

---

## 10. 容错与恢复

### 10.1 数据完整性保障

- 创建提示词时验证变量格式
- 更新时保留历史版本
- 删除时采用软删除

### 10.2 错误处理

- 变量未提供时抛出明确错误
- 版本冲突时提示用户
- 持久化失败时回滚操作

### 10.3 恢复策略

- 支持版本回滚
- 保留指定数量的历史版本
- 软删除可恢复

---

## 附录：提示词分类示例

| 类别 | 说明 | 示例 |
|-----|------|-----|
| customer_service | 客服场景 | 售后咨询、售前解答 |
| coding | 编码场景 | 代码生成、代码审查 |
| analysis | 分析场景 | 数据分析、报告生成 |
| creative | 创意场景 | 写作、文案生成 |
| general | 通用场景 | 问答、闲聊 |
