# UI层目录结构（Vue 2.0 静态页面）

本文档汇总了所有迭代的UI组件，采用Vue 2.0框架，所有JS文件放置在 `static/js/` 目录。

## 整体目录结构

```
static/
├── js/                              # JavaScript文件目录
│   ├── vue.min.js                   # Vue 2.0 核心库
│   ├── vue-router.min.js            # Vue Router 3.x
│   ├── vuex.min.js                  # Vuex 3.x 状态管理
│   ├── axios.min.js                  # HTTP请求库
│   │
│   ├── components/                   # 通用UI组件库
│   │   ├── common/                  # 通用基础组件
│   │   │   ├── Button.vue
│   │   │   ├── Input.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Loading.vue
│   │   │   ├── Dropdown.vue
│   │   │   ├── Tabs.vue
│   │   │   ├── Tooltip.vue
│   │   │   ├── Alert.vue
│   │   │   └── Toast.vue
│   │   └── layout/                  # 布局组件
│   │       ├── Header.vue
│   │       ├── Sidebar.vue
│   │       ├── Footer.vue
│   │       ├── MainContent.vue
│   │       └── Panel.vue
│   │
│   ├── infrastructure/               # 基础设施层UI (迭代一、二)
│   │   ├── config/                  # 配置管理UI (S02)
│   │   │   ├── ConfigPanel.vue
│   │   │   ├── ConfigForm.vue
│   │   │   └── ConfigItem.vue
│   │   ├── events/                  # 事件总线UI (S03)
│   │   │   ├── EventLog.vue
│   │   │   └── EventItem.vue
│   │   ├── persistence/             # 数据持久化UI (S01)
│   │   │   └── DataViewer.vue
│   │   ├── recording/               # 录制回放UI (S04)
│   │   │   ├── RecordingPanel.vue
│   │   │   ├── ReplayControls.vue
│   │   │   └── RecordingList.vue
│   │   ├── tools/                   # 工具管理UI (S19/S20)
│   │   │   ├── ToolRegistry.vue
│   │   │   ├── ToolList.vue
│   │   │   └── ToolDetail.vue
│   │   └── llm/                     # LLM调用UI (S21)
│   │       ├── LLMInvokePanel.vue
│   │       ├── ModelInfo.vue
│   │       └── RequestBuilder.vue
│   │
│   ├── domain/                       # 领域层UI (迭代三、四)
│   │   ├── project/                 # 项目管理UI (S05)
│   │   │   ├── ProjectList.vue
│   │   │   ├── ProjectCard.vue
│   │   │   ├── ProjectDetail.vue
│   │   │   └── ProjectCreateModal.vue
│   │   ├── session/                 # 会话管理UI (S06)
│   │   │   ├── SessionList.vue
│   │   │   ├── SessionItem.vue
│   │   │   ├── SessionDetail.vue
│   │   │   └── MessageThread.vue
│   │   ├── task/                    # 任务执行UI (S08)
│   │   │   ├── TaskPlanView.vue
│   │   │   ├── TaskCard.vue
│   │   │   ├── TaskStatusBadge.vue
│   │   │   └── TaskDependencyGraph.vue
│   │   ├── intent/                 # 意图理解UI (S07)
│   │   │   ├── IntentPanel.vue
│   │   │   └── IntentResult.vue
│   │   └── llm/                    # LLM调用UI (S11)
│   │       ├── RequestPreview.vue
│   │       └── ResponseViewer.vue
│   │
│   ├── conversation/                 # 对话层UI (迭代五)
│   │   ├── main/                    # 主对话界面 (S10)
│   │   │   ├── ChatWindow.vue
│   │   │   ├── ChatInput.vue
│   │   │   ├── ChatHeader.vue
│   │   │   └── ChatMessages.vue
│   │   ├── task/                    # 任务组管理UI (S12/S13)
│   │   │   ├── TaskGroupPanel.vue
│   │   │   ├── TaskGroupCard.vue
│   │   │   ├── TaskItem.vue
│   │   │   └── TaskProgress.vue
│   │   ├── execution/              # 执行UI (S17)
│   │   │   ├── ExecutionStatus.vue
│   │   │   ├── ToolCallBadge.vue
│   │   │   └── ExecutionLog.vue
│   │   ├── inspection/             # 检查UI (S18)
│   │   │   ├── ValidationResult.vue
│   │   │   └── CheckRuleList.vue
│   │   └── stream/                 # 流式输出UI (S10)
│   │       ├── StreamText.vue
│   │       ├── ThinkBlock.vue
│   │       └── ToolResultBlock.vue
│   │
│   ├── gateway/                     # 网关层UI (迭代六)
│   │   ├── api/                    # API网关UI (S14)
│   │   │   ├── ApiConsole.vue
│   │   │   ├── EndpointList.vue
│   │   │   └── RequestResponse.vue
│   │   └── websocket/              # WebSocket UI (S15)
│   │       ├── ConnectionStatus.vue
│   │       ├── EventStream.vue
│   │       └── SubscriptionManager.vue
│   │
│   ├── integration/                 # UI整合 (迭代七)
│   │   ├── views/                  # 完整页面视图
│   │   │   ├── Dashboard.vue
│   │   │   ├── ProjectView.vue
│   │   │   ├── ConversationView.vue
│   │   │   ├── SettingsView.vue
│   │   │   └── WelcomeView.vue
│   │   ├── panels/                 # 可停靠面板
│   │   │   ├── ToolPanel.vue
│   │   │   ├── TerminalPanel.vue
│   │   │   └── DiagnosticsPanel.vue
│   │   └── dialogs/                # 对话框
│   │       ├── ProjectDialog.vue
│   │       ├── ConfigDialog.vue
│   │       └── ConfirmDialog.vue
│   │
│   ├── mixins/                      # Vue Mixins
│   │   ├── projectMixin.js
│   │   ├── sessionMixin.js
│   │   └── taskMixin.js
│   │
│   ├── store/                       # Vuex Store
│   │   ├── index.js                 # Store根模块
│   │   ├── project.js               # 项目状态模块
│   │   ├── session.js               # 会话状态模块
│   │   ├── task.js                 # 任务状态模块
│   │   ├── conversation.js          # 对话状态模块
│   │   ├── websocket.js             # WebSocket状态模块
│   │   └── theme.js                # 主题状态模块
│   │
│   ├── api.js                       # API调用封装 (axios)
│   ├── websocket.js                 # WebSocket封装
│   ├── router.js                    # Vue Router配置
│   ├── App.vue                      # 应用根组件
│   └── main.js                      # 应用入口文件
│
├── css/                             # 样式文件
│   ├── global.css                   # 全局样式
│   ├── variables.css                # CSS变量
│   ├── components/                  # 组件样式
│   │   ├── button.css
│   │   ├── modal.css
│   │   └── ...
│   └── themes/                      # 主题样式
│       ├── light.css                # 浅色主题
│       └── dark.css                 # 深色主题
│
└── index.html                        # HTML入口
```

