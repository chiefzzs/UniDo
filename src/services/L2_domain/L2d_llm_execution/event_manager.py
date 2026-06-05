"""
L2d LLM Execution Service - Event Manager

事件管理器，负责事件的发布和分发。
"""

from .interfaces import EventPublisher
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes


class DefaultEventPublisher(EventPublisher):
    """默认事件发布器"""
    
    def __init__(self, event_bus=None):
        self._event_bus = event_bus or EventBus.get_instance()
    
    def publish_request_sent(self, request_id: str, dialog_id: str, round_number: int = None, **kwargs):
        """发布请求发送事件"""
        # 必须显式传入session_id，不允许使用dialog_id作为默认值
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_request_sent: session_id 参数缺失，必须显式传入")
        
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_REQUEST_SENT,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                **kwargs,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_response_received(self, request_id: str, dialog_id: str, round_number: int = None, **kwargs):
        """发布响应接收事件"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_response_received: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_RESPONSE_RECEIVED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                **kwargs,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_thinking(self, request_id: str, dialog_id: str, thinking: str, round_number: int = None, **kwargs):
        """发布思考内容事件（流式片段，thinking字段）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_thinking: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_THINKING,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'thinking': thinking,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_reasoning(self, request_id: str, dialog_id: str, reasoning: str, round_number: int = None, **kwargs):
        """发布推理内容事件（流式片段，reasoning_content字段）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_reasoning: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_REASONING,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'reasoning': reasoning,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_stream_chunk(self, request_id: str, dialog_id: str, content: str, round_number: int = None, **kwargs):
        """发布流式响应片段事件（文本片段）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_stream_chunk: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_STREAM_CHUNK,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'content': content,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_call_failed(self, request_id: str, dialog_id: str, error: str, round_number: int = None, **kwargs):
        """发布调用失败事件"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_call_failed: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_CALL_FAILED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'error': error,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_call_completed(self, request_id: str, dialog_id: str, round_number: int = None, **kwargs):
        """发布LLM调用完成事件"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_call_completed: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_CALL_COMPLETED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                **kwargs,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    # ==================== 聚合事件（按SSE顺序发布） ====================
    
    def publish_text_completed(self, request_id: str, dialog_id: str, content: str, round_number: int = None, **kwargs):
        """发布文本聚合完成事件（llm.call_text_completed）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_text_completed: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_CALL_TEXT_COMPLETED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'content': content,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_thinking_completed(self, request_id: str, dialog_id: str, thinking: str, round_number: int = None, **kwargs):
        """发布思考聚合完成事件（llm.call_thinking_completed，thinking字段）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_thinking_completed: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_CALL_THINKING_COMPLETED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'thinking': thinking,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_reasoning_completed(self, request_id: str, dialog_id: str, reasoning: str, round_number: int = None, **kwargs):
        """发布推理聚合完成事件（llm.call_reasoning_completed，reasoning_content字段）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_reasoning_completed: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_CALL_REASONING_COMPLETED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'reasoning': reasoning,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
    
    def publish_tool_call_completed(self, request_id: str, dialog_id: str, tool_calls: list, round_number: int = None, **kwargs):
        """发布工具调用完成事件（llm.tool_call_completed）"""
        session_id = kwargs.pop('session_id', None)
        if session_id is None:
            raise ValueError("publish_tool_call_completed: session_id 参数缺失，必须显式传入")
        self._event_bus.publish(Event(
            event_type=EventTypes.LLM_TOOL_CALL_COMPLETED,
            payload={
                'request_id': request_id,
                'dialog_id': dialog_id,
                'round_number': round_number,
                'tool_calls': tool_calls,
                'source_component': 'L2_llm_execution',
                'source_service': 'LLMExecutionService',
                'session_id': session_id
            }
        ))
