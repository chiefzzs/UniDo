"""
L1 Infrastructure - ID Generator

提供统一的ID生成服务，确保ID生成的唯一性和一致性
遵循职责单一原则（SRP），将ID生成职责集中在一个类中
"""

import uuid
from datetime import datetime
from typing import Optional


class IDGenerator:
    """统一的ID生成器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'IDGenerator':
        """获取单例实例"""
        return cls()
    
    def generate_session_id(self) -> str:
        """生成会话ID"""
        return f"sess-{uuid.uuid4().hex[:12]}"
    
    def generate_dialog_id(self) -> str:
        """生成对话ID"""
        return f"dialog-{uuid.uuid4().hex[:12]}"
    
    def generate_message_id(self) -> str:
        """生成消息ID"""
        return f"msg-{uuid.uuid4().hex[:12]}"
    
    def generate_request_id(self) -> str:
        """生成LLM请求ID"""
        return f"req-{uuid.uuid4().hex[:12]}"
    
    def generate_call_id(self) -> str:
        """生成工具调用ID"""
        return f"call-{uuid.uuid4().hex[:12]}"
    
    def generate_task_id(self) -> str:
        """生成任务ID"""
        return f"task-{uuid.uuid4().hex[:12]}"
    
    def generate_group_id(self) -> str:
        """生成任务组ID"""
        return f"group-{uuid.uuid4().hex[:12]}"
    
    def generate_tool_id(self) -> str:
        """生成工具定义ID"""
        return f"tool-{uuid.uuid4().hex[:12]}"
    
    def generate_skill_id(self) -> str:
        """生成技能定义ID"""
        return f"skill-{uuid.uuid4().hex[:12]}"
    
    def generate_project_id(self) -> str:
        """生成项目ID"""
        return f"proj-{uuid.uuid4().hex[:12]}"
    
    def generate_log_id(self, prefix: str = "log") -> str:
        """生成日志ID"""
        return f"{prefix}-{uuid.uuid4().hex[:12]}"
    
    def generate_event_id(self) -> str:
        """生成事件ID"""
        return f"evt-{uuid.uuid4().hex[:12]}"
    
    def generate_record_id(self) -> str:
        """生成事件记录ID"""
        return f"rec-{uuid.uuid4().hex[:12]}"
    
    def generate_subscription_id(self) -> str:
        """生成订阅ID"""
        return f"sub-{uuid.uuid4().hex[:8]}"
    
    def generate_memory_id(self, memory_type: str = "mem") -> str:
        """生成记忆ID"""
        return f"{memory_type}-{uuid.uuid4().hex[:12]}"
    
    def generate_template_id(self) -> str:
        """生成模板ID"""
        return f"template-{uuid.uuid4().hex[:12]}"
    
    def generate_config_id(self, config_type: str = "config") -> str:
        """生成配置ID"""
        return f"{config_type}-{uuid.uuid4().hex[:12]}"
    
    def generate_frontend_history_id(self) -> str:
        """生成前台历史消息ID"""
        return f"fhm-{uuid.uuid4().hex[:12]}"
    
    def generate_websocket_message_id(self) -> str:
        """生成WebSocket消息ID（用于缓存）"""
        return f"wsc-{uuid.uuid4().hex[:12]}"
    
    def generate_prompt_id(self) -> str:
        """生成提示词ID"""
        return f"prompt-{uuid.uuid4().hex[:12]}"
    
    def generate_version_id(self) -> str:
        """生成提示词版本ID"""
        return f"ver-{uuid.uuid4().hex[:12]}"
    
    def generate_custom_id(self, prefix: str) -> str:
        """生成自定义前缀的ID"""
        if not prefix:
            raise ValueError("prefix 不能为空")
        return f"{prefix}-{uuid.uuid4().hex[:12]}"


# 全局单例
_id_generator: Optional[IDGenerator] = None


def get_id_generator() -> IDGenerator:
    """获取全局ID生成器实例"""
    global _id_generator
    if _id_generator is None:
        _id_generator = IDGenerator.get_instance()
    return _id_generator


def generate_session_id() -> str:
    """便捷函数：生成会话ID"""
    return get_id_generator().generate_session_id()


def generate_dialog_id() -> str:
    """便捷函数：生成对话ID"""
    return get_id_generator().generate_dialog_id()


def generate_message_id() -> str:
    """便捷函数：生成消息ID"""
    return get_id_generator().generate_message_id()


def generate_request_id() -> str:
    """便捷函数：生成请求ID"""
    return get_id_generator().generate_request_id()


def generate_call_id() -> str:
    """便捷函数：生成调用ID"""
    return get_id_generator().generate_call_id()


def generate_task_id() -> str:
    """便捷函数：生成任务ID"""
    return get_id_generator().generate_task_id()


def generate_group_id() -> str:
    """便捷函数：生成任务组ID"""
    return get_id_generator().generate_group_id()


def generate_tool_id() -> str:
    """便捷函数：生成工具ID"""
    return get_id_generator().generate_tool_id()


def generate_skill_id() -> str:
    """便捷函数：生成技能ID"""
    return get_id_generator().generate_skill_id()


def generate_project_id() -> str:
    """便捷函数：生成项目ID"""
    return get_id_generator().generate_project_id()


def generate_log_id(prefix: str = "log") -> str:
    """便捷函数：生成日志ID"""
    return get_id_generator().generate_log_id(prefix)


def generate_event_id() -> str:
    """便捷函数：生成事件ID"""
    return get_id_generator().generate_event_id()


def generate_record_id() -> str:
    """便捷函数：生成记录ID"""
    return get_id_generator().generate_record_id()


def generate_subscription_id() -> str:
    """便捷函数：生成订阅ID"""
    return get_id_generator().generate_subscription_id()


def generate_memory_id(memory_type: str = "mem") -> str:
    """便捷函数：生成记忆ID"""
    return get_id_generator().generate_memory_id(memory_type)


def generate_template_id() -> str:
    """便捷函数：生成模板ID"""
    return get_id_generator().generate_template_id()


def generate_config_id(config_type: str = "config") -> str:
    """便捷函数：生成配置ID"""
    return get_id_generator().generate_config_id(config_type)


def generate_frontend_history_id() -> str:
    """便捷函数：生成前台历史消息ID"""
    return get_id_generator().generate_frontend_history_id()


def generate_websocket_message_id() -> str:
    """便捷函数：生成WebSocket消息ID"""
    return get_id_generator().generate_websocket_message_id()


def generate_custom_id(prefix: str) -> str:
    """便捷函数：生成自定义ID"""
    return get_id_generator().generate_custom_id(prefix)


def generate_prompt_id() -> str:
    """便捷函数：生成提示词ID"""
    return get_id_generator().generate_prompt_id()


def generate_version_id() -> str:
    """便捷函数：生成版本ID"""
    return get_id_generator().generate_version_id()
