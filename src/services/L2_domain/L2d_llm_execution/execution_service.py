"""
L2d LLM Execution Service - Execution Service

核心执行服务，负责执行LLM调用、处理流式响应、解析工具调用。
"""

import time
from typing import List, Optional, Dict, Any, Callable
from .interfaces import LLMExecutor
from .models import LLMExecutionResponse, LLMCallRecord, ExecutionMode
from .strategies import RecordStrategy, LoopbackStrategy
from .stream_merger import StreamMerger
from services.L1_infrastructure.L1a_id_generator.id_generator import generate_request_id, generate_call_id
from services.L1_infrastructure.L1c_llm.llm_client import LLMClient


# ============ 改进项1: 消息格式统一工具函数 ============
def normalize_user_message_content(content: Any) -> List[Dict]:
    """
    统一用户消息格式为数组格式。
    
    输入可能的格式：
    - 字符串: "用户输入内容"
    - 数组: [{"type": "text", "text": "内容"}]
    - 其他类型
    
    输出：统一格式 [{"type": "text", "text": "内容"}]
    """
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    elif isinstance(content, list):
        # 检查是否已经是正确格式
        for item in content:
            if isinstance(item, dict) and "type" in item and "text" in item:
                return content
        # 如果是其他数组格式，尝试转换
        return [{"type": "text", "text": str(item)} for item in content]
    else:
        return [{"type": "text", "text": str(content)}]


def normalize_all_messages(messages: List[Dict]) -> List[Dict]:
    """
    规范化所有消息的格式，确保user消息的content字段统一为数组格式。
    
    Args:
        messages: 原始消息列表
        
    Returns:
        规范化后的消息列表
    """
    normalized = []
    for msg in messages:
        role = msg.get('role')
        content = msg.get('content', '')
        
        if role == 'user':
            normalized.append({
                'role': role,
                'content': normalize_user_message_content(content)
            })
        else:
            normalized.append(msg)
    return normalized


# ============ 改进项2: finish_reason 判断工具函数 ============
def determine_finish_reason(response: Dict) -> str:
    """
    根据 content 和 tool_calls 正确判断 finish_reason。
    
    判断逻辑：
    1. 如果有 tool_calls 且不为空列表 -> "tool_calls"
    2. 如果有 content 且不为空字符串 -> "stop"
    3. 如果既没有内容也没有工具调用 -> "error"（异常情况）
    4. 其他情况保持原值
    
    Args:
        response: LLM响应字典
        
    Returns:
        正确的 finish_reason
    """
    has_content = bool(response.get('content', '').strip())
    tool_calls = response.get('tool_calls', [])
    has_tool_calls = isinstance(tool_calls, list) and len(tool_calls) > 0
    original_reason = response.get('finish_reason', '')
    
    # 优先检查工具调用
    if has_tool_calls:
        return "tool_calls"
    # 然后检查内容
    elif has_content:
        return "stop"
    # 如果两者都没有，标记为错误
    elif not has_content and not has_tool_calls:
        return "error"
    # 保持原值
    return original_reason


# ============ 改进项3: tool_calls 结构规范化 ============
def normalize_tool_calls(tool_calls: Optional[List[Dict]]) -> List[Dict]:
    """
    确保 tool_calls 中的每个调用都包含 index 字段。
    
    Args:
        tool_calls: 工具调用列表
        
    Returns:
        规范化后的工具调用列表（确保每个调用都有index）
    """
    if not isinstance(tool_calls, list):
        return []
    
    normalized = []
    for idx, tc in enumerate(tool_calls):
        # 确保 index 字段存在
        if 'index' not in tc:
            tc = {**tc, 'index': idx}
        # 如果有 function 字段，也确保里面的结构完整
        if 'function' in tc and isinstance(tc['function'], dict):
            tc['function'] = tc['function']
        normalized.append(tc)
    
    return normalized


