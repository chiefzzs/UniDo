"""
WebSocket消息缓存服务

用于临时缓存WebSocket消息，支持会话切换时的消息回放。
消息不持久化到磁盘，仅在内存中缓存。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class WebSocketMessage:
    """WebSocket消息对象"""
    
    def __init__(self, session_id: str, message_type: str, content: str, 
                 metadata: Dict[str, Any] = None):
        self.message_id = f"ws-{datetime.now().timestamp()}-{hash(session_id + content) % 100000}"
        self.session_id = session_id
        self.message_type = message_type  # user, assistant, tool, event
        self.content = content
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'message_type': self.message_type,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at
        }


class WebSocketCacheService:
    """WebSocket消息缓存服务"""
    
    _instance = None
    
    def __init__(self):
        # 消息缓存: {session_id: [messages...]}
        self._cache: Dict[str, List[WebSocketMessage]] = {}
        # 最大缓存消息数（每个会话）
        self._max_messages_per_session = 1000
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = WebSocketCacheService()
        return cls._instance
    
    def add_message(self, session_id: str, message_type: str, content: str, 
                    metadata: Dict[str, Any] = None):
        """
        添加消息到缓存
        
        Args:
            session_id: 会话ID
            message_type: 消息类型 (user, assistant, tool, event)
            content: 消息内容
            metadata: 元数据
        """
        if session_id not in self._cache:
            self._cache[session_id] = []
        
        message = WebSocketMessage(session_id, message_type, content, metadata)
        self._cache[session_id].append(message)
        
        # 限制缓存数量
        if len(self._cache[session_id]) > self._max_messages_per_session:
            self._cache[session_id] = self._cache[session_id][-self._max_messages_per_session:]
    
    def get_messages(self, session_id: str, limit: int = 100, offset: int = 0,
                     message_types: Optional[List[str]] = None) -> List[WebSocketMessage]:
        """
        获取会话的缓存消息
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            offset: 分页偏移
            message_types: 消息类型过滤
        
        Returns:
            消息列表
        """
        if session_id not in self._cache:
            return []
        
        messages = self._cache[session_id]
        
        # 类型过滤
        if message_types:
            messages = [m for m in messages if m.message_type in message_types]
        
        # 分页
        start = offset
        end = start + limit
        return messages[start:end]
    
    def get_message_count(self, session_id: str) -> int:
        """获取会话的消息数量"""
        return len(self._cache.get(session_id, []))
    
    def clear_session(self, session_id: str):
        """清空会话缓存"""
        if session_id in self._cache:
            del self._cache[session_id]
    
    def clear_all(self):
        """清空所有缓存"""
        self._cache.clear()


def get_websocket_cache_service() -> WebSocketCacheService:
    """获取WebSocket缓存服务实例"""
    return WebSocketCacheService.get_instance()