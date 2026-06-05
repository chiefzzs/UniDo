"""
L2b Memory and State Management - Data Models

数据模型定义：Session, Dialog, Message, TaskGroup, Task
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class Session:
    session_id: str
    project_id: str
    name: str
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        import inspect
        sig = inspect.signature(cls.__init__)
        params = sig.parameters.keys()
        filtered_data = {k: v for k, v in data.items() if k in params}
        return cls(**filtered_data)


@dataclass
class Dialog:
    dialog_id: str
    session_id: str
    dialog_type: str
    status: str = "active"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dialog':
        return cls(**data)


@dataclass
class Message:
    message_id: str
    dialog_id: str
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    platform_info: Dict[str, str] = field(default_factory=dict)  # 平台信息：{"os_type": "windows", "terminal_type": "powershell"}
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        # 处理旧数据兼容
        data = data.copy()
        if 'platform_info' not in data:
            data['platform_info'] = {}
        return cls(**data)


@dataclass
class TaskGroup:
    group_id: str
    session_id: str
    name: str
    status: str = "pending"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskGroup':
        return cls(**data)


@dataclass
class Task:
    task_id: str
    group_id: str
    name: str
    status: str = "pending"
    result: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(**data)
