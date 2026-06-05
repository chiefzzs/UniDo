"""
L2b Memory and State Management - API Log Models

API请求/响应和WebSocket消息的持久化数据模型
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class APIRequestLog:
    """API请求日志模型"""
    log_id: str
    request_id: str
    client_id: str
    method: str
    path: str
    query_params: Dict[str, Any] = field(default_factory=dict)
    body: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIRequestLog':
        return cls(**data)


@dataclass
class WebSocketMessageLog:
    """WebSocket消息日志模型"""
    log_id: str
    client_id: str
    session_id: Optional[str] = None
    message_type: str = ""
    direction: str = "inbound"  # inbound 或 outbound
    payload: Optional[Any] = None  # 可以是 dict 或 str
    error_message: Optional[str] = None
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessageLog':
        return cls(**data)
