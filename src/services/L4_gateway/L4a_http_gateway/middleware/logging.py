"""
Logging Middleware - 日志中间件
"""

import time
from starlette.requests import Request
from starlette.responses import Response

async def logging_middleware(request: Request, call_next):
    """日志中间件 - 记录请求信息"""
    start_time = time.time()
    
    # 记录请求信息
    print(f"📡 Request: {request.method} {request.url.path}")
    
    response: Response = await call_next(request)
    
    # 计算响应时间
    duration = time.time() - start_time
    
    # 记录响应信息
    print(f"📤 Response: {response.status_code} ({duration:.2f}ms)")
    
    return response