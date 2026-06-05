"""
L2d LLM Execution Service - Data Models

定义服务使用的数据模型。
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid


@dataclass(frozen=True)
class LLMExecutionRequest:
    """LLM执行请求模型"""
    dialog_id: str
    messages: List[Dict[str, str]]
    model_config_id: str
    stream: bool = False
    max_tokens: int = 2000
    temperature: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMExecutionResponse:
    """LLM执行响应模型"""
    request_id: str
    dialog_id: str
    content: str
    finish_reason: str
    thinking: str = ""              # 响应级思考（来自 response.thinking）
    reasoning: str = ""             # 流式思考（来自 delta.reasoning_content）
    tool_calls: Optional[List[Dict]] = None
    usage: Dict[str, int] = field(default_factory=dict)
    status: str = "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LLMCallRecord:
    """LLM调用记录模型"""
    call_id: str
    dialog_id: str
    model_config_id: str
    request_id: str  # 新增：LLM请求ID，用于回放时的ID映射
    request: Dict[str, Any]
    response: Dict[str, Any]
    status: str = "completed"
    duration_ms: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMCallRecord':
        # 向后兼容：如果数据中没有request_id字段，生成一个默认值
        if 'request_id' not in data:
            data['request_id'] = f"req-{uuid.uuid4().hex[:12]}"
        return cls(**data)


class ExecutionMode:
    """执行模式常量"""
    RECORD = "record"
    LOOPBACK = "loopback"
