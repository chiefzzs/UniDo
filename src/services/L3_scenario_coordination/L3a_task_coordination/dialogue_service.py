"""
L3a Task Coordination - Dialogue Service

对话服务：负责管理对话生命周期和上下文
"""

from typing import Optional
from services.L2_domain.L2b_memory_state.session_service import SessionService
from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L2_domain.L2b_memory_state.dialog_service import DialogService
from .base_execution_service import BaseExecutionService
from ..schemas import DialogueResponse

class DialogueService:
    def __init__(self):
        self.session_service = SessionService()
        self.message_service = MessageService()
        self.dialog_service = DialogService()
        self.execution_service = BaseExecutionService()
    
    def _ensure_session(self, session_id: str):
        session = self.session_service.get_session(session_id)
        if not session:
            # 使用指定的session_id创建会话
            self.session_service.create_session(
                project_id="",
                name="New Session",
                session_id=session_id
            )
    
    def _ensure_dialog(self, session_id: str) -> str:
        dialogs = self.dialog_service.list_dialogs(session_id)
        if dialogs:
            return dialogs[0].dialog_id
        dialog = self.dialog_service.create_dialog(
            session_id=session_id,
            dialog_type="text"
        )
        return dialog.dialog_id
    
    def process_dialogue(self, session_id: str, user_input: str) -> DialogueResponse:
        self._ensure_session(session_id)
        dialog_id = self._ensure_dialog(session_id)
        
        self.message_service.create_message(
            dialog_id=dialog_id,
            role="user",
            content=user_input
        )
        
        from ..schemas import Task
        task = Task(task_id=f"dialogue-{session_id}", input_data={"user_input": user_input})
        execution_result = self.execution_service.execute_task(task)
        
        response_content = execution_result.output_data.get("result", "") if execution_result else "任务执行完成"
        
        self.message_service.create_message(
            dialog_id=dialog_id,
            role="assistant",
            content=response_content
        )
        
        return DialogueResponse(
            session_id=session_id,
            task_id=f"dialogue-{session_id}",
            status="completed",
            content=response_content
        )
