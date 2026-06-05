"""
L3c UI Scenarios - Dialog Manager

对话管理组件：管理对话的生命周期和状态流转。
"""

from typing import Dict, Any, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.L2_domain.L2b_memory_state.dialog_service import DialogService
from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes


class DialogManager:
    """
    对话管理组件
    
    职责：
    1. 管理对话的生命周期
    2. 处理用户输入，生成message对象（现在由DialogueService内部处理）
    3. 调用通用任务协调流程
    4. 结束会话，启动对话压缩历史
    """
    
    def __init__(self):
        self.dialog_service = DialogService()
        self.message_service = MessageService()
        self.event_bus = EventBus.get_instance()
    
    def process_user_input(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        处理用户的一次对话
        
        主要流程：
        1. 调用通用任务协调流程（DialogueService内部创建dialog和用户消息）
        2. 获取助手回复消息
        3. 返回结果
        
        状态：
        - idle: 首次创建的对象
        - ongoing: 对话进行中
        - finished: 对话结束
        """
        # 调用通用任务协调流程（不传递dialog_id，由DialogueService内部创建）
        from services.L3_scenario_coordination.L3a_task_coordination.dialogue_service import DialogueService
        dialogue_service = DialogueService()
        dialogue_result = dialogue_service.process_dialogue(session_id, user_input)
        
        # 从 dialogue_result 获取 dialog_id
        dialog_id = dialogue_result.dialog_id
        
        # 获取助手回复消息
        messages = self.message_service.list_messages(dialog_id)
        assistant_message = None
        user_message = None
        for msg in reversed(messages):
            if not assistant_message and msg.role == 'assistant':
                assistant_message = msg
            elif not user_message and msg.role == 'user':
                user_message = msg
            if assistant_message and user_message:
                break
        
        result = {
            'dialog_id': dialog_id,
            'user_message': user_message.to_dict() if user_message else None,
            'assistant_message': assistant_message.to_dict() if assistant_message else None,
            'status': 'completed',
            'content': dialogue_result.content,
            'round_number': 1  # 每个对话从1开始
        }
        
        return result
    
    def finish_dialog(self, dialog_id: str, compress: bool = True) -> Dict[str, Any]:
        """
        结束对话，启动对话压缩历史
        
        主要流程：
        1) 压缩本dialog的所有消息，生成压缩消息对象
        2) 保存压缩消息对象
        """
        # 更新dialog状态为finished
        dialog = self.dialog_service.update_dialog_status(dialog_id, 'finished')
        
        if not dialog:
            raise ValueError(f"Dialog {dialog_id} not found")
        
        result = {
            'dialog_id': dialog_id,
            'status': 'finished'
        }
        
        # 如果需要压缩
        if compress:
            # 获取所有消息
            messages = self.message_service.list_messages(dialog_id=dialog_id)
            
            # 生成压缩消息（这里简化处理，实际应该使用LLM进行压缩）
            compressed_content = f"[Compressed {len(messages)} messages]"
            
            # 保存压缩消息
            compressed_message = self.message_service.create_message(
                dialog_id=dialog_id,
                role='system',
                content=compressed_content,
                metadata={
                    'type': 'compressed',
                    'original_message_count': len(messages)
                }
            )
            
            result['compressed_message'] = compressed_message.to_dict()
        
        # 发布对话完成事件
        self.event_bus.publish(Event(
            event_type=EventTypes.DIALOG_COMPLETED,
            payload={'dialog_id': dialog_id}
        ))
        
        return result
    
    def get_dialog_messages(self, dialog_id: str) -> List[Dict[str, Any]]:
        """
        获取对话的所有消息
        """
        messages = self.message_service.list_messages(dialog_id=dialog_id)
        return [msg.to_dict() for msg in messages]
