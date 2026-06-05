"""
EventWebSocketPlugin - WebSocket事件订阅插件

订阅 EventBus 并将事件推送到所有WebSocket连接。
这是一个独立的插件，可以单独启用/禁用。

职责：
1. 订阅EventBus，接收所有事件
2. 将事件推送到所有WebSocket连接（根据流式/非流式模式过滤）
3. 处理会话切换事件，触发历史消息回放
4. 缓存WebSocket消息到内存，支持历史回放

特性：
- 异步消息推送，不阻塞事件处理
- 消息去重，避免重复推送
- 会话切换时的历史消息回放
- 线程安全的连接管理
- 流式/非流式模式下的事件过滤（避免前台重复处理）

---
接口数据格式定义（WebSocket消息格式）
---

【后端推送消息格式 - Event类型】
{
  "version": "1.0",
  "type": "event",
  "action": "event.type.name",  // 事件类型
  "message_id": "msg-xxx",      // 消息唯一ID
  "session_id": "sess-xxx",     // 会话ID
  "timestamp": "2026-05-25T15:35:59.741822",  // ISO8601格式时间戳
  "data": { ... },              // 事件数据，根据action不同而变化
  "metadata": {
    "source_component": "component_name"  // 事件来源组件
  }
}

【事件分类】
- 流式事件（实时片段）：llm.stream_chunk, llm.thinking, llm.reasoning
- 聚合事件（汇总完成）：llm.call_text_completed, llm.call_thinking_completed, 
                       llm.call_reasoning_completed, llm.tool_call_completed

【转发规则】
- 流式模式：转发流式事件，不转发聚合事件（避免重复）
- 非流式模式：转发聚合事件，不转发流式事件（避免重复）
- 其他事件（如tool.call_started, dialog.created等）：始终转发

【发往前台的消息类型列表】

1. session.created - 会话创建事件
{
  "version": "1.0",
  "type": "event",
  "action": "session.created",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "session_id": "sess-xxx",
    "project_id": "proj-xxx"
  },
  "metadata": { "source_component": null }
}

2. message.created - 用户消息创建事件
{
  "version": "1.0",
  "type": "event",
  "action": "message.created",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "dialog_id": "dialog-xxx",
    "message_id": "msg-xxx",
    "role": "user",
    "content": "用户输入内容",
    "session_id": "sess-xxx"
  },
  "metadata": { "source_component": null }
}

3. llm.request_sent - LLM请求发送事件
{
  "version": "1.0",
  "type": "event",
  "action": "llm.request_sent",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "request_id": "req-xxx",
    "dialog_id": "sess-xxx",
    "model_config_id": "default",
    "messages": [...],
    "stream": false
  },
  "metadata": { "source_component": "L2_llm_execution" }
}

4. llm.response_received - LLM响应接收事件
{
  "version": "1.0",
  "type": "event",
  "action": "llm.response_received",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "request_id": "req-xxx",
    "dialog_id": "sess-xxx",
    "content": "助手回复内容",
    "finish_reason": "stop",
    "tool_calls": [],
    "usage": {},
    "source_component": "L2_llm_execution",
    "source_service": "LLMExecutionService",
    "session_id": "sess-xxx"
  },
  "metadata": { "source_component": "L2_llm_execution" }
}

5. llm.response_classified - LLM响应分类事件
{
  "version": "1.0",
  "type": "event",
  "action": "llm.response_classified",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "request_id": "req-xxx",
    "intent": "tool_call|direct_answer|summary",
    "confidence": 0.95,
    "session_id": "sess-xxx"
  },
  "metadata": { "source_component": "L2_llm_execution" }
}

6. tool.call_started - 工具调用开始事件
{
  "version": "1.0",
  "type": "event",
  "action": "tool.call_started",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "tool_name": "tool_name",
    "tool_params": { ... },
    "request_id": "req-xxx",
    "session_id": "sess-xxx"
  },
  "metadata": { "source_component": "L2_tool_execution" }
}

7. tool.execution_output_end - 工具执行输出结束事件
{
  "version": "1.0",
  "type": "event",
  "action": "tool.execution_output_end",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "tool_name": "tool_name",
    "output": "工具执行结果",
    "request_id": "req-xxx",
    "session_id": "sess-xxx"
  },
  "metadata": { "source_component": "L2_tool_execution" }
}

8. tool.call_completed - 工具调用完成事件
{
  "version": "1.0",
  "type": "event",
  "action": "tool.call_completed",
  "message_id": "msg-xxx",
  "session_id": "sess-xxx",
  "timestamp": "ISO8601",
  "data": {
    "tool_name": "tool_name",
    "success": true,
    "result": { ... },
    "request_id": "req-xxx",
    "session_id": "sess-xxx"
  },
  "metadata": { "source_component": "L2_tool_execution" }
}

【后端推送消息格式 - 历史回放类型】

// 回放开始
{
  "version": "1.0",
  "type": "replay_start",
  "action": "history.replay.started",
  "session_id": "sess-xxx",
  "timestamp": "2026-05-25T16:46:22.041419",
  "data": {
    "total_messages": 6  // 待回放消息总数
  }
}

// 回放消息（逐条推送）- 注意：data字段包含原始完整消息payload
{
  "version": "1.0",
  "type": "replay_message",
  "action": "history.replay.message",
  "session_id": "sess-xxx",
  "timestamp": "2026-05-25T15:35:59.741822",
  "data": {  // 原始WebSocket消息payload（与event类型格式完全一致）
    "version": "1.0",
    "type": "event",
    "action": "message.created",
    "message_id": "msg-xxx",
    "session_id": "sess-xxx",
    "timestamp": "ISO8601",
    "data": { ... },
    "metadata": { ... }
  },
  "replay": true,
  "replay_index": 0,      // 当前消息索引（从0开始）
  "replay_total": 6       // 总消息数
}

// 回放完成
{
  "version": "1.0",
  "type": "replay_complete",
  "action": "history.replay.complete",
  "session_id": "sess-xxx",
  "timestamp": "2026-05-25T16:46:22.xxx",
  "data": {
    "total_messages": 6  // 实际回放消息数
  }
}

【前端发送消息格式】
{
  "action": "action_name",  // send_message, switch_session, ping
  "data": { ... }           // 动作参数
}

// switch_session 示例
{
  "action": "switch_session",
  "data": {
    "session_id": "sess-xxx"
  }
}

// send_message 示例
{
  "action": "send_message",
  "data": {
    "session_id": "sess-xxx",
    "content": "用户输入内容"
  }
}
"""

