"""
L2b Memory and State Management - Message Service

消息管理服务：负责消息的创建、查询
"""

from typing import List, Optional, Dict

from services.L1_infrastructure.L1a_id_generator.id_generator import generate_message_id
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory

from .models import Message


class MessageService:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def create_message(self, dialog_id: str, role: str, content: str, metadata: Dict = None, platform_info: Dict = None) -> Message:
        # 如果没有提供平台信息且是用户消息，自动获取当前平台信息
        if role == 'user' and not platform_info:
            platform_info = self._get_current_platform()
        
        message = Message(
            message_id=generate_message_id(),
            dialog_id=dialog_id,
            role=role,
            content=content,
            metadata=metadata or {},
            platform_info=platform_info or {}
        )
        self.persistence.save('messages', message.to_dict())
        return message

    @staticmethod
    def _get_current_platform() -> Dict[str, str]:
        """获取当前平台信息"""
        import sys
        os_type = 'windows' if sys.platform.startswith('win') else \
                  'linux' if sys.platform.startswith('linux') else \
                  'macos' if sys.platform.startswith('darwin') else 'unknown'
        
        terminal_type = 'powershell' if os_type == 'windows' else 'bash'
        
        return {
            'os_type': os_type,
            'terminal_type': terminal_type
        }

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
