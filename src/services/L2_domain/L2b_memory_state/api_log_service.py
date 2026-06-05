"""
L2b Memory and State Management - API Log Service

统一的日志服务入口（向后兼容）

注意：此文件为保持向后兼容性而保留，新代码建议直接使用：
- APIRequestLogService (处理 RESTful API 日志)
- WebSocketLogService (处理 WebSocket 消息日志)
"""

from typing import List, Dict, Any, Optional
from .api_request_log_service import get_api_request_log_service
from .websocket_log_service import get_websocket_log_service


class APILogService:
    """API日志服务（统一入口，向后兼容）"""
    
    # 流式事件列表（不存储）
    STREAMING_EVENTS = {
        'llm.stream_chunk',
        'llm.thinking',
        'llm.reasoning',
    }
    
    # 聚合事件列表（存储）
    AGGREGATE_EVENTS = {
        'llm.call_text_completed',
        'llm.call_thinking_completed',
        'llm.call_reasoning_completed',
        'llm.tool_call_completed',
    }
    
    def __init__(self):
        self._api_request_service = get_api_request_log_service()
        self._websocket_service = get_websocket_log_service()
    
    def generate_log_id(self, prefix: str = "log") -> str:
        """生成日志ID"""
        return self._api_request_service.generate_log_id(prefix)
    
    # ========== RESTful API 日志方法（委托给 APIRequestLogService）==========
    
    def save_api_request(self, method: str, path: str, client_id: str = "", 
                         query_params: Dict[str, Any] = None, body: Any = None,
                         headers: Dict[str, str] = None) -> str:
        """保存API请求日志"""
        return self._api_request_service.save_api_request(
            method, path, client_id, query_params, body, headers
        )
    
    def update_api_response(self, request_id: str, status_code: int, 
                           response_body: Any = None, response_time: float = None,
                           error_message: str = None) -> bool:
        """更新API响应日志"""
        return self._api_request_service.update_api_response(
            request_id, status_code, response_body, response_time, error_message
        )
    
    def get_api_requests(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """获取API请求日志列表"""
        return self._api_request_service.get_api_requests(filters)
    
    def get_api_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """获取单个API请求日志"""
        return self._api_request_service.get_api_request(request_id)
    
    # ========== WebSocket 日志方法（委托给 WebSocketLogService）==========
    
    def save_websocket_message(self, client_id: str, payload: Any, 
                              direction: str = "inbound", session_id: str = None,
                              message_type: str = "", error_message: str = None) -> str:
        """保存WebSocket消息日志"""
        return self._websocket_service.save_websocket_message(
            client_id, payload, direction, session_id, message_type, error_message
        )
    
    def get_websocket_messages(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """获取WebSocket消息日志列表"""
        return self._websocket_service.get_websocket_messages(filters)
    
    def get_websocket_message(self, log_id: str) -> Optional[Dict[str, Any]]:
        """获取单个WebSocket消息日志"""
        return self._websocket_service.get_websocket_message(log_id)


# 全局单例
_api_log_service: Optional[APILogService] = None


def get_api_log_service() -> APILogService:
    """获取API日志服务的单例实例（向后兼容）"""
    global _api_log_service
    if _api_log_service is None:
        _api_log_service = APILogService()
    return _api_log_service
