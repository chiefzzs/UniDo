"""
L2d LLM Execution Service

LLM 执行服务负责执行 LLM 调用、处理流式响应、解析工具调用并协调工具执行。

架构特点：
- 策略模式支持录制/回放模式切换
- 依赖注入提高可测试性
- 接口抽象实现解耦
- 职责分离便于维护

依赖：
- L1c LLM客户端
- L1b 持久化服务
- L1d 事件系统
"""

from .models import (
    LLMExecutionRequest,
    LLMExecutionResponse,
    LLMCallRecord,
    ExecutionMode
)
from .execution_service import LLMExecutionService
from .strategies import RecordStrategy, LoopbackStrategy
from .stream_merger import StreamMerger
from .event_manager import DefaultEventPublisher
from .call_recorder import CallRecorder, PersistenceLoopbackStore


# 全局单例实例
_llm_execution_service: LLMExecutionService = None


def get_llm_execution_service() -> LLMExecutionService:
    """获取LLM执行服务单例实例"""
    global _llm_execution_service
    if _llm_execution_service is None:
        _llm_execution_service = LLMExecutionService(
            event_publisher=DefaultEventPublisher(),
            call_recorder=CallRecorder(),
            loopback_store=PersistenceLoopbackStore()
        )
    return _llm_execution_service


# 模式切换接口（兼容旧API）
def set_llm_mode(mode: str) -> bool:
    """设置LLM运行模式"""
    service = get_llm_execution_service()
    try:
        service.set_mode(mode)
        return True
    except Exception as e:
        print(f"❌ 设置LLM模式失败：{e}")
        return False


def get_llm_mode() -> str:
    """获取当前LLM运行模式"""
    service = get_llm_execution_service()
    return service.get_mode()


__all__ = [
    'LLMExecutionService',
    'LLMExecutionRequest',
    'LLMExecutionResponse',
    'LLMCallRecord',
    'ExecutionMode',
    'RecordStrategy',
    'LoopbackStrategy',
    'StreamMerger',
    'DefaultEventPublisher',
    'CallRecorder',
    'PersistenceLoopbackStore',
    'get_llm_execution_service',
    'set_llm_mode',
    'get_llm_mode'
]
