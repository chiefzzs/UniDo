"""
L2d LLM Execution Service - Abstract Interfaces

定义服务的抽象接口，实现依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable


class LLMExecutor(ABC):
    """LLM执行器抽象接口"""
    
    @abstractmethod
    def execute(self, request: Dict) -> Dict:
        """执行同步LLM调用"""
        pass
    
    @abstractmethod
    def execute_stream(self, request: Dict, on_chunk: Callable) -> Dict:
        """执行流式LLM调用"""
        pass


class ExecutionStrategy(ABC):
    """执行策略抽象接口"""
    
    @abstractmethod
    def execute(self, executor: LLMExecutor, request: Dict) -> Dict:
        """执行请求"""
        pass
    
    @abstractmethod
    def execute_stream(self, executor: LLMExecutor, request: Dict, 
                       on_chunk: Callable) -> Dict:
        """执行流式请求"""
        pass
    
    @property
    @abstractmethod
    def mode(self) -> str:
        """获取当前模式"""
        pass


class LoopbackStore(ABC):
    """回放数据存储抽象接口"""
    
    @abstractmethod
    def load(self) -> List[Dict]:
        """加载回放数据"""
        pass
    
    @abstractmethod
    def get_next(self) -> Optional[Dict]:
        """获取下一条记录"""
        pass
    
    @abstractmethod
    def reset(self):
        """重置索引"""
        pass
    
    @property
    @abstractmethod
    def has_more(self) -> bool:
        """是否还有更多记录"""
        pass


class EventPublisher(ABC):
    """事件发布抽象接口"""
    
    @abstractmethod
    def publish_request_sent(self, request_id: str, dialog_id: str, **kwargs):
        """发布请求发送事件"""
        pass
    
    @abstractmethod
    def publish_response_received(self, request_id: str, dialog_id: str, **kwargs):
        """发布响应接收事件"""
        pass
    
    @abstractmethod
    def publish_thinking(self, request_id: str, dialog_id: str, thinking: str):
        """发布思考内容事件（流式片段，thinking字段）"""
        pass
    
    @abstractmethod
    def publish_reasoning(self, request_id: str, dialog_id: str, reasoning: str):
        """发布推理内容事件（流式片段，reasoning_content字段）"""
        pass
    
    @abstractmethod
    def publish_stream_chunk(self, request_id: str, dialog_id: str, content: str):
        """发布流式响应片段事件"""
        pass
    
    @abstractmethod
    def publish_call_failed(self, request_id: str, dialog_id: str, error: str):
        """发布调用失败事件"""
        pass
    
    @abstractmethod
    def publish_call_completed(self, request_id: str, dialog_id: str, **kwargs):
        """发布LLM调用完成事件"""
        pass
    
    # ==================== 聚合事件（按SSE顺序发布） ====================
    
    @abstractmethod
    def publish_text_completed(self, request_id: str, dialog_id: str, content: str):
        """发布文本聚合完成事件（llm.call_text_completed）"""
        pass
    
    @abstractmethod
    def publish_thinking_completed(self, request_id: str, dialog_id: str, thinking: str):
        """发布思考聚合完成事件（llm.call_thinking_completed，thinking字段）"""
        pass
    
    @abstractmethod
    def publish_reasoning_completed(self, request_id: str, dialog_id: str, reasoning: str):
        """发布推理聚合完成事件（llm.call_reasoning_completed，reasoning_content字段）"""
        pass
    
    @abstractmethod
    def publish_tool_call_completed(self, request_id: str, dialog_id: str, tool_calls: list):
        """发布工具调用完成事件（llm.tool_call_completed）"""
        pass
