"""
L2d LLM Execution Service - Execution Strategies

执行策略实现，支持录制和回放两种模式。

========== 数据流梳理 ==========

【回放模式数据流】
1. 上层服务（DialogManager/LLMExecutionService）调用 LoopbackStrategy.execute()
   - 传入 request 参数，包含：session_id, dialog_id, request_id（当前对话的ID）
   
2. LoopbackStrategy 从 store 读取回放记录
   - record 包含原始保存的：request_id, dialog_id, session_id
   
3. ID 替换逻辑（核心）：
   - session_id: 使用 request.session_id（当前会话ID）
   - dialog_id: 使用 request.dialog_id（当前对话ID）
   - request_id: 使用 request.request_id（当前请求ID）
   
4. 返回替换后的数据给上层服务
   - 上层服务使用这些ID发布事件到前端

【设计原则】
- 无状态设计：每次调用独立处理，不维护映射缓存
- 直接替换：使用传入的当前ID直接替换原始ID
- 简化接口：只保留必要的 execute 和 execute_stream 方法
"""

import time
from typing import Callable, Optional
from .interfaces import ExecutionStrategy, LLMExecutor


class RecordStrategy(ExecutionStrategy):
    """录制模式策略"""
    
    def execute(self, executor: LLMExecutor, request: dict) -> dict:
        return executor.execute(request)
    
    def execute_stream(self, executor: LLMExecutor, request: dict, 
                       on_chunk: Callable) -> dict:
        return executor.execute_stream(request, on_chunk)
    
    @property
    def mode(self) -> str:
        return "record"


class LoopbackStrategy(ExecutionStrategy):
    """回放模式策略 - 纯回放，不发起真实请求，不记录
    
    关键特性：
    - 使用传入的当前对话ID（session_id, dialog_id, request_id）替换回放记录中的原始ID
    - 无状态设计：每次调用独立处理，不维护映射缓存
    - 不生成新ID，只使用上层传入的ID
    """
    
    def __init__(self, store):
        self._store = store
    
    def _replace_ids(self, record: dict, request: dict) -> dict:
        """替换记录中的ID为当前对话ID"""
        # 获取当前对话的ID（来自上层服务）
        current_session_id = request.get('session_id', '')
        current_dialog_id = request.get('dialog_id', '')
        current_request_id = request.get('request_id', '')
        
        # 获取回放记录中的原始ID
        original_request_id = record.get('request_id', '')
        original_dialog_id = record.get('dialog_id', '')
        original_session_id = record.get('session_id', '')
        
        # 使用当前ID替换原始ID（当前ID优先）
        new_request_id = current_request_id or original_request_id
        new_dialog_id = current_dialog_id or original_dialog_id
        new_session_id = current_session_id or original_session_id
        
        print(f"🔄 [Loopback] ID替换: session={original_session_id}->{new_session_id}, dialog={original_dialog_id}->{new_dialog_id}, request={original_request_id}->{new_request_id}")
        
        return {
            'request_id': new_request_id,
            'dialog_id': new_dialog_id,
            'session_id': new_session_id
        }
    
    def execute(self, executor: LLMExecutor, request: dict) -> dict:
        if not self._store.has_more:
            raise RuntimeError("回放数据已用完，请切换到录制模式或添加更多回放数据")
        
        record = self._store.get_next()
        if record:
            ids = self._replace_ids(record, request)
            response_data = record.get('response', {})
            
            time.sleep(0.1)  # 确保前端有足够时间订阅事件
            
            return {
                'content': response_data.get('content', ''),
                'thinking': response_data.get('thinking', ''),
                'finish_reason': response_data.get('finish_reason', 'stop'),
                'tool_calls': response_data.get('tool_calls', []),
                'usage': response_data.get('usage', {}),
                **ids
            }
        
        raise RuntimeError("回放数据读取失败")
    
    def execute_stream(self, executor: LLMExecutor, request: dict,
                       on_chunk: Callable) -> dict:
        if not self._store.has_more:
            raise RuntimeError("回放数据已用完，请切换到录制模式或添加更多回放数据")

        record = self._store.get_next()
        if record:
            ids = self._replace_ids(record, request)
            response_data = record.get('response', {})
            content = response_data.get('content', '')

            # 模拟流式输出
            for i in range(0, len(content), 50):
                chunk = content[i:i+50]
                on_chunk({'delta': chunk, 'finish_reason': None})

            return {
                'content': content,
                'finish_reason': response_data.get('finish_reason', 'stop'),
                'tool_calls': response_data.get('tool_calls', []),
                'usage': response_data.get('usage', {}),
                **ids
            }

        raise RuntimeError("回放数据读取失败")
    
    def reset_mapping(self):
        """重置方法（保持接口兼容性，无状态设计下为空操作）"""
        print("🔄 [Loopback] reset_mapping called (无状态设计，无需操作)")
    
    @property
    def mode(self) -> str:
        return "loopback"