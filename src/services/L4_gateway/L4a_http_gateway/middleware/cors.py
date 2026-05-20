"""
CORS Middleware - CORS中间件

处理跨域资源共享请求。
"""

from starlette.middleware.cors import CORSMiddleware

def setup_cors(app):
    """设置CORS中间件"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )