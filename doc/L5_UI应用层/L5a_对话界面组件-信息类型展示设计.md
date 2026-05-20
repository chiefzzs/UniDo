# L5a 对话界面组件 - 信息类型展示设计

---

## 1. 设计背景

### 1.1 问题描述

当前对话界面存在内容不分类型显示的问题：所有信息都统一展示在文本区域中，用户无法清晰区分文本回复、工具调用、思考过程、代码块等不同类型的内容。

**现有问题示例**：
```html
<div class="response-block-content">
    <!-- ThinkBlock - 未显示 -->
    <div class="think-block" style="display:none;"></div>
    <!-- TextBlock - 所有内容都在这里 -->
    <div class="text-block">
        <p>根据工具执行结果，我来总结一下：</p>
        <p>任务完成情况：✅ 成功</p>
        ...
    </div>
    <!-- ToolCallBlocks - 为空 -->
    <div class="tool-calls-container"></div>
</div>
```

### 1.2 设计目标

- **类型分离**：将不同类型的信息分开展示
- **视觉区分**：通过样式差异清晰区分内容类型
- **交互优化**：为不同类型提供针对性的交互体验
- **扩展性**：支持未来新增信息类型

---

## 2. 信息类型分类

### 2.1 类型定义

| 类型编号 | 类型名称 | 描述 | 数据来源 | 展示位置 |
|---------|---------|------|---------|---------|
| T01 | 文本消息 (Text) | LLM生成的自然语言回复 | `response.content` | TextBlock |
| T02 | 思考过程 (Think) | LLM的内部思考/推理过程 | `response.thought` | ThinkBlock |
| T03 | 工具调用 (ToolCall) | 工具调用信息（名称、参数） | `response.tool_calls[]` | ToolCallBlock |
| T04 | 工具输出 (ToolOutput) | 工具执行的实时输出 | `tool.execution_output` | ToolOutputBlock |
| T05 | 工具结果 (ToolResult) | 工具执行的最终结果 | `tool.call_completed` | ToolResultBlock |
| T06 | 代码块 (Code) | 代码片段（支持语法高亮） | `response.content` (含代码标记) | CodeBlock |
| T07 | 表格 (Table) | 结构化数据表格 | `response.content` (含表格标记) | TableBlock |
| T08 | 链接卡片 (LinkCard) | 网页链接预览 | `response.content` (含链接) | LinkCardBlock |
| T09 | 错误提示 (Error) | 错误信息展示 | `response.error` | ErrorBlock |
| T10 | 状态提示 (Status) | 操作状态提示 | 事件总线 | StatusBar |

### 2.2 类型识别规则

