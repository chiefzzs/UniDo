"""
L2b Memory and State Management - API Log Service

提供API请求/响应和WebSocket消息的持久化服务
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from services.L1_infrastructure import get_persistence_service
from .api_log_models import APIRequestLog, WebSocketMessageLog


class APILogService:
    """API日志服务"""
    
    def __init__(self):
        self.persistence = get_persistence_service()
    
    def generate_log_id(self, prefix: str = "log") -> str:
        """生成日志ID"""
        return f"{prefix}-{uuid.uuid4().hex[:12]}"
    
    def generate_request_id(self) -> str:
        """生成请求ID"""
        return f"req-{uuid.uuid4().hex[:16]}"
    
    def save_api_request(self, method: str, path: str, client_id: str = "", 
                         query_params: Dict[str, Any] = None, body: Any = None,
                         headers: Dict[str, str] = None) -> str:
        """
        保存API请求日志
        
        :param method: HTTP方法 (GET, POST, PUT, DELETE等)
        :param path: 请求路径
        :param client_id: 客户端ID
        :param query_params: 查询参数
        :param body: 请求体
        :param headers: 请求头
        :return: 请求ID
        """
        request_id = self.generate_request_id()
        
        # 序列化请求体
        body_str = None
        if body is not None:
            try:
                body_str = json.dumps(body, ensure_ascii=False)
            except:
                body_str = str(body)
        
        log = APIRequestLog(
            log_id=self.generate_log_id("api"),
            request_id=request_id,
            client_id=client_id,
            method=method,
            path=path,
            query_params=query_params or {},
            body=body_str,
            headers=headers or {}
        )
        
        self.persistence.save("api_requests", log.to_dict())
        return request_id
    
    def update_api_response(self, request_id: str, status_code: int, 
                           response_body: Any = None, response_time: float = None,
                           error_message: str = None) -> bool:
        """
        更新API响应日志
        
        :param request_id: 请求ID
        :param status_code: 响应状态码
        :param response_body: 响应体
        :param response_time: 响应时间（毫秒）
        :param error_message: 错误消息
        :return: 是否更新成功
        """
        logs = self.persistence.list("api_requests", {"request_id": request_id})
        
        if not logs:
            return False
        
        log_data = logs[0]
        log_data['status_code'] = status_code
        
        # 序列化响应体
        if response_body is not None:
            try:
                log_data['response_body'] = json.dumps(response_body, ensure_ascii=False)
            except:
                log_data['response_body'] = str(response_body)
        
        if response_time is not None:
            log_data['response_time'] = response_time
        
        if error_message is not None:
            log_data['error_message'] = error_message
        
        self.persistence.save("api_requests", log_data)
        return True
    
    def save_websocket_message(self, client_id: str, payload: Any, 
                              direction: str = "inbound", session_id: str = None,
                              message_type: str = "", error_message: str = None) -> str:
        """
        保存WebSocket消息日志
        
        :param client_id: 客户端ID
        :param payload: 消息内容
        :param direction: 消息方向 (inbound/outbound)
        :param session_id: 会话ID
        :param message_type: 消息类型
        :param error_message: 错误消息
        :return: 日志ID
        """
        # 序列化消息内容
        payload_str = None
        if payload is not None:
            try:
                payload_str = json.dumps(payload, ensure_ascii=False)
            except:
                payload_str = str(payload)
        
        log = WebSocketMessageLog(
            log_id=self.generate_log_id("ws"),
            client_id=client_id,
            session_id=session_id,
            message_type=message_type,
            direction=direction,
            payload=payload_str,
            error_message=error_message
        )
        
        self.persistence.save("websocket_messages", log.to_dict())
        return log.log_id
    
    def get_api_requests(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取API请求日志列表
        
        :param filters: 过滤条件
        :return: 日志列表
        """
        return self.persistence.list("api_requests", filters)
    
    def get_api_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个API请求日志
        
        :param request_id: 请求ID
        :return: 日志详情
        """
        logs = self.persistence.list("api_requests", {"request_id": request_id})
        return logs[0] if logs else None
    
    def get_websocket_messages(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取WebSocket消息日志列表
        
        :param filters: 过滤条件
        :return: 日志列表
        """
        return self.persistence.list("websocket_messages", filters)
    
    def get_websocket_message(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个WebSocket消息日志
        
        :param log_id: 日志ID
        :return: 日志详情
        """
        logs = self.persistence.list("websocket_messages", {"log_id": log_id})
        return logs[0] if logs else None


# 全局单例
_api_log_service: Optional[APILogService] = None


def get_api_log_service() -> APILogService:
    """获取API日志服务的单例实例"""
    global _api_log_service
    if _api_log_service is None:
        _api_log_service = APILogService()
    return _api_log_service
