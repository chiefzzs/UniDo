"""
前台历史消息服务

负责记录和提供前台展示用的历史消息。
与大模型对话历史（messages）不同，前台历史是发送给前端UI的WebSocket消息记录。
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory


class FrontendHistoryMessage:
    """前台历史消息实体"""
    
    def __init__(self, 
                 message_id: str,
                 session_id: str,
                 message_type: str,  # 'user', 'assistant', 'tool', 'event'
                 content: str,
                 metadata: Dict[str, Any] = None,
                 created_at: str = None):
        self.message_id = message_id
        self.session_id = session_id
        self.message_type = message_type
        self.content = content
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'session_id': self.session_id,
            'message_type': self.message_type,
            'content': self.content,
            'metadata': self.metadata,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FrontendHistoryMessage':
        return cls(
            message_id=data.get('message_id'),
            session_id=data.get('session_id'),
            message_type=data.get('message_type'),
            content=data.get('content'),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at')
        )


class FrontendHistoryService:
    """
    前台历史消息服务
    
    职责：
    1. 记录发送给前端的所有WebSocket消息
    2. 提供按会话查询历史消息的接口
    3. 支持消息类型的过滤和分页
    """
    
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()
    
    def _generate_id(self) -> str:
        """生成唯一消息ID"""
        return f"fhm-{uuid.uuid4().hex[:12]}"
    
    def record_message(self, session_id: str, message_type: str, 
                       content: str, metadata: Dict[str, Any] = None) -> FrontendHistoryMessage:
        """
        记录一条前台历史消息
        
        Args:
            session_id: 会话ID
            message_type: 消息类型 ('user', 'assistant', 'tool', 'event')
            content: 消息内容
            metadata: 额外元数据
            
        Returns:
            创建的消息对象
        """
        message = FrontendHistoryMessage(
            message_id=self._generate_id(),
            session_id=session_id,
            message_type=message_type,
            content=content,
            metadata=metadata or {}
        )
        
        # 保存到持久化存储
        self.persistence.save('frontend_history', message.to_dict())
        
        print(f"[FrontendHistoryService] 记录消息: {message_type} -> {content[:50]}...")
        return message
    
    def get_session_history(self, session_id: str, 
                           message_types: List[str] = None,
                           limit: int = 100,
                           offset: int = 0) -> List[FrontendHistoryMessage]:
        """
        获取会话的前台历史消息
        
        Args:
            session_id: 会话ID
            message_types: 消息类型过滤列表，None表示不过滤
            limit: 返回消息数量限制
            offset: 分页偏移
            
        Returns:
            历史消息列表，按时间排序
        """
        try:
            # 构建过滤条件
            filters = {'session_id': session_id}
            if message_types:
                # 这里简化处理，实际可能需要更复杂的查询
                pass
            
            # 从持久化存储获取
            records = self.persistence.list('frontend_history', filters)
            
            # 转换为消息对象
            messages = [FrontendHistoryMessage.from_dict(r) for r in records]
            
            # 按时间排序
            messages.sort(key=lambda m: m.created_at)
            
            # 应用分页
            messages = messages[offset:offset + limit]
            
            print(f"[FrontendHistoryService] 获取会话 {session_id} 历史: {len(messages)} 条")
            return messages
            
        except Exception as e:
            print(f"[FrontendHistoryService] 获取历史失败: {e}")
            return []
    
    def clear_session_history(self, session_id: str) -> bool:
        """
        清空会话的前台历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功
        """
        try:
            # 获取所有记录
            all_records = self.persistence.list('frontend_history', {})
            
            # 过滤出当前会话的记录
            session_records = [r for r in all_records if r.get('session_id') == session_id]
            
            # 保留其他会话的记录
            other_records = [r for r in all_records if r.get('session_id') != session_id]
            
            # 重写整个文件
            from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
            storage = StorageFactory.get_instance()
            if storage:
                storage._write_all('frontend_history', other_records)
            
            print(f"[FrontendHistoryService] 清空会话 {session_id} 历史，删除 {len(session_records)} 条")
            return True
            
        except Exception as e:
            print(f"[FrontendHistoryService] 清空历史失败: {e}")
            return False


# 全局服务实例
_frontend_history_service: Optional[FrontendHistoryService] = None

def get_frontend_history_service() -> FrontendHistoryService:
    """获取前台历史消息服务单例"""
    global _frontend_history_service
    if _frontend_history_service is None:
        _frontend_history_service = FrontendHistoryService()
    return _frontend_history_service
