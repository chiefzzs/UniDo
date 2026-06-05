"""
L2b Memory and State Management - Dialog Service

对话管理服务：负责对话的创建、查询、状态更新
"""

from typing import List, Optional

from services.L1_infrastructure.L1a_id_generator.id_generator import generate_dialog_id
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes

from .models import Dialog


class DialogService:
    """
    对话服务
        
        1) 给第一个dialog对象增加system message（dialog_service.create_dialog 内部处理）
       
    """

    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()

    def create_dialog(self, session_id: str, dialog_type: str) -> Dialog:
        dialog = Dialog(
            dialog_id=generate_dialog_id(),
            session_id=session_id,
            dialog_type=dialog_type
        )
        self.persistence.save('dialogs', dialog.to_dict())

        existing_dialogs = self.list_dialogs(session_id)
        is_first_dialog = len(existing_dialogs) == 0

        if is_first_dialog:
             from services.L2_domain.L2b_memory_state.message_service import MessageService
             message_service = MessageService()
             message_service.create_message(
                 dialog_id=dialog.dialog_id,
                 role="system",
                 content="你是一个智能助手，能够帮助用户完成各种任务。",
                 metadata={
                     "type": "system",
                     "source": "system_prompt"
                 }
             )

        self.event_bus.publish(Event(
            event_type=EventTypes.DIALOG_CREATED,
            payload={
                'dialog_id': dialog.dialog_id,
                'session_id': session_id,
                'dialog_type': dialog_type
            }
        ))

        return dialog

    def get_dialog(self, dialog_id: str) -> Optional[Dialog]:
        all_dialogs = self.persistence.list('dialogs')
        for d in all_dialogs:
            if d.get('dialog_id') == dialog_id:
                return Dialog.from_dict(d)
        return None

    def list_dialogs(self, session_id: str = None) -> List[Dialog]:
        all_dialogs = self.persistence.list('dialogs')
        result = [Dialog.from_dict(d) for d in all_dialogs]

        if session_id:
            result = [d for d in result if d.session_id == session_id]

        return result

    def update_dialog_status(self, dialog_id: str, status: str) -> Optional[Dialog]:
        all_dialogs = self.persistence.list('dialogs')
        for i, d in enumerate(all_dialogs):
            if d.get('dialog_id') == dialog_id:
                d['status'] = status
                all_dialogs[i] = d
                self.persistence.save('dialogs', d)
                return Dialog.from_dict(d)
        return None