# ============ 改进项4: 异常终止检测 ============
def detect_abnormal_termination(response: Dict, llm_request: Dict = None) -> Dict:
    """
    检测LLM调用是否异常终止。
    
    检测条件：
    1. finish_reason 为 "stop" 但 content 为空
    2. finish_reason 为 "stop" 但存在 tool_calls
    3. finish_reason 为 "tool_calls" 但 tool_calls 为空
    4. 响应中存在明显错误标识
    
    Args:
        response: LLM响应字典
        llm_request: 原始LLM请求（可选，用于更详细的错误分析）
        
    Returns:
        检测结果字典，包含：
        - is_abnormal: 是否异常
        - reason: 异常原因描述
        - suggestion: 建议的处理方式
    """
    content = response.get('content', '')
    tool_calls = response.get('tool_calls', [])
    finish_reason = response.get('finish_reason', '')
    
    has_content = bool(content.strip())
    has_tool_calls = isinstance(tool_calls, list) and len(tool_calls) > 0
    
    # 检测逻辑
    if finish_reason == "stop" and not has_content and not has_tool_calls:
        return {
            'is_abnormal': True,
            'reason': "finish_reason 为 'stop' 但没有内容输出，可能是 LLM 返回异常",
            'suggestion': "检查 LLM 服务状态，验证 API 调用是否成功"
        }
    
    if finish_reason == "stop" and has_tool_calls:
        return {
            'is_abnormal': True,
            'reason': "finish_reason 为 'stop' 但存在工具调用，状态不一致",
            'suggestion': "检查 finish_reason 判断逻辑，确保工具调用时返回 'tool_calls'"
        }
    
    if finish_reason == "tool_calls" and not has_tool_calls:
        return {
            'is_abnormal': True,
            'reason': "finish_reason 为 'tool_calls' 但工具调用列表为空",
            'suggestion': "检查工具调用解析逻辑，验证 LLM 返回格式"
        }
    
    if response.get('error') or (isinstance(response, dict) and 'error' in response):
        return {
            'is_abnormal': True,
            'reason': f"LLM 调用返回错误: {response.get('error', '未知错误')}",
            'suggestion': "检查 LLM 配置和网络连接"
        }
    
    # 检查 token 使用情况
    usage = response.get('usage', {})
    completion_tokens = usage.get('completion_tokens', 0)
    if finish_reason == "stop" and completion_tokens < 10 and not has_tool_calls:
        return {
            'is_abnormal': True,
            'reason': f"完成 token 数过少 ({completion_tokens})，可能被截断或返回异常",
            'suggestion': "检查 max_tokens 设置，增加输出限制"
        }
    
    return {
        'is_abnormal': False,
        'reason': "正常",
        'suggestion': None
    }


