"""
L3a Task Coordination - Dialogue Service

对话服务：负责管理对话生命周期和上下文
"""

from typing import Optional
from services.L2_domain.L2b_memory_state.session_service import SessionService
from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L2_domain.L2b_memory_state.dialog_service import DialogService
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes
from .base_execution_service import BaseExecutionService
from ..schemas import DialogueResponse

class DialogueService:
    def __init__(self):
        self.session_service = SessionService()
        self.message_service = MessageService()
        self.dialog_service = DialogService()
        self.execution_service = BaseExecutionService()
        self.event_bus = EventBus.get_instance()
    
    def _ensure_session(self, session_id: str):
        if not session_id:
            raise ValueError("session_id 不能为空")

        
    def init_dialog(self, session_id: str) -> str:
        """
        初始化对话
        
        Args:
            session_id: 会话ID
        
        Returns:
            对话ID
        """
                # 如果没有传入 dialog_id，则创建新的
        
        dialog = self.dialog_service.create_dialog(
            session_id=session_id,
            dialog_type="default"
        )
        dialog_id = dialog.dialog_id

        # 更新dialog状态为ongoing
        self.dialog_service.update_dialog_status(dialog_id, 'ongoing')

        # 注：ROUND_STARTED 事件由 BaseExecutionService.execute_with_recursive_llm() 在循环中发布
        # 避免重复发布

        return dialog.dialog_id

    def process_dialogue(self, session_id: str, user_input: str) -> DialogueResponse:
        """
        处理对话
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
        """
        self._ensure_session(session_id)
        
        # 初始化对话
        dialog_id = self.init_dialog(session_id)
        

        # 获取当前平台信息
        platform_info = self.message_service._get_current_platform()
        
        # 构建包含平台信息的用户消息内容
        platform_reminder = f"<system-reminder>\n\n操作系统类型: {platform_info['os_type']}\n\n终端类型: {platform_info['terminal_type']}</system-reminder>"
        user_content = f"\n<user_input>\n{user_input}\n</user_input>"
        
        # 生成用户message对象
        user_message = self.message_service.create_message(
            dialog_id=dialog_id,
            role='user',
            content=f"{platform_reminder}{user_content}",
            metadata={
                'type': 'user_input',
                'source': 'ui'
            },
            platform_info=platform_info
        )

        # 发布用户输入事件
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': dialog_id,
                'message_id': user_message.message_id,
                'role': 'user',
                'content': user_input,
                'session_id': session_id
            }
        ))
                
        # 创建任务
        from ..schemas import Task
        task = Task(task_id=f"dialogue-{session_id}", input_data={
            "user_input": user_input,
            "session_id": session_id
        })

        # 使用递归 LLM 调用执行任务（支持多轮工具调用）
        execution_result = self.execution_service.execute_with_recursive_llm(
            task=task,
            session_id=session_id,
            user_input=user_input,
            dialog_id=dialog_id
        )

        response_content = execution_result.output_data.get("result", "") if execution_result else "任务执行完成"
        thinking_content = execution_result.output_data.get("thinking", "") if execution_result else ""

        # 保存助手消息（包含思考内容）
        self.message_service.create_message(
            dialog_id=dialog_id,
            role="assistant",
            content=response_content,
            metadata={"thinking": thinking_content}
        )

        # 注：ROUND_COMPLETED 事件由 BaseExecutionService.execute_with_recursive_llm() 在循环中发布
        # 避免重复发布

        # 更新dialog状态为completed
        self.dialog_service.update_dialog_status(dialog_id, 'completed')

        # 发布 dialog.completed 事件（对话完成）
        self.event_bus.publish(Event(
            event_type=EventTypes.DIALOG_COMPLETED,
            payload={
                'dialog_id': dialog_id,
                'session_id': session_id
            }
        ))

        return DialogueResponse(
            session_id=session_id,
            task_id=f"dialogue-{session_id}",
            dialog_id=dialog_id,
            status="completed",
            content=response_content,
            thinking=thinking_content
        )