| 类型 | 识别方式 | 示例 |
|-----|---------|------|
| 文本消息 | 默认类型，无特殊标记 | 普通自然语言文本 |
| 思考过程 | `response.thought` 字段存在 | `"thought": "我需要分析用户意图..."` |
| 工具调用 | `response.data.tool_calls` 数组非空 | `[{"tool_name": "RunCommand", ...}]` |
| 代码块 | 内容包含 ``` 标记 | ```python\nprint("hello")\n``` |
| 表格 | 内容包含 Markdown 表格语法 | `\| 列1 \| 列2 \|` |
| 链接卡片 | 内容包含 URL | `[链接文本](https://example.com)` |
| 错误提示 | `response.status` 为 error | `{"status": "error", "error": "..."}` |

---

## 3. 组件结构设计

### 3.1 组件层级架构

```
AssistantResponseBlock (容器组件)
    │
    ├─► ThinkBlock (思考过程)
    │       └─► 折叠/展开按钮
    │
    ├─► TextBlock (文本回复)
    │       ├─► 普通文本段落
    │       ├─► 内嵌代码片段
    │       └─► 链接（转为可点击）
    │
    ├─► CodeBlock (代码块)
    │       ├─► 语法高亮
    │       ├─► 语言标识
    │       └─► 复制按钮
    │
    ├─► TableBlock (表格)
    │       └─► 响应式表格展示
    │
    ├─► ToolCallBlock (工具调用)
    │       ├─► 工具图标
    │       ├─► 工具名称
    │       └─► 参数展示
    │
    ├─► ToolOutputBlock (工具输出)
    │       ├─► 实时输出区域
    │       └─► 滚动控制
    │
    └─► ToolResultBlock (工具结果)
            ├─► 状态图标（成功/失败）
            └─► 结果摘要
```

### 3.2 组件职责说明

| 组件 | 职责 | 数据属性 |
|-----|------|---------|
| `AssistantResponseBlock` | 容器组件，管理整体布局和状态 | `responseId`, `status` |
| `ThinkBlock` | 展示思考过程，支持折叠 | `thought`, `expanded` |
| `TextBlock` | 展示纯文本内容 | `content` |
| `CodeBlock` | 展示代码片段，支持语法高亮 | `code`, `language`, `filename` |
| `TableBlock` | 展示表格数据 | `headers`, `rows` |
| `ToolCallBlock` | 展示工具调用信息 | `toolName`, `arguments`, `callId` |
| `ToolOutputBlock` | 展示工具实时输出 | `output`, `isStreaming` |
| `ToolResultBlock` | 展示工具执行结果 | `success`, `result`, `error` |

---

## 4. 数据结构设计

### 4.1 后端响应数据结构

```json
{
    "type": "message_response",
    "status": "success",
    "session_id": "session-xxx",
    "data": {
        "content": "根据工具执行结果，我来总结一下：\n\n**任务完成情况：** ✅ 成功",
        "type": "text",
        "thought": "用户需要创建目录，我应该调用RunCommand工具执行mkdir命令...",
        "tool_calls": [
            {
                "tool_name": "RunCommand",
                "arguments": "{\"command\": \"mkdir test_10\", \"workspace\": \"D:\\learnning\\260521\\workspace\"}",
                "call_id": "call-abc123",
                "status": "completed",
                "result": "命令执行成功",
                "error": null,
                "output": "mkdir: created directory 'test_10'"
            }
        ],
        "code_blocks": [
            {
                "code": "def hello():\n    print('Hello World')",
                "language": "python",
                "filename": "hello.py"
            }
        ],
        "tables": [],
        "links": []
    }
}
```

### 4.2 前端解析数据结构

```typescript
interface MessageData {
    content: string;
    type: 'text' | 'tool' | 'code' | 'error';
    thought?: string;
    tool_calls?: ToolCall[];
    code_blocks?: CodeBlock[];
    tables?: TableData[];
    links?: LinkData[];
}

interface ToolCall {
    tool_name: string;
    arguments: string | object;
    call_id: string;
    status: 'completed' | 'failed' | 'executing';
    result?: string;
    error?: string;
    output?: string;
}

interface CodeBlock {
    code: string;
    language: string;
    filename?: string;
}

interface TableData {
    headers: string[];
    rows: string[][];
}

interface LinkData {
    text: string;
    url: string;
    title?: string;
}
```

---

## 5. 展示设计规范

### 5.1 文本消息 (TextBlock)

**样式规范**：
- 使用标准字体（14px/16px）
- 行高 1.6-1.8
- 段落间距 12px
- 文字颜色：主文本 #333，辅助文本 #666

**交互规范**：
- 链接自动识别并转为可点击
- 支持 Markdown 格式渲染（粗体、斜体、列表等）

**HTML结构**：
```html
<div class="text-block">
    <p class="text-paragraph">根据工具执行结果，我来总结一下：</p>
    <p class="text-paragraph">
        <strong>任务完成情况：</strong> ✅ 成功
    </p>
    <ul class="text-list">
        <li>项目已创建</li>
        <li>配置已更新</li>
    </ul>
</div>
```

### 5.2 思考过程 (ThinkBlock)

**样式规范**：
- 背景色：浅色背景（#f8f9fa）
- 边框：虚线边框（#e9ecef）
- 图标：🧠 思考图标
- 可折叠设计

**交互规范**：
- 默认折叠状态（可配置）
- 点击展开/折叠
- 支持复制思考内容

**HTML结构**：
```html
<div class="think-block" id="think-msg-xxx">
    <button class="think-toggle" onclick="toggleThink(this)">
        <span class="think-icon">🧠</span>
        <span class="think-label">思考过程</span>
        <span class="think-arrow">▼</span>
    </button>
    <div class="think-content" style="display: none;">
        <p>用户需要创建目录，我应该调用RunCommand工具执行mkdir命令...</p>
        <button class="think-copy" onclick="copyContent(this)">复制</button>
    </div>
</div>
```

### 5.3 代码块 (CodeBlock)

**样式规范**：
- 背景色：深色背景（#1e1e1e）
- 字体：等宽字体（Consolas, Monaco, monospace）
- 语法高亮：支持多种语言
- 圆角：8px
- 边框：1px solid #333

**交互规范**：
- 点击复制按钮复制代码
- 支持行号显示（可选）
- 支持语言选择/切换

**HTML结构**：
```html
<div class="code-block">
    <div class="code-header">
        <span class="code-language">Python</span>
        <span class="code-filename">hello.py</span>
        <button class="code-copy" onclick="copyCode(this)">
            <svg class="copy-icon">...</svg>
        </button>
    </div>
    <pre class="code-content"><code class="language-python">def hello():
    print('Hello World')</code></pre>
</div>
```

### 5.4 工具调用 (ToolCallBlock)

**样式规范**：
- 背景色：白色背景
- 边框：1px solid #e5e7eb（灰色边框）
- 图标：🔧 工具图标
- 分隔线：浅灰色虚线

**交互规范**：
- 参数可展开/折叠
- 显示工具执行状态
- 支持点击查看详情

**HTML结构**：
```html
<div class="tool-call-block" id="tool-call-xxx">
    <div class="tool-header">
        <span class="tool-icon">🔧</span>
        <span class="tool-name">RunCommand</span>
        <span class="tool-status completed">✓ 已完成</span>
    </div>
    <div class="tool-arguments">
        <div class="arg-label">参数：</div>
        <pre class="arg-value">{"command": "mkdir test_10", "workspace": "..."}</pre>
    </div>
</div>
```

### 5.5 工具输出 (ToolOutputBlock)

**样式规范**：
- 背景色：黑色背景（#0d1117）
- 字体：等宽字体，浅色文字（#c9d1d9）
- 边框：1px solid #30363d
- 最大高度：300px（自动滚动）

**交互规范**：
- 实时追加输出内容
- 自动滚动到底部
- 支持暂停/继续输出

**HTML结构**：
```html
<div class="tool-output-block">
    <div class="output-header">
        <span class="output-label">工具输出</span>
        <button class="output-scroll-lock" onclick="toggleScrollLock(this)">
            <svg>...</svg>
        </button>
    </div>
    <div class="output-content" id="output-xxx">
        <span class="output-line">mkdir: created directory 'test_10'</span>
    </div>
</div>
```

### 5.6 工具结果 (ToolResultBlock)

**样式规范**：
- 成功状态：绿色边框，绿色图标
- 失败状态：红色边框，红色图标
- 背景色：对应状态的浅色背景

**交互规范**：
- 显示结果摘要
- 失败时显示错误详情
- 支持点击展开完整结果

**HTML结构**：
```html
<div class="tool-result-block success">
    <div class="result-icon">✅</div>
    <div class="result-content">
        <div class="result-title">工具执行成功</div>
        <div class="result-summary">目录 test_10 已成功创建</div>
        <button class="result-details" onclick="toggleDetails(this)">查看详情</button>
    </div>
</div>
```

### 5.7 链接卡片 (LinkCard)

**样式规范**：
- 背景色：白色背景
- 边框：1px solid #e5e7eb
- 圆角：8px
- 悬停效果：阴影加深

**交互规范**：
- 点击跳转到链接
- 显示链接预览（标题、描述、图标）

**HTML结构**：
```html
<div class="link-card" onclick="openLink(this)">
    <div class="link-favicon">
        <img src="https://example.com/favicon.ico" alt="Favicon">
    </div>
    <div class="link-info">
        <div class="link-title">Example Website</div>
        <div class="link-url">https://example.com</div>
        <div class="link-description">这是一个示例网站</div>
    </div>
    <div class="link-arrow">→</div>
</div>
```

---

## 6. 类型解析与渲染流程

### 6.1 解析流程

```
后端响应数据
    │
    ▼
解析 response.data
    │
    ├─► 检查 thought 字段
    │       │
    │       └─► 存在 → 创建 ThinkBlock
    │
    ├─► 解析 content 字段
    │       │
    │       ├─► 检测代码块标记 → 创建 CodeBlock
    │       ├─► 检测表格标记 → 创建 TableBlock
    │       ├─► 检测链接 → 创建 LinkCard
    │       │
    │       └─► 剩余文本 → 创建 TextBlock
    │
    ├─► 检查 tool_calls 数组
    │       │
    │       └─► 非空 → 遍历创建 ToolCallBlock + ToolOutputBlock + ToolResultBlock
    │
    └─► 检查 status 字段
            │
            └─► error → 创建 ErrorBlock
```

### 6.2 渲染流程图

```
renderResponse(response) {
    1. 创建 AssistantResponseBlock 容器
    2. 解析数据类型
    3. 按顺序创建子组件：
       ├─► ThinkBlock（如果有思考内容）
       ├─► TextBlock（文本内容）
       ├─► CodeBlock（代码块）
       ├─► TableBlock（表格）
       ├─► LinkCard（链接）
       ├─► ToolCallBlock（工具调用信息）
       ├─► ToolOutputBlock（工具输出）
       └─► ToolResultBlock（工具结果）
    4. 将子组件挂载到容器
    5. 渲染到DOM
}
```

---

## 7. 事件驱动更新机制

### 7.1 事件与组件映射

| 事件类型 | 目标组件 | 更新动作 |
|---------|---------|---------|
| `llm.stream_chunk` | TextBlock | 追加文本内容 |
| `tool.call_started` | ToolCallBlock | 创建工具调用卡片 |
| `tool.execution_output` | ToolOutputBlock | 追加输出内容 |
| `tool.execution_output_end` | ToolOutputBlock | 标记输出完成 |
| `tool.call_completed` | ToolResultBlock | 更新工具结果状态 |
| `message.updated` | 各组件 | 更新内容 |

### 7.2 实时输出处理流程

```
工具执行开始
        │
        ▼
收到 tool.call_started 事件
        │
        ├─► 创建 ToolCallBlock（显示工具名称和参数）
        │
        └─► 创建 ToolOutputBlock（准备接收输出）
                │
                ▼
收到 tool.execution_output 事件（多次）
                │
                ├─► 追加输出内容到 ToolOutputBlock
                │
                └─► 自动滚动到底部
                        │
                        ▼
收到 tool.call_completed 事件
                │
                ├─► 创建 ToolResultBlock（显示成功/失败）
                │
                └─► 更新 ToolCallBlock 状态
```

---

## 8. 样式设计规范

### 8.1 颜色方案

| 元素 | 颜色值 | 说明 |
|-----|-------|------|
| 主文本 | #1f2937 | 深色文本 |
| 辅助文本 | #6b7280 | 浅色文本 |
| 成功状态 | #10b981 | 绿色 |
| 失败状态 | #ef4444 | 红色 |
| 警告状态 | #f59e0b | 橙色 |
| 代码背景 | #1e1e1e | 深色背景 |
| 工具卡片边框 | #e5e7eb | 灰色边框 |
| 思考块背景 | #f8f9fa | 浅色背景 |

### 8.2 间距规范

| 元素 | 间距值 | 说明 |
|-----|-------|------|
| 组件间距 | 16px | 子组件之间的垂直间距 |
| 内边距 | 12px/16px | 组件内部padding |
| 圆角 | 8px | 卡片类组件圆角 |
| 行高 | 1.6-1.8 | 文本行高 |

### 8.3 字体规范

| 元素 | 字体 | 字号 |
|-----|------|-----|
| 正文 | 系统无衬线 | 14px |
| 代码 | Consolas/Monaco | 13px |
| 标题 | 系统无衬线 | 16px |
| 辅助文字 | 系统无衬线 | 12px |

---

## 9. 扩展性设计

### 9.1 新增信息类型流程

```
1. 定义新类型标识（如 T11: Chart）
2. 添加类型识别规则
3. 创建对应的 Block 组件
4. 更新解析器逻辑
5. 添加样式定义
6. 更新文档
```

### 9.2 组件注册机制

```typescript
// 组件注册中心
const componentRegistry = {
    'text': TextBlock,
    'thought': ThinkBlock,
    'code': CodeBlock,
    'table': TableBlock,
    'tool_call': ToolCallBlock,
    'tool_output': ToolOutputBlock,
    'tool_result': ToolResultBlock,
    'link': LinkCard,
    'error': ErrorBlock
};

// 动态注册新组件
function registerComponent(type, component) {
    componentRegistry[type] = component;
}

// 使用注册中心渲染
function renderByType(type, data) {
    const Component = componentRegistry[type];
    if (Component) {
        return new Component(data);
    }
    // 回退到文本展示
    return new TextBlock({ content: JSON.stringify(data) });
}
```

---

## 10. 兼容性考虑

### 10.1 降级方案

| 场景 | 降级策略 |
|-----|---------|
| 浏览器不支持 WebSocket | 降级为轮询方式 |
| JavaScript 禁用 | 显示静态内容 |
| 深色模式不支持 | 使用浅色模式 |
| 语法高亮失败 | 显示纯文本代码 |

### 10.2 响应式设计

- **桌面端**：完整功能展示
- **平板端**：简化布局，隐藏侧边栏
- **移动端**：单列布局，折叠非核心内容

---

## 附录：组件协作关系图

```
┌─────────────────────────────────────────────────────────────────┐
│              AssistantResponseBlock                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  ThinkBlock          │  可折叠思考过程展示             │  │
│  ├──────────────────────┼─────────────────────────────────┤  │
│  │  TextBlock           │  文本消息展示                   │  │
│  ├──────────────────────┼─────────────────────────────────┤  │
│  │  CodeBlock           │  代码块展示（语法高亮）         │  │
│  ├──────────────────────┼─────────────────────────────────┤  │
│  │  TableBlock          │  表格数据展示                   │  │
│  ├──────────────────────┼─────────────────────────────────┤  │
│  │  ToolCallBlock       │  工具调用信息                   │  │
│  ├──────────────────────┼─────────────────────────────────┤  │
│  │  ToolOutputBlock     │  工具实时输出                   │  │
│  ├──────────────────────┼─────────────────────────────────┤  │
│  │  ToolResultBlock     │  工具执行结果                   │  │
│  └──────────────────────┴─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

**文档版本**: v1.0  
**创建日期**: 2026-05-20  
**适用项目**: Trae AI Assistant  
**作者**: Trae AI Team