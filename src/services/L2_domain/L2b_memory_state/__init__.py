"""
L2b Memory and State Management Service

L2b 记忆与状态管理服务负责管理会话、对话、消息及任务状态。

职责：
- Session管理：会话的创建、查询、更新、删除
- Dialog管理：对话的创建、查询、添加消息
- Message管理：消息的创建、查询
- TaskGroup/Task管理：任务组的创建、任务的添加和状态更新
- 记忆管理：短期记忆、长期记忆、记忆压缩

依赖 L1 层：
- L1b 持久化服务：用于存储和读取记忆数据
- L1d 事件系统：发布会话和记忆变更事件
"""

from .models import Session, Dialog, Message, TaskGroup, Task
from .api_log_models import APIRequestLog, WebSocketMessageLog
from .session_service import SessionService
from .dialog_service import DialogService
from .message_service import MessageService
from .task_group_service import TaskGroupService
from .task_service import TaskService
from .memory_service import MemoryService
from .api_log_service import APILogService, get_api_log_service
from .websocket_log_service import WebSocketLogService, get_websocket_log_service


def get_session_service() -> SessionService:
    return SessionService()


def get_dialog_service() -> DialogService:
    return DialogService()


def get_message_service() -> MessageService:
    return MessageService()


def get_task_group_service() -> TaskGroupService:
    return TaskGroupService()


def get_task_service() -> TaskService:
    return TaskService()


def get_memory_service() -> MemoryService:
    return MemoryService()


__all__ = [
    'Session', 'Dialog', 'Message', 'TaskGroup', 'Task',
    'APIRequestLog', 'WebSocketMessageLog',
    'SessionService', 'DialogService', 'MessageService',
    'TaskGroupService', 'TaskService', 'MemoryService', 'APILogService',
    'WebSocketLogService',
    'get_session_service', 'get_dialog_service', 'get_message_service',
    'get_task_group_service', 'get_task_service', 'get_memory_service',
    'get_api_log_service', 'get_websocket_log_service'
]