## UI与后台服务对应关系

| UI目录 | UI组件 | 对应后台服务 | 服务层次 |
|--------|-------|-------------|---------|
| infrastructure/config | ConfigPanel, ConfigForm | S02 | 基础设施层 |
| infrastructure/events | EventLog | S03 | 基础设施层 |
| infrastructure/persistence | DataViewer | S01 | 基础设施层 |
| infrastructure/recording | RecordingPanel, ReplayControls | S04 | 基础设施层 |
| infrastructure/tools | ToolRegistry, ToolList | S19 | 基础设施层 |
| infrastructure/llm | LLMInvokePanel, RequestBuilder | S21 | 基础设施层 |
| domain/project | ProjectList, ProjectCard | S05 | 领域层 |
| domain/session | SessionList, MessageThread | S06 | 领域层 |
| domain/task | TaskPlanView, TaskCard | S08 | 领域层 |
| domain/intent | IntentPanel, IntentResult | S07 | 对话层 |
| domain/llm | RequestPreview, ResponseViewer | S11 | 领域层 |
| conversation/main | ChatWindow, ChatInput | S10 | 对话层 |
| conversation/task | TaskGroupPanel, TaskItem | S12/S13 | 对话层 |
| conversation/execution | ExecutionStatus, ToolCallBadge | S17 | 对话层 |
| conversation/inspection | ValidationResult | S18 | 对话层 |
| conversation/stream | StreamText, ThinkBlock | S10 | 对话层 |
| gateway/api | ApiConsole | S14 | 网关层 |
| gateway/websocket | ConnectionStatus, EventStream | S15 | 网关层 |
| integration/views | Dashboard, ProjectView | S16 | UI层 |
| integration/panels | ToolPanel, TerminalPanel | S16 | UI层 |

## UI开发迭代顺序

| 迭代 | 后台服务 | UI组件 | Vue组件 |
|------|---------|--------|---------|
| v0.1 | S01, S02, S03, S20 | 通用组件 + 配置面板 + 事件日志 + 数据查看器 | Button, Input, Modal, ConfigPanel, EventLog, DataViewer |
| v0.2 | S04, S19, S21 | 录制面板 + 工具列表 + LLM调用面板 | RecordingPanel, ToolList, LLMInvokePanel |
| v0.3 | S05, S06 | 项目列表 + 会话列表 + 消息线程 | ProjectList, SessionList, MessageThread |
| v0.4 | S08, S09, S11, S07 | 任务计划视图 + 意图面板 + LLM预览 | TaskPlanView, IntentPanel, ResponseViewer |
| v0.5 | S10, S12, S13, S17, S18 | 主对话窗口 + 任务组面板 + 流式输出 | ChatWindow, TaskGroupPanel, StreamText |
| v0.6 | S14, S15 | API控制台 + WebSocket状态 + Store整合 | ApiConsole, EventStream, Vuex Store |
| v0.7 | S16 | 完整应用视图 + 主题支持 + E2E测试 | Dashboard, ConversationView, Theme |

## Vuex Store 模块设计

```javascript
// store/index.js
import Vue from 'vue'
import Vuex from 'vuex'
import project from './project'
import session from './session'
import task from './task'
import conversation from './conversation'
import websocket from './websocket'
import theme from './theme'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    project,
    session,
    task,
    conversation,
    websocket,
    theme
  }
})

// store/websocket.js 示例
export default {
  namespaced: true,
  state: {
    connected: false,
    events: [],
    subscriptions: []
  },
  mutations: {
    SET_CONNECTED(state, connected) {
      state.connected = connected
    },
    ADD_EVENT(state, event) {
      state.events.push(event)
    },
    CLEAR_EVENTS(state) {
      state.events = []
    }
  },
  actions: {
    connect({ commit }) { /* WebSocket连接逻辑 */ },
    disconnect({ commit }) { /* 断开连接 */ },
    subscribe({ commit }, eventType) { /* 订阅事件 */ }
  }
}
```
