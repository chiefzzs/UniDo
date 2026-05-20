"""
L3c UI Scenarios - Message Manager

消息管理组件：支持创建历史消息对象。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes


class MessageManager:
    """
    消息管理组件
    
    支持创建历史消息对象：
    1. System Message：用于引导对话方向
    2. User Message：用于用户输入
    3. Assistant Message：用于系统回复
    4. Tool Message：用于工具调用结果
    """
    
    def __init__(self):
        self.message_service = MessageService()
        self.event_bus = EventBus.get_instance()
    
    def create_system_message(self, dialog_id: str, content: str, 
                              source: str = "system_prompt") -> Dict[str, Any]:
        """
        创建System Message
        
        用途：用于引导对话方向，设置助手行为模式和角色定位。
        """
        message = self.message_service.create_message(
            dialog_id=dialog_id,
            role='system',
            content=content,
            metadata={
                'type': 'system',
                'source': source
            }
        )
        
        # 发布消息添加事件
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': dialog_id,
                'message_id': message.message_id,
                'role': 'system'
            }
        ))
        
        return message.to_dict()
    
    def create_user_message(self, dialog_id: str, content: str, 
                           source: str = "ui") -> Dict[str, Any]:
        """
        创建User Message
        
        用途：用于封装用户输入内容。
        """
        message = self.message_service.create_message(
            dialog_id=dialog_id,
            role='user',
            content=content,
            metadata={
                'type': 'user_input',
                'source': source
            }
        )
        
        # 发布消息添加事件
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': dialog_id,
                'message_id': message.message_id,
                'role': 'user'
            }
        ))
        
        return message.to_dict()
    
    def create_assistant_message(self, dialog_id: str, content: str,
                                 tool_calls: Optional[list] = None,
                                 source: str = "llm") -> Dict[str, Any]:
        """
        创建Assistant Message
        
        用途：用于系统回复，可包含工具调用指令。
        """
        metadata = {
            'type': 'assistant_response',
            'source': source
        }
        
        message = self.message_service.create_message(
            dialog_id=dialog_id,
            role='assistant',
            content=content,
            metadata=metadata
        )
        
        # 如果有工具调用，添加到metadata中
        if tool_calls:
            message_dict = message.to_dict()
            message_dict['tool_calls'] = tool_calls
            return message_dict
        
        # 发布消息添加事件
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': dialog_id,
                'message_id': message.message_id,
                'role': 'assistant'
            }
        ))
        
        return message.to_dict()
    
    def create_tool_message(self, dialog_id: str, content: str,
                           call_id: str, tool_name: str,
                           success: bool = True,
                           source: str = "tool_executor") -> Dict[str, Any]:
        """
        创建Tool Message
        
        用途：用于工具调用结果返回。
        """
        message = self.message_service.create_message(
            dialog_id=dialog_id,
            role='tool',
            content=content,
            metadata={
                'type': 'tool_result',
                'source': source,
                'call_id': call_id,
                'tool_name': tool_name,
                'success': success
            }
        )
        
        # 发布消息添加事件
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': dialog_id,
                'message_id': message.message_id,
                'role': 'tool'
            }
        ))
        
        return message.to_dict()
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        获取消息
        """
        message = self.message_service.get_message(message_id)
        if message:
            return message.to_dict()
        return None
    
    def list_messages(self, dialog_id: str, limit: int = None) -> list:
        """
        列出对话的所有消息
        """
        messages = self.message_service.list_messages(dialog_id=dialog_id, limit=limit)
        return [msg.to_dict() for msg in messages]