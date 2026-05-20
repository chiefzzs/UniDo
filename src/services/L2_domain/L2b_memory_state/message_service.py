"""
L2b Memory and State Management - Message Service

消息管理服务：负责消息的创建、查询
"""

import uuid
from typing import List, Optional, Dict

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory

from .models import Message


class MessageService:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def _generate_id(self) -> str:
        return f"msg-{uuid.uuid4().hex[:12]}"

    def create_message(self, dialog_id: str, role: str, content: str, metadata: Dict = None) -> Message:
        message = Message(
            message_id=self._generate_id(),
            dialog_id=dialog_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.persistence.save('messages', message.to_dict())
        return message

    def get_message(self, message_id: str) -> Optional[Message]:
        all_messages = self.persistence.list('messages')
        for m in all_messages:
            if m.get('message_id') == message_id:
                return Message.from_dict(m)
        return None

    def list_messages(self, dialog_id: str = None, limit: int = None) -> List[Message]:
        all_messages = self.persistence.list('messages')
        result = [Message.from_dict(m) for m in all_messages]

        if dialog_id:
            result = [m for m in result if m.dialog_id == dialog_id]

        result.sort(key=lambda x: x.created_at)

        if limit:
            result = result[-limit:]

        return result
