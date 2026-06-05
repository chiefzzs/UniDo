# 道一（UniDo）

基于 Python 的 AI 助手后端服务，提供工具管理、LLM 调用、对话管理等核心功能。

## 快速入门

### 5分钟快速上手

#### 步骤1：安装依赖

```powershell
# 进入项目目录
cd d:\learnning\260521

# 安装依赖
pip install -r requirements.txt
```

#### 步骤2：启动服务

```powershell
# 启动主服务
python run.py
```

服务启动后访问：http://localhost:8000

#### 步骤3：配置并开始使用

1. **配置模型**：工具菜单 → 模型管理 → 新建模型（配置您的 OpenAI API）
2. **配置工作区**：工具菜单 → 工作区管理 → 新建工作区（配置本地项目路径）
3. **创建项目**：工具菜单 → 项目管理 → 新建项目（关联模型和工作区）
4. **开始对话**：在主界面选择项目，开始与道一交流

详细操作请查看：[快速操作指南](doc/手册/快速操作指南.md)

---

## 文档目录

### 📖 使用手册

| 文档 | 说明 |
|------|------|
| [快速操作指南](doc/手册/快速操作指南.md) | 5分钟快速入门 |
| [对话页面手册](doc/手册/对话页面手册.md) | 对话界面使用指南 |
| [项目管理页面手册](doc/手册/项目管理页面手册.md) | 项目配置管理 |
| [模型管理页面手册](doc/手册/模型管理页面手册.md) | AI 模型配置 |
| [工作区管理页面手册](doc/手册/工作区管理页面手册.md) | 工作区配置 |
| [提示词管理页面手册](doc/手册/提示词管理页面手册.md) | 提示词模板管理 |
| [工具管理页面手册](doc/手册/工具管理页面手册.md) | 工具配置与激活 |
| [存储配置页面手册](doc/手册/存储配置页面手册.md) | 数据持久化配置 |

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 🛠️ 工具管理 | 注册、查询、更新工具定义，支持平台兼容性标记（操作系统、终端类型） |
| 🤖 LLM 调用 | 支持 OpenAI、Anthropic 等多种 LLM API |
| 💬 对话管理 | 管理对话会话和消息历史，支持多项目隔离 |
| ⚡ 事件驱动 | 基于事件总线的异步通信机制 |
| 🔧 技能扩展 | 支持多种技能插件扩展 |

---

## 项目结构

```
道一（UniDo）/
├── src/                       # 后端服务
│   ├── services/
│   │   ├── L1_infrastructure/     # 基础设施层
│   │   │   ├── L1a_id_generator/     # ID生成器
│   │   │   ├── L1b_persistence/      # 持久化服务
│   │   │   ├── L1c_llm/              # LLM客户端
│   │   │   ├── L1d_events/           # 事件总线
│   │   │   └── L1e_storage_config/  # 存储配置
│   │   ├── L2_domain/             # 领域层
│   │   │   ├── L2a_project_config/  # 项目配置
│   │   │   ├── L2b_memory_state/    # 记忆状态
│   │   │   ├── L2c_tool_execution/  # 工具执行
│   │   │   ├── L2d_llm_execution/   # LLM执行
│   │   │   ├── L2f_tool_management/  # 工具管理
│   │   │   └── L2h_prompt_management/ # 提示词管理
│   │   ├── L3_scenario_coordination/  # 场景协同层
│   │   └── L4_gateway/            # 网关层
│   │       ├── L4a_http_gateway/   # HTTP API
│   │       └── L4b_websocket_gateway/ # WebSocket
│   ├── tools/                     # 工具定义
│   │   ├── descriptions/         # 工具描述（中英文）
│   │   └── implement/             # 工具实现
│   ├── skills/                    # 技能扩展
│   └── data/                      # 数据存储
│
├── static_src/                   # 前端源码
│   ├── js/
│   │   ├── components/           # Vue 组件
│   │   │   ├── admin/            # 管理页面组件
│   │   │   │   ├── ModelPageComponent.js      # 模型管理
│   │   │   │   ├── ProjectPageComponent.js    # 项目管理
│   │   │   │   ├── PromptPageComponent.js      # 提示词管理
│   │   │   │   ├── StoragePageComponent.js     # 存储配置
│   │   │   │   ├── ToolPageComponent.js        # 工具管理
│   │   │   │   └── WorkspacePageComponent.js   # 工作区管理
│   │   │   ├── chat/             # 对话页面组件
│   │   │   │   ├── ChatPageComponent.js        # 对话主页面
│   │   │   │   ├── ChatSidebarComponent.js     # 侧边栏
│   │   │   │   ├── ChatInputComponent.js        # 输入组件
│   │   │   │   └── ...                       # 消息、工具卡片等
│   │   │   ├── infrastructure/   # 基础设施组件
│   │   │   │   ├── ApiClient.js              # API客户端
│   │   │   │   ├── DataNormalizer.js         # 数据标准化
│   │   │   │   ├── EventBus.js               # 事件总线
│   │   │   │   ├── StateManager.js           # 状态管理
│   │   │   │   └── WSClient.js               # WebSocket客户端
│   │   │   ├── nav/               # 导航组件
│   │   │   └── services/          # 业务服务
│   │   └── tests/                 # 前端测试
│   ├── package.json
│   └── playwright.config.ts
│
├── doc/                          # 文档
│   └── 手册/                      # 使用手册
│
├── config/                       # 配置文件
├── run.py                        # 启动脚本
└── requirements.txt              # Python依赖
```

---

## 技术栈

| 技术 | 说明 |
|------|------|
| **框架** | FastAPI + Uvicorn |
| **通信** | WebSocket + HTTP |
| **数据存储** | JSON 文件（可扩展至数据库） |
| **前端** | Vue.js + 原生 JavaScript |
| **工具链** | 18+ 内置工具（文件操作、搜索、命令执行等） |

---

## 服务访问

| 服务 | 地址 |
|------|------|
| **主界面** | http://localhost:8000 |
| **HTTP API** | http://localhost:8000/api |
| **WebSocket** | ws://localhost:8000/ws |
| **API 文档** | http://localhost:8000/docs |

---

## 开发

```powershell
# 开发模式运行（自动重载）
python run.py --reload
```

---

## 注意事项

- ✅ 首次运行会自动创建必要的数据目录
- ✅ Windows 环境下请使用 PowerShell 执行命令
- ✅ 确保 8000 端口未被占用
- ⚠️ API 密钥请勿提交到公开仓库

---

## 支持

如有问题，请查看 [故障排除](doc/手册/快速操作指南.md#故障排除) 章节。