class LLMExecutionService:
    """LLM执行服务核心类"""
    
    def __init__(self, llm_client=None, event_publisher=None, 
                 call_recorder=None, loopback_store=None):
        self._llm_client = llm_client or LLMClient()
        self._event_publisher = event_publisher
        # 默认创建 CallRecorder，确保录制模式下能保存调用记录
        from .call_recorder import CallRecorder, PersistenceLoopbackStore
        self._call_recorder = call_recorder or CallRecorder()
        # 默认创建 LoopbackStore，确保回放模式下能读取数据
        self._loopback_store = loopback_store or PersistenceLoopbackStore()
        
        self._strategy = RecordStrategy()
        self._current_mode = ExecutionMode.RECORD
        
        mode_display = "📹 录制模式" if self._current_mode == ExecutionMode.RECORD else "🔄 回放模式"
        print(f"🤖 L2大模型调用服务初始化完成")
        print(f"   当前模式: {mode_display} ({self._current_mode})")
    
    def set_strategy(self, strategy):
        """设置执行策略"""
        self._strategy = strategy
        self._current_mode = strategy.mode
    
    def set_mode(self, mode: str):
        """设置执行模式"""
        old_mode = self._current_mode
        
        if mode == ExecutionMode.LOOPBACK:
            if self._loopback_store:
                self._loopback_store.load()
                # 重置索引计数器，确保每次切换到回放模式时都从头开始回放
                self._loopback_store.reset()
            self._strategy = LoopbackStrategy(self._loopback_store)
            # 重置 ID 映射表（清理后台计数器）
            self._strategy.reset_mapping()
            self._current_mode = ExecutionMode.LOOPBACK
        else:
            self._strategy = RecordStrategy()
            self._current_mode = ExecutionMode.RECORD
        
        old_display = "📹 录制模式" if old_mode == ExecutionMode.RECORD else "🔄 回放模式"
        new_display = "📹 录制模式" if self._current_mode == ExecutionMode.RECORD else "🔄 回放模式"
        print(f"🔄 LLM 模式切换：{old_display} -> {new_display}")
        
        if self._call_recorder:
            self._call_recorder.set_mode(self._current_mode)
        
        # 同步设置 LLMClient 的模式，避免回放模式下保存调用记录
        if self._llm_client:
            self._llm_client.set_mode(self._current_mode)
    
    def get_mode(self) -> str:
        """获取当前模式"""
        return self._current_mode
    
    def execute(self, session_id: str, model_config_id: str, messages: List[Dict],
                max_tokens: int = 4096, temperature: float = 0.7,
                stream: bool = False, tools: Optional[List[Dict]] = None,
                dialog_id: str = None, round_number: int = None) -> LLMExecutionResponse:
        """
        执行LLM调用（简化接口，供上层服务调用）
        
        Args:
            session_id: 会话ID
            model_config_id: 模型配置ID
            messages: 消息列表
            max_tokens: 最大token数
            temperature: 温度参数
            stream: 是否流式调用
            tools: 工具定义列表
            dialog_id: 对话ID（如果不传则使用session_id）
            round_number: 轮次编号（用于关联到特定轮次）
        
        Returns:
            LLMExecutionResponse对象
        """
        # 如果没有传入 dialog_id，则使用 session_id（保持向后兼容）
        actual_dialog_id = dialog_id if dialog_id else session_id
        
        return self.execute_llm(
            dialog_id=actual_dialog_id,
            model_config_id=model_config_id,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            tools=tools,
            round_number=round_number,
            session_id=session_id
        )
    
    def execute_llm(self, dialog_id: str, model_config_id: str, messages: List[Dict],
                    model_name: str = None, api_type: str = None, 
                    api_address: str = None, api_key: str = None,
                    temperature: float = 0.7, max_tokens: int = 2000,
                    tools: Optional[List[Dict]] = None, 
                    stream: bool = False,
                    round_number: int = None,
                    session_id: str = None) -> LLMExecutionResponse:
        
        # 必须显式传入 session_id，不允许使用 dialog_id 作为默认值
        if session_id is None:
            raise ValueError("execute_llm: session_id 参数缺失，必须显式传入")
        
        # 生成统一的request_id（所有后续事件都使用这个ID）
        request_id = generate_request_id()
        
        # ============ 改进项1: 规范化消息格式 ============
        normalized_messages = normalize_all_messages(messages)
        
        llm_request = self._build_llm_request(
            messages=normalized_messages,  # 使用规范化后的消息
            model_name=model_name,
            api_type=api_type,
            api_address=api_address,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools
        )
        
        start_time = time.time()
        
        try:
            # 先发布请求发送事件（必须在执行前发布，用于创建ResponseBlock）
            print(f"[LLMExecution] 准备发布 request_sent 事件: request_id={request_id}, dialog_id={dialog_id}, session_id={session_id}")
            self._publish_request_sent(request_id, dialog_id, model_config_id, messages, tools, stream, round_number, session_id)
            print(f"[LLMExecution] request_sent 事件发布成功")
            
            if stream:
                response = self._execute_stream(
                    request_id=request_id,
                    dialog_id=dialog_id,
                    model_config_id=model_config_id,
                    llm_request=llm_request,
                    round_number=round_number,
                    session_id=session_id
                )
            else:
                response = self._execute_sync(
                    request_id=request_id,
                    dialog_id=dialog_id,
                    model_config_id=model_config_id,
                    llm_request=llm_request,
                    round_number=round_number,
                    session_id=session_id
                )
            
            # 有效request_id就是我们生成的request_id（保持统一）
            effective_request_id = request_id
            
            duration_ms = int((time.time() - start_time) * 1000)
            # 使用统一的request_id保存记录
            self._save_call_record(request_id, dialog_id, model_config_id, llm_request, response, duration_ms)
            # 使用统一的request_id发布响应事件
            self._publish_response_received(request_id, dialog_id, response, round_number, session_id)
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._save_failed_record(request_id, dialog_id, model_config_id, llm_request, str(e), duration_ms)
            self._publish_call_failed(request_id, dialog_id, str(e), round_number, session_id)
            
            return LLMExecutionResponse(
                request_id=request_id,
                dialog_id=dialog_id,
                content=f"Error: {str(e)}",
                finish_reason="error",
                status="failed"
            )
    
    def _execute_sync(self, request_id: str, dialog_id: str, model_config_id: str, 
                      llm_request: dict, round_number: int = None, session_id: str = None) -> LLMExecutionResponse:
        """执行同步调用"""
        # 必须显式传入 session_id，不允许使用 dialog_id 作为默认值
        if session_id is None:
            raise ValueError("_execute_sync: session_id 参数缺失，必须显式传入")
        
        executor = _LLMClientAdapter(self._llm_client, dialog_id, model_config_id)
        # 将dialog_id、request_id和session_id添加到llm_request中，以便策略可以使用它们
        # request_id 用于确保回放模式下返回的 request_id 与发布事件时使用的一致
        # session_id 用于确保回放模式下返回的 session_id 与发布事件时使用的一致
        llm_request_with_ids = {**llm_request, 'dialog_id': dialog_id, 'request_id': request_id, 'session_id': session_id}
        
        llm_response = self._strategy.execute(executor, llm_request_with_ids)
        
        # 使用统一的request_id（由L2层生成，保持所有事件ID一致）
        effective_request_id = request_id
        # 使用传入的dialog_id（保持与上层一致，不使用策略返回的dialog_id）
        effective_dialog_id = dialog_id
        
        thinking = llm_response.get('thinking', '')
        reasoning = llm_response.get('reasoning', '')
        content = llm_response.get('content', '')
        
        # ============ 改进项3: 规范化 tool_calls 结构 ============
        normalized_tool_calls = normalize_tool_calls(llm_response.get('tool_calls'))
        
        # ============ 改进项2: 正确判断 finish_reason ============
        # 构建用于判断的响应字典
        response_for_finish_reason = {
            'content': content,
            'tool_calls': normalized_tool_calls,
            'finish_reason': llm_response.get('finish_reason', '')
        }
        correct_finish_reason = determine_finish_reason(response_for_finish_reason)
        
        # ============ 改进项4: 检测异常终止 ============
        abnormal_result = detect_abnormal_termination({
            'content': content,
            'tool_calls': normalized_tool_calls,
            'finish_reason': correct_finish_reason,
            'usage': llm_response.get('usage', {})
        }, llm_request)
        
        if abnormal_result['is_abnormal']:
            print(f"⚠️ [LLMExecution] 检测到异常终止: {abnormal_result['reason']}")
            print(f"   建议: {abnormal_result['suggestion']}")
        
        if self._event_publisher:
            # 非流式模式：发布聚合事件（避免前台重复处理）
            # 按照文档约定顺序发布：思考(thinking) → 推理(reasoning) → 文本(text) → 工具(tool)
            
            # 1. 发布thinking聚合完成事件
            if thinking:
                self._event_publisher.publish_thinking_completed(
                    request_id=effective_request_id,
                    dialog_id=effective_dialog_id,
                    thinking=thinking,
                    round_number=round_number,
                    session_id=session_id
                )
            
            # 2. 发布reasoning聚合完成事件
            if reasoning:
                self._event_publisher.publish_reasoning_completed(
                    request_id=effective_request_id,
                    dialog_id=effective_dialog_id,
                    reasoning=reasoning,
                    round_number=round_number,
                    session_id=session_id
                )
            
            # 3. 发布文本聚合完成事件
            if content:
                self._event_publisher.publish_text_completed(
                    request_id=effective_request_id,
                    dialog_id=effective_dialog_id,
                    content=content,
                    round_number=round_number,
                    session_id=session_id
                )
            
            # 4. 发布工具调用完成事件（如果有工具调用）
            if normalized_tool_calls:
                self._event_publisher.publish_tool_call_completed(
                    request_id=effective_request_id,
                    dialog_id=effective_dialog_id,
                    tool_calls=normalized_tool_calls,
                    round_number=round_number,
                    session_id=session_id
                )
            
            # 发布调用完成事件（使用正确的finish_reason）
            self._event_publisher.publish_call_completed(
                request_id=effective_request_id,
                dialog_id=effective_dialog_id,
                round_number=round_number,
                content=content,
                finish_reason=correct_finish_reason,
                session_id=session_id
            )
        
        # 确定最终状态
        status = "completed"
        if abnormal_result['is_abnormal'] or correct_finish_reason == "error":
            status = "abnormal"
        
        return LLMExecutionResponse(
            request_id=effective_request_id,
            dialog_id=effective_dialog_id,
            content=content,
            thinking=thinking,
            reasoning=reasoning,
            finish_reason=correct_finish_reason,  # 使用正确的finish_reason
            tool_calls=normalized_tool_calls,      # 使用规范化的tool_calls
            usage=llm_response.get('usage', {}),
            status=status  # 根据异常检测结果设置状态
        )
    
    def _execute_stream(self, request_id: str, dialog_id: str, model_config_id: str,
                        llm_request: dict, round_number: int = None, session_id: str = None) -> LLMExecutionResponse:
        """执行流式调用"""
        # 必须显式传入 session_id，不允许使用 dialog_id 作为默认值
        if session_id is None:
            raise ValueError("_execute_stream: session_id 参数缺失，必须显式传入")
        
        merger = StreamMerger()
        executor = _LLMClientAdapter(self._llm_client, dialog_id, model_config_id)
        
        # 将dialog_id、request_id和session_id添加到llm_request中，以便策略可以使用它们
        llm_request_with_ids = {**llm_request, 'dialog_id': dialog_id, 'request_id': request_id, 'session_id': session_id}
        
        # 在回放模式下，流式回调中先使用原始request_id和dialog_id，后续会被替换
        def on_chunk(chunk: Dict):
            forward_data = merger.process_chunk(chunk)
            if forward_data and self._event_publisher:
                # 根据数据类型发布不同事件
                data_type = forward_data.get('type', 'content')
                if data_type == 'thinking':
                    # reasoning_content 流式思考
                    self._event_publisher.publish_reasoning(
                        request_id=request_id,
                        dialog_id=dialog_id,
                        reasoning=forward_data['content'],
                        round_number=round_number,
                        session_id=session_id
                    )
                elif data_type == 'content':
                    self._event_publisher.publish_stream_chunk(
                        request_id=request_id,
                        dialog_id=dialog_id,
                        content=forward_data['content'],
                        round_number=round_number,
                        session_id=session_id
                    )
        
        llm_response = self._strategy.execute_stream(executor, llm_request_with_ids, on_chunk)
        
        # 使用统一的request_id（由L2层生成，保持所有事件ID一致）
        effective_request_id = request_id
        # 使用传入的dialog_id（保持与上层一致，不使用策略返回的dialog_id）
        effective_dialog_id = dialog_id
        
        final = merger.get_final_message()
        
        # 区分两种思考内容：
        # reasoning_content: 流式思考（来自 delta.reasoning_content）
        # thinking: 响应级思考（来自 response.thinking）
        reasoning_content = merger.reasoning_content or ''
        thinking = llm_response.get('thinking', '')
        content = final['content'] or llm_response.get('content', '')
        tool_calls = llm_response.get('tool_calls') or final.get('tool_calls', [])
        
        # ============ 改进项3: 规范化 tool_calls 结构 ============
        normalized_tool_calls = normalize_tool_calls(tool_calls)
        
        # ============ 改进项2: 正确判断 finish_reason ============
        raw_finish_reason = llm_response.get('finish_reason') or merger.finish_reason or "stop"
        response_for_finish_reason = {
            'content': content,
            'tool_calls': normalized_tool_calls,
            'finish_reason': raw_finish_reason
        }
        correct_finish_reason = determine_finish_reason(response_for_finish_reason)
        
        # ============ 改进项4: 检测异常终止 ============
        abnormal_result = detect_abnormal_termination({
            'content': content,
            'tool_calls': normalized_tool_calls,
            'finish_reason': correct_finish_reason,
            'usage': llm_response.get('usage', {})
        }, llm_request)
        
        if abnormal_result['is_abnormal']:
            print(f"⚠️ [LLMExecution] 检测到异常终止: {abnormal_result['reason']}")
            print(f"   建议: {abnormal_result['suggestion']}")
        
        # 按SSE顺序发布聚合事件（使用有效的request_id和dialog_id）
        if self._event_publisher:
            # 1. 文本聚合完成
            self._event_publisher.publish_text_completed(
                request_id=effective_request_id,
                dialog_id=effective_dialog_id,
                content=content,
                round_number=round_number,
                session_id=session_id
            )
            # 2. reasoning_content 推理聚合完成
            if reasoning_content:
                self._event_publisher.publish_reasoning_completed(
                    request_id=effective_request_id,
                    dialog_id=effective_dialog_id,
                    reasoning=reasoning_content,
                    round_number=round_number,
                    session_id=session_id
                )
            # 3. thinking 思考聚合完成
            if thinking:
                self._event_publisher.publish_thinking_completed(
                    request_id=effective_request_id,
                    dialog_id=effective_dialog_id,
                    thinking=thinking,
                    round_number=round_number,
                    session_id=session_id
                )
            # 4. 工具调用完成（使用规范化的tool_calls）
            self._event_publisher.publish_tool_call_completed(
                request_id=effective_request_id,
                dialog_id=effective_dialog_id,
                tool_calls=normalized_tool_calls,
                round_number=round_number,
                session_id=session_id
            )
            # 5. 调用完成（使用正确的finish_reason）
            self._event_publisher.publish_call_completed(
                request_id=effective_request_id,
                dialog_id=effective_dialog_id,
                round_number=round_number,
                content=content,
                thinking=thinking,
                reasoning=reasoning_content,
                tool_calls=normalized_tool_calls,
                finish_reason=correct_finish_reason,
                session_id=session_id
            )
        
        # 确定最终状态
        status = "completed"
        if abnormal_result['is_abnormal'] or correct_finish_reason == "error":
            status = "abnormal"
        
        return LLMExecutionResponse(
            request_id=effective_request_id,
            dialog_id=effective_dialog_id,
            content=content,
            thinking=thinking,
            reasoning=reasoning_content,
            finish_reason=correct_finish_reason,  # 使用正确的finish_reason
            tool_calls=normalized_tool_calls,      # 使用规范化的tool_calls
            status=status  # 根据异常检测结果设置状态
        )
    
    def _build_llm_request(self, **kwargs) -> dict:
        """构建LLM请求字典"""
        return {
            'model_name': kwargs.get('model_name') or "default",
            'messages': kwargs.get('messages'),
            'api_type': kwargs.get('api_type') or "openai",
            'api_address': kwargs.get('api_address') or "http://localhost/v1",
            'api_key': kwargs.get('api_key') or "demo",
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2000),
            'tools': kwargs.get('tools') or []
        }
    
    def _save_call_record(self, request_id: str, dialog_id: str, model_config_id: str,
                          llm_request: dict, response: LLMExecutionResponse, duration_ms: int):
        """保存调用记录"""
        if not self._call_recorder or self._current_mode == ExecutionMode.LOOPBACK:
            return
        
        record = LLMCallRecord(
            call_id=generate_call_id(),
            dialog_id=dialog_id,
            model_config_id=model_config_id,
            request_id=request_id,  # 保存原始request_id用于回放映射
            request=llm_request,
            response={
                'content': response.content,
                'thinking': response.thinking,
                'finish_reason': response.finish_reason,
                'tool_calls': response.tool_calls,
                'usage': response.usage
            },
            status="completed",
            duration_ms=duration_ms
        )
        self._call_recorder.save(record)
    
    def _save_failed_record(self, request_id: str, dialog_id: str, model_config_id: str,
                            llm_request: dict, error: str, duration_ms: int):
        """保存失败记录"""
        if not self._call_recorder or self._current_mode == ExecutionMode.LOOPBACK:
            return
        
        record = LLMCallRecord(
            call_id=generate_call_id(),
            dialog_id=dialog_id,
            model_config_id=model_config_id,
            request_id=request_id,
            request=llm_request,
            response={'error': error},
            status="failed",
            duration_ms=duration_ms
        )
        self._call_recorder.save(record)
    
    def _publish_request_sent(self, request_id: str, dialog_id: str, model_config_id: str,
                              messages: List[Dict], tools: Optional[List[Dict]], stream: bool, 
                              round_number: int = None, session_id: str = None):
        """发布请求发送事件"""
        if not self._event_publisher:
            return
        self._event_publisher.publish_request_sent(
            request_id=request_id,
            dialog_id=dialog_id,
            round_number=round_number,
            model_config_id=model_config_id,
            messages=messages,
            tools=tools,
            stream=stream,
            session_id=session_id
        )
    
    def _publish_response_received(self, request_id: str, dialog_id: str, response: LLMExecutionResponse, round_number: int = None, session_id: str = None):
        """发布响应接收事件"""
        if not self._event_publisher:
            return
        self._event_publisher.publish_response_received(
            request_id=request_id,
            dialog_id=dialog_id,
            round_number=round_number,
            content=response.content,
            finish_reason=response.finish_reason,
            tool_calls=response.tool_calls,
            usage=response.usage,
            session_id=session_id
        )
    
    def _publish_call_failed(self, request_id: str, dialog_id: str, error: str, round_number: int = None, session_id: str = None):
        """发布调用失败事件"""
        if not self._event_publisher:
            return
        self._event_publisher.publish_call_failed(request_id, dialog_id, error, round_number, session_id=session_id)
    
    def execute_stream(self, session_id: str, model_config_id: str, messages: List[Dict],
                       on_chunk: Callable, max_tokens: int = 4096, 
                       temperature: float = 0.7) -> LLMExecutionResponse:
        """
        执行流式LLM调用（简化接口，供上层服务调用）
        
        Args:
            session_id: 会话ID（用作dialog_id）
            model_config_id: 模型配置ID
            messages: 消息列表
            on_chunk: 回调函数，处理每个chunk
            max_tokens: 最大token数
            temperature: 温度参数
        
        Returns:
            LLMExecutionResponse对象
        """
        request_id = generate_request_id()
        
        llm_request = self._build_llm_request(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=[]
        )
        
        self._publish_request_sent(request_id, session_id, model_config_id, messages, [], True, None, session_id)
        
        start_time = time.time()
        
        try:
            response = self._execute_stream(
                request_id=request_id,
                dialog_id=session_id,
                model_config_id=model_config_id,
                llm_request=llm_request,
                session_id=session_id
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            self._save_call_record(request_id, session_id, model_config_id, llm_request, response, duration_ms)
            self._publish_response_received(request_id, session_id, response)
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._save_failed_record(request_id, session_id, model_config_id, llm_request, str(e), duration_ms)
            self._publish_call_failed(request_id, session_id, str(e))
            
            return LLMExecutionResponse(
                request_id=request_id,
                dialog_id=session_id,
                content=f"Error: {str(e)}",
                finish_reason="error",
                status="failed"
            )
    
    def list_call_records(self, dialog_id: str = None) -> list:
        """
        列出LLM调用记录
        
        Args:
            dialog_id: 可选的dialog_id过滤条件
        
        Returns:
            调用记录列表
        """
        if not self._call_recorder:
            return []
        return self._call_recorder.list(dialog_id=dialog_id)
    
    def parse_tool_calls(self, content: str) -> list:
        """
        解析工具调用
        
        Args:
            content: 包含工具调用的内容（JSON格式字符串）
        
        Returns:
            工具调用列表
        """
        import json
        try:
            data = json.loads(content)
            if isinstance(data, dict) and 'tool_calls' in data:
                return data['tool_calls']
            return []
        except json.JSONDecodeError:
            return []


class _LLMClientAdapter(LLMExecutor):
    """LLM客户端适配器"""
    
    def __init__(self, client: LLMClient, session_id: str, model_config_id: str):
        self._client = client
        self._session_id = session_id
        self._model_config_id = model_config_id
    
    def execute(self, request: dict) -> dict:
        """同步调用"""
        # 将dict转换为LLMRequest对象
        from services.L1_infrastructure.L1c_llm.llm_client import LLMRequest
        llm_request = LLMRequest(
            model_name=request.get('model_name', 'default'),
            messages=request.get('messages', []),
            temperature=request.get('temperature', 0.7),
            max_tokens=request.get('max_tokens', 2048),
            stream=request.get('stream', False),
            api_type=request.get('api_type', 'openai'),
            api_address=request.get('api_address', 'http://localhost/v1'),
            api_key=request.get('api_key', 'demo'),
            tools=request.get('tools', []),
            tool_choice=request.get('tool_choice')
        )
        
        response = self._client.send_request(
            llm_request,
            session_id=self._session_id,
            model_config_id=self._model_config_id
        )
        
        return {
            'content': response.content,
            'thinking': response.thinking,
            'finish_reason': response.finish_reason,
            'tool_calls': response.tool_calls,
            'usage': response.usage
        }
    
    def execute_stream(self, request: dict, on_chunk: Callable) -> dict:
        """流式调用"""
        # 将dict转换为LLMRequest对象
        from services.L1_infrastructure.L1c_llm.llm_client import LLMRequest
        llm_request = LLMRequest(
            model_name=request.get('model_name', 'default'),
            messages=request.get('messages', []),
            temperature=request.get('temperature', 0.7),
            max_tokens=request.get('max_tokens', 2048),
            stream=True,
            api_type=request.get('api_type', 'openai'),
            api_address=request.get('api_address', 'http://localhost/v1'),
            api_key=request.get('api_key', 'demo'),
            tools=request.get('tools', []),
            tool_choice=request.get('tool_choice')
        )
        
        final_content = []
        def on_stream_chunk(chunk):
            on_chunk({
                'delta': chunk.delta,
                'chunk_type': chunk.chunk_type,
                'finish_reason': chunk.finish_reason,
                'index': chunk.index,
                'tool_calls': chunk.tool_calls
            })
            if chunk.delta:
                final_content.append(chunk.delta)
        
        response = self._client.send_stream_request(
            llm_request,
            on_chunk=on_stream_chunk,
            session_id=self._session_id,
            model_config_id=self._model_config_id
        )
        
        return {
            'content': response.content,
            'thinking': response.thinking,
            'finish_reason': response.finish_reason,
            'tool_calls': response.tool_calls,
            'usage': response.usage
        }
