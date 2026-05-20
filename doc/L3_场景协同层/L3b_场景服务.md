# L3b 验证用例场景

## 概述

**L3b 是文档中用于说明验证用例的场景集合，代码中不应存在。**

这些场景用于验证系统功能的正确性，是在设计和开发阶段用来理解和验证系统行为的用例。

---

## 验证用例列表

| 场景编号 | 场景名称 | 验证目的 | 对应L3a服务 |
|---------|---------|---------|------------|
| SC04 | 简单单次文本对话 | 验证基础对话能力 | DialogueService |
| SC05 | 简单单次工具对话 | 验证工具调用能力 | TaskExecutionService |
| SC16 | 任务组对话 | 验证任务组协调能力 | TaskGroupExecutionService |
| SC17 | 嵌套任务组对话 | 验证递归任务协调能力 | TaskGroupExecutionService（递归） |

---

## 场景说明

### SC04 简单单次文本对话

**验证目标**：验证系统能够处理简单的单轮文本对话，不需要工具调用。

**验证步骤**：
1. 用户输入简单文本问题
2. 系统调用DialogueService
3. DialogueService调用TaskGroupExecutionService（无任务）
4. 返回文本响应

**预期结果**：系统返回符合语境的文本回答。

---

### SC05 简单单次工具对话

**验证目标**：验证系统能够识别需要工具调用的场景，并正确执行工具。

**验证步骤**：
1. 用户输入需要工具的问题（如"搜索天气"）
2. 系统调用DialogueService
3. DialogueService调用TaskGroupExecutionService
4. TaskGroupExecutionService调用TaskExecutionService
5. TaskExecutionService调用L2c执行工具
6. 返回工具执行结果

**预期结果**：系统识别工具调用需求，执行工具并返回结果。

---

### SC16 任务组对话

**验证目标**：验证系统能够处理包含多个任务的任务组场景。

**验证步骤**：
1. 用户输入复杂任务（拆分为多个子任务）
2. 系统调用DialogueService
3. DialogueService调用TaskGroupExecutionService
4. TaskGroupExecutionService依次执行各任务
5. TaskExecutionService调用L2c执行各工具
6. 返回任务组执行结果

**预期结果**：系统按顺序执行各任务，返回完整的任务组结果。

---

### SC17 嵌套任务组对话

**验证目标**：验证系统能够处理嵌套的任务组（任务组中包含子任务组）。

**验证步骤**：
1. 用户输入非常复杂的任务（嵌套的任务结构）
2. 系统调用DialogueService
3. DialogueService调用TaskGroupExecutionService
4. TaskGroupExecutionService发现子任务组，递归调用自己
5. 递归执行直到所有叶子任务完成
6. 返回嵌套任务组的完整执行结果

**预期结果**：系统正确处理嵌套任务组，递归执行所有层级。

---

## 代码实现说明

**重要**：上述验证用例仅用于文档说明和设计验证，实际代码中不应存在L3b组件。

**正确实现方式**：
- 验证用例在设计阶段用于理解系统行为
- 实际代码只需实现L3a的5个服务
- DialogueService会调用相应的服务组合完成用户请求

**示例**：

```python
# 错误：代码中不应该有SceneService或具体场景处理
class SceneService:
    def handle_free_chat(self, ...):
        ...

# 正确：代码中只需要DialogueService
class DialogueService:
    def chat(self, session_id, user_input, context):
        # 根据用户输入自动判断需要调用的服务
        ...
```

---

## L3a服务与验证用例的对应关系

```
SC04（简单文本对话）→ DialogueService
                        ↓
                   （无需TaskExecution）

SC05（简单工具对话）→ DialogueService → TaskExecutionService → L2c
                                              ↓
                                           （单个任务）

SC16（任务组对话）→ DialogueService → TaskGroupExecutionService
                                              ↓
                              TaskExecutionService → L2c
                                              ↓
                                         （多个任务）

SC17（嵌套任务组）→ DialogueService → TaskGroupExecutionService（递归）
                                              ↓
                              TaskGroupExecutionService（嵌套层）
                                              ↓
                              TaskExecutionService → L2c
```
