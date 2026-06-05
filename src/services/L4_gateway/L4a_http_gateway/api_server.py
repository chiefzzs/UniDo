"""
API Server - HTTP服务器实现

使用FastAPI构建RESTful API服务，集成WebSocket支持。
"""

import os

# 全局 API 服务器实例
api_server_instance = None
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from services.L4_gateway.L4a_http_gateway.routes import (
    project_routes,
    session_routes,
    message_routes,
    config_routes,
    storage_config_routes,
    event_storage_config_routes,
    api_log_routes,
    llm_routes,
    history_chat_routes,
    prompt_routes
)
from services.L4_gateway.L4a_http_gateway.middleware.logging import logging_middleware
from services.L4_gateway.L4a_http_gateway.middleware.auth import auth_middleware
from services.L4_gateway.L4a_http_gateway.middleware.api_logging import APILoggingMiddleware
from services.L4_gateway.L4b_websocket_gateway.ws_server import WebSocketServer

class APIServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        global api_server_instance
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="AI Agent System API",
            description="L4 Gateway Layer - HTTP API Gateway",
            version="1.0.0"
        )
        
        # 初始化事件总线的持久化服务
        self._init_event_bus_persistence()
        
        self.ws_server = WebSocketServer()
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        
        # 设置全局实例
        global api_server_instance
        api_server_instance = self
    
    def _init_event_bus_persistence(self):
        """初始化事件总线的持久化服务"""
        from services.L1_infrastructure import get_event_bus, get_persistence_service
        
        # 初始化LLM执行服务，确保启动时打印模式信息
        from services.L2_domain.L2d_llm_execution import get_llm_execution_service
        get_llm_execution_service()
        
        try:
            event_bus = get_event_bus()
            persistence_service = get_persistence_service()
            event_bus._persistence_service = persistence_service
            
            # 验证持久化服务是否正确设置
            test_saved = persistence_service.save('events', {
                'record_id': 'test',
                'event_type': 'test',
                'payload': {},
                'test': True
            })
            print(f"[OK] 事件总线持久化服务已初始化，测试保存返回: {test_saved}")
        except Exception as e:
            import traceback
            print(f"[FAIL] 初始化事件总线持久化服务失败: {e}")
            traceback.print_exc()
        
        # 初始化事件控制台打印机
        self._init_event_console_printer()
        
        # 初始化WebSocket事件插件
        self._init_websocket_plugin()
    
    def _init_event_console_printer(self):
        """初始化事件控制台打印机"""
        from services.L1_infrastructure.L1d_events.EventConsolePrinter import get_event_console_printer
        from services.L1_infrastructure import get_event_bus
        
        try:
            printer = get_event_console_printer()
            event_bus = get_event_bus()
            printer.initialize(event_bus)
        except Exception as e:
            import traceback
            print(f"[FAIL] 初始化事件控制台打印机失败: {e}")
            traceback.print_exc()
    
    def _init_websocket_plugin(self):
        """初始化WebSocket事件插件"""
        from services.L1_infrastructure.L1d_events.EventWebSocketPlugin import get_websocket_plugin
        from services.L1_infrastructure import get_event_bus
        
        try:
            plugin = get_websocket_plugin()
            event_bus = get_event_bus()
            plugin.initialize(event_bus)
        except Exception as e:
            import traceback
            print(f"[FAIL] 初始化WebSocket插件失败: {e}")
            traceback.print_exc()
    
    def _setup_middleware(self):
        """设置中间件"""
        # CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # API请求日志中间件（记录所有请求和响应）
        self.app.add_middleware(APILoggingMiddleware)
        
        # 日志中间件
        self.app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
        
        # 认证中间件
        self.app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
    
    def _setup_routes(self):
        """设置路由"""
        from services.L4_gateway.L4a_http_gateway.routes.project_sessions_routes import router as project_sessions_router
        
        self.app.include_router(
            project_routes.router,
            prefix="/api/projects",
            tags=["Projects"]
        )
        
        # 项目会话路由（嵌套在projects下）
        self.app.include_router(
            project_sessions_router,
            prefix="/api/projects/{project_id}/sessions",
            tags=["Project Sessions"]
        )
        
        self.app.include_router(
            session_routes.router,
            prefix="/api/sessions",
            tags=["Sessions"]
        )
        
        self.app.include_router(
            message_routes.router,
            prefix="/api/messages",
            tags=["Messages"]
        )
        
        # 配置路由 (直接挂载在 /api 下)
        self.app.include_router(
            config_routes.router,
            prefix="/api",
            tags=["Configs"]
        )
        
        # 存储配置路由
        self.app.include_router(
            storage_config_routes.router,
            prefix="/api/storage-config",
            tags=["Storage Configs"]
        )
        
        # 事件存储配置路由
        self.app.include_router(
            event_storage_config_routes.router,
            prefix="/api/event-storage-config",
            tags=["Event Storage Configs"]
        )
        
        # API日志路由
        self.app.include_router(
            api_log_routes.router,
            prefix="/api",
            tags=["API Logs"]
        )
        
        # LLM模式切换路由
        self.app.include_router(
            llm_routes.router,
            tags=["LLM"]
        )
        
        # WebSocket缓存历史消息路由
        self.app.include_router(
            history_chat_routes.router,
            prefix="/api",
            tags=["History Chat"]
        )
        
        # 提示词管理路由
        self.app.include_router(
            prompt_routes.router,
            tags=["提示词管理"]
        )
        
        # 健康检查
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "layer": "L4 Gateway"}
        
        # WebSocket端点
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await websocket.accept()
            # 获取WebSocket插件并注册连接
            from services.L1_infrastructure.L1d_events.EventWebSocketPlugin import get_websocket_plugin
            plugin = get_websocket_plugin()
            plugin.register_connection(websocket)
            # 处理连接
            await self.ws_server.handle_connection(websocket, client_id, plugin)
    
    def _setup_static_files(self):
        """设置静态文件服务"""
        static_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'newstatic')
        static_dir = os.path.abspath(static_dir)
        
        if os.path.exists(static_dir):
            # 挂载静态文件到 /newstatic/ 路径
            self.app.mount("/newstatic", StaticFiles(directory=static_dir), name="newstatic")
            
            # 添加首页路由
            @self.app.get("/")
            async def index():
                import os
                index_path = os.path.join(static_dir, "index.html")
                if os.path.exists(index_path):
                    with open(index_path, "r", encoding="utf-8") as f:
                        return HTMLResponse(content=f.read(), status_code=200)
                return {"message": "AI Agent System API", "layer": "L4 Gateway"}
        
        # 开发模式：挂载static_src目录到 /static/ 路径
        dev_static_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'static_src')
        dev_static_dir = os.path.abspath(dev_static_dir)
        
        if os.path.exists(dev_static_dir):
            self.app.mount("/static", StaticFiles(directory=dev_static_dir), name="static")
            print(f"[DEBUG] Mounted dev static files from: {dev_static_dir}")
    
    def run(self):
        """启动HTTP服务器"""
        import uvicorn
        print(f"🚀 Starting L4 HTTP Gateway on http://{self.host}:{self.port}")
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            reload=True,
            reload_dirs=["src"]
        )
    
    def get_app(self):
        """获取FastAPI应用实例"""
        return self.app

def create_app():
    """创建FastAPI应用实例（工厂函数）
    
    用于uvicorn的factory模式启动。
    """
    server = APIServer()
    return server.get_app()

if __name__ == "__main__":
    import uvicorn
    import random
    server = APIServer()
    api_server_instance = server
    port = random.randint(9000, 9999)
    print(f"Starting server on port {port}...")
    uvicorn.run(
        server.app,
        host="127.0.0.1",
        port=port,
        reload=False
    )