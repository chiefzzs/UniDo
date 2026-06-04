# Trae AI 助手后端服务

基于 Python 的 AI 助手后端服务，提供工具管理、LLM 调用、对话管理等核心功能。

## 项目结构

```
src/
├── services/
│   ├── L1_infrastructure/     # 基础设施层（ID生成、持久化、LLM、事件）
│   ├── L2_domain/             # 领域层（项目配置、记忆状态、工具执行、LLM执行）
│   ├── L3_scenario_coordination/  # 场景协同层
│   └── L4_gateway/            # 网关层（HTTP、WebSocket）
├── tools/                     # 工具定义
├── skills/                    # 技能扩展
└── data/                      # 数据存储
```

## 快速开始

### 环境要求

- Python 3.8+
- 依赖包：见 `requirements.txt`（如不存在，需手动安装）

### 安装依赖

```powershell
# 安装基础依赖
pip install fastapi uvicorn websockets pydantic python-dotenv

# 安装数据库和工具依赖
pip install aiofiles python-multipart requests
```

### 启动服务

```powershell
# 进入项目目录
cd d:\learnning\260521

# 启动主服务
python run.py
```

### 服务访问

- **HTTP API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws
- **API 文档**: http://localhost:8000/docs

## 核心功能

1. **工具管理**: 注册、查询、更新工具定义，支持平台兼容性标记
2. **LLM 调用**: 支持流式和非流式 LLM 调用
3. **对话管理**: 管理对话会话和消息历史
4. **技能扩展**: 支持多种技能插件（创意绘图、代码助手等）
5. **事件驱动**: 基于事件总线的异步通信机制

## 配置说明

配置文件位于 `config/` 目录：
- `platform_tools.json`: 平台工具配置
- `src/data/dev/`: 开发环境数据

## 技术栈

- **框架**: FastAPI + Uvicorn
- **通信**: WebSocket + HTTP
- **数据存储**: JSON 文件（可扩展至数据库）
- **工具链**: 支持 18+ 内置工具（文件操作、搜索、命令执行等）

## 开发

```powershell
# 开发模式运行（自动重载）
python run.py --reload
```

## 注意事项

- 首次运行会自动创建必要的数据目录
- Windows 环境下请使用 PowerShell 执行命令
- 确保 8000 端口未被占用