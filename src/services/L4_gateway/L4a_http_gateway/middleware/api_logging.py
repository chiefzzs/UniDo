"""
API Logging Middleware - API请求日志中间件

自动记录所有HTTP请求和响应
"""

import time
import json
from typing import Callable
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware

# 延迟导入以避免循环依赖
_api_log_service = None

def get_api_log_service():
    global _api_log_service
    if _api_log_service is None:
        from services.L2_domain.L2b_memory_state import get_api_log_service as get_service
        _api_log_service = get_service()
    return _api_log_service


class APILoggingMiddleware(BaseHTTPMiddleware):
    """API请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 获取客户端ID（从请求头或生成）
        client_id = request.headers.get('X-Client-ID', f"client-{id(request)}")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 提取请求信息
        method = request.method
        path = str(request.url.path)
        query_params = dict(request.query_params)
        
        # 提取请求头（过滤敏感信息）
        headers = {}
        for key, value in request.headers.items():
            if key.lower() not in ['authorization', 'cookie', 'x-api-key']:
                headers[key] = value
        
        # 保存请求日志（不读取请求体，只记录基本信息）
        log_service = get_api_log_service()
        request_id = log_service.save_api_request(
            method=method,
            path=path,
            client_id=client_id,
            query_params=query_params,
            body=None,  # 不在中间件中读取请求体，避免影响后续处理
            headers=headers
        )
        
        # 添加请求ID到请求状态
        request.state.request_id = request_id
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 记录响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 更新响应日志（只记录状态码和响应时间，不读取响应体）
            log_service.update_api_response(
                request_id=request_id,
                status_code=response.status_code,
                response_body=None,
                response_time=response_time
            )
            
            # 添加请求ID到响应头
            response.headers['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            # 记录异常
            response_time = (time.time() - start_time) * 1000
            log_service.update_api_response(
                request_id=request_id,
                status_code=500,
                error_message=str(e),
                response_time=response_time
            )
            raise
