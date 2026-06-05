"""
L2b Memory and State Management - WebSocket Log Service

专门处理 WebSocket 消息日志的服务
"""

import json
from typing import List, Dict, Any, Optional
from .base_log_service import BaseLogService
from .api_log_models import WebSocketMessageLog


class WebSocketLogService(BaseLogService):
    """WebSocket消息日志服务"""
    
    COLLECTION_NAME = "websocket_messages"
    
    # 流式事件列表（不存储）
    STREAMING_EVENTS = {
        'llm.stream_chunk',
        'llm.thinking',
        'llm.reasoning',
    }
    
    def __init__(self):
        super().__init__()
    
    def save_websocket_message(self, client_id: str, payload: Any, 
                              direction: str = "inbound", session_id: str = None,
                              message_type: str = "", error_message: str = None) -> str:
        """
        保存WebSocket消息日志
        
        根据文档约定：
        - 不存储流式事件（llm.stream_chunk, llm.thinking, llm.reasoning）
        - 仅存储聚合事件/非流式事件
        
        :param client_id: 客户端ID
        :param payload: 消息内容
        :param direction: 消息方向 (inbound/outbound)
        :param session_id: 会话ID
        :param message_type: 消息类型
        :param error_message: 错误消息
        :return: 日志ID（如果事件被过滤返回空字符串）
        """
        action = self._extract_action(payload)
        
        # 过滤流式事件（不存储）
        if action in self.STREAMING_EVENTS:
            print(f"[WebSocketLogService] 跳过流式事件存储: {action}")
            return ""
        
        # 序列化消息内容
        payload_to_store = self._serialize_payload(payload)
        
        log = WebSocketMessageLog(
            log_id=self.generate_log_id("ws"),
            client_id=client_id,
            session_id=session_id,
            message_type=message_type or action or "",
            direction=direction,
            payload=payload_to_store,
            error_message=error_message
        )
        
        self._save_log(self.COLLECTION_NAME, log.to_dict())
        return log.log_id
    
    def get_websocket_messages(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取WebSocket消息日志列表
        
        :param filters: 过滤条件
        :return: 日志列表
        """
        if not filters or 'session_id' not in filters:
            return self._get_logs(self.COLLECTION_NAME, filters)
        
        target_session_id = filters['session_id']
        persistence_filters = {k: v for k, v in filters.items() if k != 'session_id'}
        all_messages = self._get_logs(self.COLLECTION_NAME, persistence_filters)
        
        # 获取该会话下的所有对话ID
        dialog_ids = self._get_dialog_ids_for_session(target_session_id)
        
        # 过滤匹配的消息
        return [msg for msg in all_messages if self._matches_session(msg, target_session_id, dialog_ids)]
    
    def get_websocket_message(self, log_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个WebSocket消息日志
        
        :param log_id: 日志ID
        :return: 日志详情
        """
        return self._get_log(self.COLLECTION_NAME, log_id)
    
    def _extract_action(self, payload: Any) -> Optional[str]:
        """从payload中提取action字段"""
        if isinstance(payload, dict):
            return payload.get('action')
        elif isinstance(payload, str):
            try:
                return json.loads(payload).get('action')
            except:
                return None
        return None
    
    def _get_dialog_ids_for_session(self, session_id: str) -> set:
        """获取指定会话下的所有对话ID"""
        try:
            from services.L2_domain.L2b_memory_state import get_dialog_service
            dialog_service = get_dialog_service()
            dialogs = dialog_service.list_dialogs(session_id)
            return {dialog.dialog_id for dialog in dialogs}
        except Exception as e:
            print(f"[WebSocketLogService] Failed to get dialogs for session: {e}")
            return set()
    
    def _matches_session(self, msg: Dict[str, Any], session_id: str, dialog_ids: set) -> bool:
        """判断消息是否匹配指定的会话"""
        # 直接匹配消息的session_id字段
        msg_session_id = msg.get('session_id')
        if msg_session_id == session_id:
            return True
        
        # 从payload中提取信息进行匹配
        try:
            payload_raw = msg.get('payload', '{}')
            payload = payload_raw if isinstance(payload_raw, dict) else json.loads(payload_raw)
            
            # 匹配payload中的session_id
            if payload.get('session_id') == session_id:
                if msg.get('session_id') is None:
                    msg['session_id'] = session_id
                return True
            
            # 匹配payload中的dialog_id（必须属于当前会话）
            payload_dialog_id = payload.get('dialog_id')
            if payload_dialog_id in dialog_ids:
                if msg.get('session_id') is None:
                    msg['session_id'] = session_id
                return True
                
        except json.JSONDecodeError:
            pass
        
        return False


# 全局单例
_websocket_log_service: Optional[WebSocketLogService] = None


def get_websocket_log_service() -> WebSocketLogService:
    """获取WebSocket消息日志服务的单例实例"""
    global _websocket_log_service
    if _websocket_log_service is None:
        _websocket_log_service = WebSocketLogService()
    return _websocket_log_service
