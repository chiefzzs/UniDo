"""
L3c UI Scenarios - Session Manager

会话管理组件：管理用户会话的创建、查询、更新、删除和归档。
调用L2b SessionService进行持久化操作。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.L2_domain.L2b_memory_state.session_service import SessionService
from services.L2_domain.L2b_memory_state.dialog_service import DialogService
from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes


class SessionManager:
    """
    会话管理组件
    
    职责：
    1. 会话创建：新建session对象，初始化dialog对象，添加system message
    2. 新建对话对象：返回session的第一个dialog或创建新dialog
    3. 得到历史消息：非压缩式或压缩式获得历史消息
    4. 得到大模型信息：依据Session关联的Project获取大模型信息
    """
    
    def __init__(self):
        self.session_service = SessionService()
        self.dialog_service = DialogService()
        self.message_service = MessageService()
        self.event_bus = EventBus.get_instance()
    
    def create_session(self, project_id: str, name: str = "未命名会话") -> Dict[str, Any]:
        """
        创建会话
        
        场景1：会话创建
        1) 新建session对象
        2) 初始化此session对象包含的dialog对象
        3) 给第一个dialog对象增加system message，用于引导对话方向
        
        结果：
        - sessions.json中多了一个session对象
        - events.json中多了一个event对象
        - dialogs.json中多了一个dialog对象
        - messages.json中多了一个message对象
        """
        session = self.session_service.create_session(
            project_id=project_id,
            name=name
        )
        
        # 创建初始dialog
        dialog = self.dialog_service.create_dialog(
            session_id=session.session_id,
            dialog_type="default"
        )
        
        # 添加system message
        system_message = self.message_service.create_message(
            dialog_id=dialog.dialog_id,
            role="system",
            content="你是一个智能助手，能够帮助用户完成各种任务。",
            metadata={
                "type": "system",
                "source": "system_prompt"
            }
        )
        
        # 发布会话创建事件
        self.event_bus.publish(Event(
            event_type=EventTypes.SESSION_CREATED,
            payload={
                'session_id': session.session_id,
                'project_id': project_id,
                'dialog_id': dialog.dialog_id,
                'message_id': system_message.message_id
            }
        ))
        
        return {
            'session': session.to_dict(),
            'dialog': dialog.to_dict(),
            'system_message': system_message.to_dict()
        }
    
    def get_or_create_default_dialog(self, session_id: str) -> Dict[str, Any]:
        """
        获取或创建默认对话
        
        场景2：新建对话对象
        1) 如果是第一次，返回session对象的第一个dialog对象
        2) 如果不是第一次，session对象新建一个dialog对象，并放到自己的队列中
        """
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 获取session的所有dialog
        dialogs = self.dialog_service.list_dialogs(session_id=session_id)
        
        if not dialogs:
            # 第一次，创建初始dialog
            dialog = self.dialog_service.create_dialog(
                session_id=session_id,
                dialog_type="default"
            )
            return dialog.to_dict()
        else:
            # 返回第一个dialog
            return dialogs[0].to_dict()
    
    def get_history_messages(self, session_id: str, compress: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        """
        得到历史消息
        
        场景3：得到历史消息
        
        非压缩式获得：
        1) 从session对象中获取所有dialog对象
        2) 从每个dialog对象中获取所有message对象
        3) 合并所有message对象，返回给用户
        
        压缩式获得：
        当历史消息 > 设定的上限
        1) 最近的dialog对象，读取所有消息
        2) 历史dialog，读取压缩消息
        """
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 获取所有dialog
        dialogs = self.dialog_service.list_dialogs(session_id=session_id)
        
        all_messages = []
        for dialog in dialogs:
            messages = self.message_service.list_messages(dialog_id=dialog.dialog_id)
            all_messages.extend([msg.to_dict() for msg in messages])
        
        # 按时间排序
        all_messages.sort(key=lambda x: x.get('created_at', ''))
        
        # 压缩处理
        if compress and len(all_messages) > limit:
            # 保留最近的limit条消息
            return all_messages[-limit:]
        
        return all_messages
    
    def get_llm_info(self, session_id: str) -> Dict[str, Any]:
        """
        得到大模型信息
        
        场景4：得到大模型信息
        依据本Session关联的Project，得到关联的大模型信息，返回大模型信息
        """
        session = self.session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 这里应该从Project获取大模型信息
        # 暂时返回默认配置
        return {
            'model': 'Qwen/Qwen3.5-397B-A17B',
            'max_tokens': 16000,
            'temperature': 0.7,
            'stream': True
        }
    
    def update_session_status(self, session_id: str, status: str) -> Dict[str, Any]:
        """
        更新会话状态
        
        状态：
        - idle: 首次创建的对象
        - ongoing: 对话进行中
        - finished: 对话结束
        """
        session = self.session_service.update_session(
            session_id=session_id,
            status=status
        )
        
        if session:
            return session.to_dict()
        else:
            raise ValueError(f"Session {session_id} not found")