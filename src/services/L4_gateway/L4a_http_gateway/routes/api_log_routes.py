"""
API Log Routes - API日志查询路由

提供API请求/响应和WebSocket消息的查询接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List

from services.L2_domain.L2b_memory_state import get_api_log_service

router = APIRouter(prefix="/api-logs", tags=["API Logs"])


@router.get("/api-requests", summary="获取API请求日志列表")
async def get_api_requests(
    client_id: Optional[str] = Query(None, description="客户端ID"),
    method: Optional[str] = Query(None, description="HTTP方法"),
    path: Optional[str] = Query(None, description="请求路径"),
    status_code: Optional[int] = Query(None, description="响应状态码")
):
    """
    获取API请求日志列表，支持按条件过滤
    
    :param client_id: 客户端ID过滤
    :param method: HTTP方法过滤 (GET, POST, PUT, DELETE等)
    :param path: 请求路径过滤
    :param status_code: 响应状态码过滤
    :return: 日志列表
    """
    try:
        filters = {}
        if client_id:
            filters['client_id'] = client_id
        if method:
            filters['method'] = method
        if path:
            filters['path'] = path
        if status_code is not None:
            filters['status_code'] = status_code
        
        log_service = get_api_log_service()
        logs = log_service.get_api_requests(filters)
        
        return {"status": "success", "data": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-requests/{request_id}", summary="获取单个API请求日志")
async def get_api_request(request_id: str):
    """
    获取单个API请求日志详情
    
    :param request_id: 请求ID
    :return: 日志详情
    """
    try:
        log_service = get_api_log_service()
        log = log_service.get_api_request(request_id)
        
        if not log:
            raise HTTPException(status_code=404, detail=f"API request log not found: {request_id}")
        
        return {"status": "success", "data": log}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websocket-messages", summary="获取WebSocket消息日志列表")
async def get_websocket_messages(
    client_id: Optional[str] = Query(None, description="客户端ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    direction: Optional[str] = Query(None, description="消息方向 (inbound/outbound)"),
    message_type: Optional[str] = Query(None, description="消息类型")
):
    """
    获取WebSocket消息日志列表，支持按条件过滤
    
    :param client_id: 客户端ID过滤
    :param session_id: 会话ID过滤
    :param direction: 消息方向过滤 (inbound/outbound)
    :param message_type: 消息类型过滤
    :return: 日志列表
    """
    try:
        filters = {}
        if client_id:
            filters['client_id'] = client_id
        if session_id:
            filters['session_id'] = session_id
        if direction:
            filters['direction'] = direction
        if message_type:
            filters['message_type'] = message_type
        
        log_service = get_api_log_service()
        logs = log_service.get_websocket_messages(filters)
        
        return {"status": "success", "data": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websocket-messages/{log_id}", summary="获取单个WebSocket消息日志")
async def get_websocket_message(log_id: str):
    """
    获取单个WebSocket消息日志详情
    
    :param log_id: 日志ID
    :return: 日志详情
    """
    try:
        log_service = get_api_log_service()
        log = log_service.get_websocket_message(log_id)
        
        if not log:
            raise HTTPException(status_code=404, detail=f"WebSocket message log not found: {log_id}")
        
        return {"status": "success", "data": log}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