import json
import asyncio
from typing import Dict, Set, Any, Optional, List
from starlette.websockets import WebSocket
from datetime import datetime

from services.L1_infrastructure.L1d_events.event_bus import get_event_bus


class EventWebSocketPlugin:
    """
    WebSocket事件订阅插件
    
    订阅 EventBus 并将事件推送到所有WebSocket连接。
    插件模式：初始化时订阅事件总线，在连接到来时注册WebSocket连接。
    
    支持流式/非流式模式过滤：
    - 流式模式：转发流式事件，不转发聚合事件
    - 非流式模式：转发聚合事件，不转发流式事件
    """
    
    # 内部事件列表（不推送到前端）
    INTERNAL_EVENTS = {
        'system.initialized',
        'system.shutdown',
        'memory.saved',
        'memory.compressed',
        'memory.cleared',
        'message.created',  # 用户消息在前端直接处理，不依赖后台
        'tool.registered',  # 工具注册事件，不需要转发给前台
    }
    
    # 流式事件列表（实时片段）
    STREAMING_EVENTS = {
        'llm.stream_chunk',
        'llm.thinking',
        'llm.reasoning',
    }
    
    # 聚合事件列表（汇总完成）
    AGGREGATE_EVENTS = {
        'llm.call_text_completed',
        'llm.call_thinking_completed',
        'llm.call_reasoning_completed',
        'llm.tool_call_completed',
    }
    
    def __init__(self):
        self._event_bus = None
        self._subscription_id = None
        self._initialized = False
        self._connections: Set[WebSocket] = set()
        self._main_event_loop = None
        # 用于防止重复推送的消息ID缓存
        self._sent_message_ids: Set[str] = set()
        # 消息ID缓存清理定时器
        self._cleanup_task = None
        # 会话流式状态跟踪
        self._session_streaming_state: Dict[str, bool] = {}  # session_id -> is_streaming
    
    def initialize(self, event_bus):
        """
        初始化并订阅事件总线
        
        Args:
            event_bus: EventBus 实例
        """
        if self._initialized:
            return
        
        self._event_bus = event_bus
        
        # 订阅所有事件（使用 '*' 通配符）
        self._subscription_id = self._event_bus.subscribe('*', self._on_event, 'EventWebSocketPlugin')
        self._initialized = True
        
        # 启动消息ID缓存清理任务
        self._start_cleanup_task()
        
        print("[OK] EventWebSocketPlugin initialized, listening to all events")
        print(f"     Subscription ID: {self._subscription_id}")
    
    def _start_cleanup_task(self):
        """启动消息ID缓存清理任务"""
        if self._cleanup_task:
            return
        
        async def cleanup():
            """定期清理过期的消息ID缓存"""
            while True:
                await asyncio.sleep(60)  # 每分钟清理一次
                # 清理所有消息ID（简单策略：每次清理全部，因为消息推送应该是即时的）
                self._sent_message_ids.clear()
                print(f"[WS-PLUGIN] Cleaned up {len(self._sent_message_ids)} message IDs")
        
        # 如果有事件循环，启动清理任务
        try:
            loop = asyncio.get_running_loop()
            self._cleanup_task = loop.create_task(cleanup())
            print("[WS-PLUGIN] Started message ID cleanup task")
        except RuntimeError:
            print("[WS-PLUGIN] No running event loop for cleanup task")
    
    def register_connection(self, websocket: WebSocket):
        """注册WebSocket连接"""
        self._connections.add(websocket)
        # 保存主事件循环引用（第一次注册时）
        if not self._main_event_loop:
            try:
                self._main_event_loop = asyncio.get_running_loop()
                print(f"[WS-PLUGIN] Saved main event loop: {self._main_event_loop}")
            except RuntimeError:
                print(f"[WS-PLUGIN] No running event loop available")
        print(f"[WS-PLUGIN] Registered WebSocket connection, total: {len(self._connections)}")
    
    def unregister_connection(self, websocket: WebSocket):
        """注销WebSocket连接"""
        self._connections.discard(websocket)
        print(f"[WS-PLUGIN] Unregistered WebSocket connection, total: {len(self._connections)}")
    
    def _on_event(self, event, event_record=None, correlation_id: str = None):
        """
        事件回调处理函数
        
        Args:
            event: 事件对象
            event_record: 事件记录（可选）
            correlation_id: 关联ID（可选）
        """
        # 过滤掉内部事件
        if event.event_type in self.INTERNAL_EVENTS:
            return
        
        # 处理会话切换事件 - 触发历史回放
        if event.event_type == 'session.switched':
            self._handle_session_switch(event)
            return
        
        # 获取会话ID
        session_id = event.payload.get('session_id') if isinstance(event.payload, dict) else None
        
        # 根据流式/非流式模式过滤事件
        if not self._should_forward_event(event.event_type, session_id):
            print(f"[WS-PLUGIN] 跳过事件（模式过滤）: {event.event_type}, session: {session_id}")
            return
        
        # 更新会话流式状态
        self._update_streaming_state(event.event_type, session_id)
        
        # 打印接收事件
        print(f"\n{'='*60}")
        print(f"[WS-PLUGIN] >>> Received Event <<<")
        print(f"  Type: {event.event_type}")
        print(f"  Time: {event.timestamp}")
        print(f"  Connections: {len(self._connections)}")
        print(f"  Session: {session_id}")
        print(f"  Streaming: {self._session_streaming_state.get(session_id, False)}")
        
        if isinstance(event.payload, dict):
            source = event.payload.get('source_component', 'unknown')
            print(f"  Source: {source}")
            # 打印关键数据
            for key in ['response_type', 'tool_name', 'call_id']:
                if key in event.payload:
                    value = event.payload[key]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:50] + '...'
                    print(f"  {key}: {value}")
        print(f"{'='*60}\n")
        
        # 构建WebSocket消息
        # 根据唯一入口原则，不生成新的 message_id，使用事件中原有的 message_id
        message_id = None
        if isinstance(event.payload, dict):
            message_id = event.payload.get('message_id')
        
        event_data = {
            'version': '1.0',
            'type': 'event',
            'action': event.event_type,
            'session_id': session_id,
            'timestamp': event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
            'data': event.payload if isinstance(event.payload, dict) else {'content': str(event.payload)},
            'metadata': {
                'source_component': event.payload.get('source_component') if isinstance(event.payload, dict) else 'unknown'
            }
        }
        
        # 只在 message_id 存在时添加（由 MessageService 等业务服务创建）
        if message_id:
            event_data['message_id'] = message_id
        
        # 广播到所有连接
        self._broadcast(event_data)
    
    def _should_forward_event(self, event_type: str, session_id: str) -> bool:
        """
        判断是否应该转发事件到前台
        
        转发规则：
        - 流式模式：转发流式事件，不转发聚合事件
        - 非流式模式：转发聚合事件，不转发流式事件
        - 其他事件（如tool.call_started, dialog.created等）：始终转发
        
        Args:
            event_type: 事件类型
            session_id: 会话ID
        
        Returns:
            是否应该转发
        """
        # 非LLM事件始终转发
        if not event_type.startswith('llm.'):
            return True
        
        # 获取会话的流式状态（默认为非流式）
        is_streaming = self._session_streaming_state.get(session_id, False)
        
        # 流式事件处理
        if event_type in self.STREAMING_EVENTS:
            # 流式模式：转发；非流式模式：不转发
            return is_streaming
        
        # 聚合事件处理
        if event_type in self.AGGREGATE_EVENTS:
            # 非流式模式：转发；流式模式：不转发
            return not is_streaming
        
        # 其他LLM事件（如llm.request_sent, llm.response_received等）始终转发
        return True
    
    def _update_streaming_state(self, event_type: str, session_id: str):
        """
        更新会话的流式状态
        
        Args:
            event_type: 事件类型
            session_id: 会话ID
        """
        if not session_id:
            return
        
        # 如果收到流式事件，标记会话为流式模式
        if event_type in self.STREAMING_EVENTS:
            self._session_streaming_state[session_id] = True
        
        # 如果收到聚合事件，标记会话为非流式模式
        if event_type in self.AGGREGATE_EVENTS:
            self._session_streaming_state[session_id] = False
    
    def _clear_session_sent_messages(self, session_id):
        """
        清除指定会话的已发送消息记录
        
        Args:
            session_id: 会话ID
        
        当用户切换到一个新会话时，需要清除该会话之前的已发送消息记录，
        这样下次切换回该会话时可以重新推送所有历史消息。
        """
        # 找出所有属于该会话的已发送消息键并删除
        keys_to_remove = []
        for key in self._sent_message_ids:
            if key.startswith(f"{session_id}:"):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self._sent_message_ids.discard(key)
        
        print(f"[WS-PLUGIN] Cleared {len(keys_to_remove)} sent message records for session {session_id}")
    
    def _handle_session_switch(self, event):
        """
        处理会话切换事件，触发历史消息回放
        
        Args:
            event: SESSION_SWITCHED 事件
        """
        session_id = event.payload.get('session_id')
        client_id = event.payload.get('client_id')
        
        if not session_id:
            print(f"[WS-PLUGIN] Session switch event without session_id")
            return
        
        print(f"\n{'='*60}")
        print(f"[WS-PLUGIN] >>> Session Switch Detected <<<")
        print(f"  Session ID: {session_id}")
        print(f"  Client ID: {client_id}")
        print(f"{'='*60}\n")
        
        # 清除该会话的已发送消息记录，确保每次切换到会话时都能重新推送所有历史消息
        self._clear_session_sent_messages(session_id)
        
        try:
            # 优先从API日志服务获取持久化的历史消息
            # 这样可以确保重启后历史消息仍然可用，并且与websocket_messages.json一致
            from services.L4_gateway.L4a_http_gateway.middleware.api_logging import get_api_log_service
            api_log_service = get_api_log_service()
            
            # 获取该会话的所有outbound消息
            messages = api_log_service.get_websocket_messages({
                'session_id': session_id,
                'direction': 'outbound'
            })
            
            print(f"[WS-PLUGIN] Found {len(messages)} persisted messages for session {session_id}")
            
            # 如果持久化存储中没有消息，尝试从内存缓存获取
            if not messages:
                from services.L2_domain.L2b_memory_state.websocket_cache_service import get_websocket_cache_service
                cache_service = get_websocket_cache_service()
                cache_messages = cache_service.get_messages(session_id)
                print(f"[WS-PLUGIN] Found {len(cache_messages)} cached messages for session {session_id}")
                
                # 转换为与持久化存储相同的格式
                messages = [msg.to_dict() for msg in cache_messages]
            
            if not self._main_event_loop:
                print(f"[WS-PLUGIN] No event loop available, cannot replay")
                return
            
            # 创建异步回放任务
            replay_task = self._create_replay_task(session_id, messages, event.timestamp)
            self._main_event_loop.call_soon_threadsafe(
                lambda coro: asyncio.create_task(coro),
                replay_task
            )
            
        except Exception as e:
            import traceback
            print(f"[WS-PLUGIN] Failed to replay history: {e}")
            traceback.print_exc()
    
    async def _create_replay_task(self, session_id: str, messages: List, timestamp) -> None:
        """
        创建异步历史回放任务
        
        Args:
            session_id: 会话ID
            messages: 消息列表（从持久化存储获取的字典格式，包含payload字段）
            timestamp: 事件时间戳
        """
        try:
            # 直接以保存的次序回放，不进行排序
            print(f"[WS-PLUGIN] Replay started for session {session_id}, {len(messages)} messages")
            
            # 逐条推送历史消息（带短暂延迟，避免消息堆积）
            sent_count = 0
            skipped_count = 0
            for idx, msg in enumerate(messages):
                # 解析payload字段（持久化存储中payload是JSON字符串）
                payload_str = msg.get('payload', '{}')
                try:
                    payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
                except json.JSONDecodeError:
                    print(f"[WS-PLUGIN] Failed to parse payload for message: {msg.get('log_id')}")
                    continue
                
                # 获取消息ID用于去重
                msg_id = payload.get('message_id', msg.get('log_id', f"msg-{idx}"))
                
                # 跳过已发送的消息（去重）
                # 使用 session_id + msg_id 作为去重键，支持多次切换会话
                deduplication_key = f"{session_id}:{msg_id}"
                if deduplication_key in self._sent_message_ids:
                    print(f"[WS-PLUGIN] Skipping duplicate message for session: {msg_id}")
                    skipped_count += 1
                    continue
                
                # 标记消息已发送（按会话去重）
                self._sent_message_ids.add(deduplication_key)
                
                # 直接发送原始payload，与正常对话消息格式一致
                await self._send_to_all_connections(json.dumps(payload, ensure_ascii=False), 'replay')
                sent_count += 1

                # 每条消息延迟500ms，确保前端处理完毕再发送下一条
                await asyncio.sleep(0.1)
            
            print(f"[WS-PLUGIN] History replay completed for session {session_id}: 发送 {sent_count} 条消息, 跳过 {skipped_count} 条重复消息 (共 {len(messages)} 条)")
            
        except Exception as e:
            import traceback
            print(f"[WS-PLUGIN] Error in replay task: {e}")
            traceback.print_exc()
    
    async def _send_to_all_connections(self, message: str, event_type: str):
        """
        异步发送消息到所有连接
        
        Args:
            message: 消息内容（已序列化）
            event_type: 事件类型（用于日志）
        """
        success_count = 0
        failed_count = 0
        
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
                success_count += 1
            except Exception as e:
                print(f"[WS-PLUGIN] Failed to send {event_type} to connection: {e}")
                failed_count += 1
        
        if success_count > 0:
            print(f"[WS-PLUGIN] Sent {event_type} to {success_count} connections")
        if failed_count > 0:
            print(f"[WS-PLUGIN] Failed to send {event_type} to {failed_count} connections")
    
    def _create_send_coro(self, ws, message, evt_type):
        """创建发送消息的协程"""
        async def _send():
            try:
                await ws.send_text(message)
                print(f"[WS-PLUGIN] Send completed: {evt_type}")
            except Exception as e:
                print(f"[WS-PLUGIN] Send failed: {e}")
        return _send
    
    def _broadcast(self, event_data: Dict[str, Any]):
        """广播事件到所有WebSocket连接"""
        if not self._main_event_loop:
            print(f"[WS-PLUGIN] No event loop available, skipping broadcast")
            return
        
        try:
            message = json.dumps(event_data, ensure_ascii=False)
            event_type = event_data.get('action', 'unknown')
            session_id = event_data.get('session_id')
            
            print(f"[WS-PLUGIN] Broadcasting: {event_type}")
            print(f"  Message length: {len(message)} chars")
            print(f"  Active connections: {len(self._connections)}")
            
            # 记录WebSocket消息到API日志
            try:
                from services.L4_gateway.L4a_http_gateway.middleware.api_logging import get_api_log_service
                log_service = get_api_log_service()
                log_service.save_websocket_message(
                    client_id='broadcast',
                    payload=event_data,
                    direction='outbound',
                    session_id=session_id,  # 使用正确的session_id，确保历史回放时能按session过滤
                    message_type=f'event_{event_type}'
                )
            except Exception as e:
                print(f"[WS-PLUGIN] Failed to log message: {e}")
            
            # 记录到WebSocket内存缓存（用于前端展示和会话切换回放）
            if session_id:
                try:
                    from services.L2_domain.L2b_memory_state.websocket_cache_service import get_websocket_cache_service
                    cache_service = get_websocket_cache_service()
                    
                    # 根据事件类型确定消息类型和内容
                    data = event_data.get('data', {})
                    content = ''
                    msg_type = 'event'
                    
                    if event_type == 'llm.response_received':
                        content = data.get('content', '')
                        msg_type = 'assistant'
                    elif event_type == 'message.created' and data.get('role') == 'user':
                        content = data.get('content', '')
                        msg_type = 'user'
                    elif event_type == 'tool.execution.output':
                        content = str(data.get('output', ''))
                        msg_type = 'tool'
                    elif 'thinking' in data:
                        content = data.get('thinking', '')
                        msg_type = 'thinking'
                    elif 'content' in data:
                        # 通用处理：任何包含content字段的事件
                        content = data.get('content', '')
                        msg_type = 'event'
                    
                    if content:
                        cache_service.add_message(
                            session_id=session_id,
                            message_type=msg_type,
                            content=content,
                            metadata={
                                'event_type': event_type,
                                'source_component': data.get('source_component', 'unknown')
                            }
                        )
                except Exception as e:
                    print(f"[WS-PLUGIN] Failed to record to websocket cache: {e}")
            
            # 使用主事件循环发送消息 - 使用 call_soon_threadsafe 确保立即调度
            def send_to_websocket(ws, msg, evt_type):
                async def _send():
                    try:
                        await ws.send_text(msg)
                        print(f"[WS-PLUGIN] Send completed: {evt_type}")
                    except Exception as e:
                        print(f"[WS-PLUGIN] Send failed: {e}")
                return _send()
            
            success_count = 0
            for ws in list(self._connections):
                try:
                    # 创建一个协程来发送消息
                    send_coro = send_to_websocket(ws, message, event_type)
                    # 使用 call_soon_threadsafe 将协程添加到事件循环
                    self._main_event_loop.call_soon_threadsafe(
                        lambda coro: asyncio.create_task(coro),
                        send_coro
                    )
                    success_count += 1
                except Exception as e:
                    print(f"[WS-PLUGIN] Failed to schedule send: {e}")
            
            print(f"[WS-PLUGIN] Broadcast scheduled for {success_count} connections")
            
        except Exception as e:
            print(f"[WS-PLUGIN] Broadcast failed: {e}")
    
    def _on_send_done(self, future, event_type: str):
        """发送完成回调"""
        try:
            future.result()
            print(f"[WS-PLUGIN] Send completed: {event_type}")
        except Exception as e:
            print(f"[WS-PLUGIN] Send failed: {e}")
    
    def shutdown(self):
        """关闭插件"""
        # 取消清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            self._cleanup_task = None
            print("[WS-PLUGIN] Cleanup task cancelled")
        
        if self._subscription_id and self._event_bus:
            self._event_bus.unsubscribe(self._subscription_id)
            print("[OK] EventWebSocketPlugin shutdown")
        
        self._connections.clear()
        self._sent_message_ids.clear()


# 全局插件实例
_global_plugin = None

def get_websocket_plugin() -> EventWebSocketPlugin:
    """获取全局WebSocket插件实例"""
    global _global_plugin
    if _global_plugin is None:
        _global_plugin = EventWebSocketPlugin()
    return _global_plugin
