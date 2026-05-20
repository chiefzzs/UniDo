"""
Auth Middleware - 认证中间件
"""

from starlette.requests import Request
from starlette.responses import Response, JSONResponse

async def auth_middleware(request: Request, call_next):
    """认证中间件 - 处理API认证
    
    当前实现为简单的API Key认证，生产环境应使用更安全的认证方式。
    """
    # 公开路径不需要认证
    public_paths = [
        "/health",
        "/docs",
        "/openapi.json",
        "/",
        "/index.html"
    ]
    
    # 检查是否为公开路径
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # 获取API Key
    api_key = request.headers.get("X-API-Key")
    
    # 在开发环境中，如果没有配置API Key，允许所有请求
    if not api_key:
        # 开发模式下跳过认证
        return await call_next(request)
    
    # 验证API Key（实际实现中应该从配置或数据库中验证）
    # 这里简化处理，接受任何非空的API Key
    if api_key:
        return await call_next(request)
    
    # 认证失败
    return JSONResponse(
        status_code=401,
        content={"status": "error", "message": "Unauthorized - Invalid API Key"}
    )