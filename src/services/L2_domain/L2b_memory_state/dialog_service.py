"""
L2b Memory and State Management - Dialog Service

对话管理服务：负责对话的创建、查询、状态更新
"""

import uuid
from typing import List, Optional

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory

from .models import Dialog


class DialogService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus

    def _generate_id(self) -> str:
        return f"dialog-{uuid.uuid4().hex[:12]}"

    def create_dialog(self, session_id: str, dialog_type: str) -> Dialog:
        dialog = Dialog(
            dialog_id=self._generate_id(),
            session_id=session_id,
            dialog_type=dialog_type
        )
        self.persistence.save('dialogs', dialog.to_dict())
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
