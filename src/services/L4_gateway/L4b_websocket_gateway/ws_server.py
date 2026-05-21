"""
WebSocket Server - WebSocket服务器实现

提供实时双向通信功能，支持消息持久化和事件实时推送。
"""

import asyncio
import json
import datetime
from typing import Dict, Any, Set
from fastapi import WebSocket, WebSocketDisconnect

# 延迟导入以避免循环依赖
_api_log_service = None
_event_bus = None

def get_api_log_service():
    global _api_log_service
    if _api_log_service is None:
        from services.L2_domain.L2b_memory_state import get_api_log_service as get_service
        _api_log_service = get_service()
    return _api_log_service

def get_event_bus():
    global _event_bus
    if _event_bus is None:
        from services.L1_infrastructure.L1d_events import get_event_bus as get_bus
        _event_bus = get_bus()
    return _event_bus


class WebSocketServer:
    # 不推送到前端的事件类型（内部管理事件）
    # 注意：工具执行状态事件（如 tool.execution_started, tool.call_completed）需要保留用于前端显示
    INTERNAL_EVENTS = {
        'tool.registered',       # 工具注册 - 内部事件
        'tool.unregistered',     # 工具注销 - 内部事件
        'tool.updated',          # 工具更新 - 内部事件
        'tool.loaded',           # 工具加载 - 内部事件
        'client.message_received',  # 客户端消息接收 - 内部事件
        'client.message_sent',      # 客户端消息发送 - 内部事件
        'memory.compressed',     # 记忆压缩 - 内部事件
        'memory.cleared',        # 记忆清除 - 内部事件
    }
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of event types
        self.connection_manager = ConnectionManager()
        self.message_handler = MessageHandler()
        self._event_subscription_id = None
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """订阅事件总线，将事件推送到所有连接的客户端"""
        try:
            event_bus = get_event_bus()
            self._event_subscription_id = event_bus.subscribe(
                '*',  # 订阅所有事件
                self._on_event_received,
                subscriber_name='websocket_server'
            )
            print("✅ WebSocket服务器已订阅事件总线")
        except Exception as e:
            print(f"❌ 订阅事件总线失败: {e}")
    
    def _on_event_received(self, event):
        """事件总线回调，将事件推送到所有订阅的客户端"""
        # 过滤掉内部事件，不推送到前端
        if event.event_type in self.INTERNAL_EVENTS:
            return

        print(f"[EVENT DEBUG] 接收到事件: {event.event_type}")

        event_data = {
            'type': 'event',
            'event_type': event.event_type,
            'payload': event.payload,
            'timestamp': event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp)
        }

        # 异步发送事件到所有客户端
        asyncio.create_task(self._broadcast_event(event_data))
    
    async def _broadcast_event(self, event_data: Dict[str, Any]):
        """广播事件到所有连接的客户端"""
        try:
            message = json.dumps(event_data)
            await self.connection_manager.broadcast(message)
        except Exception as e:
            print(f"❌ 广播事件失败: {e}")
    
    async def handle_connection(self, websocket: WebSocket, client_id: str):
        """处理WebSocket连接"""
        await self.connection_manager.connect(websocket, client_id)
        # 初始化订阅为空集合
        self.connection_subscriptions[client_id] = set()
        
        try:
            while True:
                data = await websocket.receive_text()
                
                # 记录收到的消息（inbound）
                log_service = get_api_log_service()
                message = json.loads(data)
                message_type = message.get("action") or message.get("type", "")
                session_id = message.get("session_id")
                
                log_service.save_websocket_message(
                    client_id=client_id,
                    payload=message,
                    direction="inbound",
                    session_id=session_id,
                    message_type=message_type
                )
                
                # 发布客户端消息接收事件
                try:
                    from services.L1_infrastructure.L1d_events.event_record import Event
                    from services.L1_infrastructure.L1d_events.event_types import EventTypes
                    
                    event_bus = get_event_bus()
                    event_bus.publish(Event(
                        event_type=EventTypes.CLIENT_MESSAGE_RECEIVED,
                        payload={
                            'client_id': client_id,
                            'session_id': session_id,
                            'message_type': message_type,
                            'message_length': len(data),
                            'source_component': 'L4_websocket_gateway',
                            'source_service': 'WebSocketServer'
                        }
                    ))
                except Exception as e:
                    print(f"❌ 发布客户端消息接收事件失败: {e}")
                
                # 处理消息
                response = await self.message_handler.handle(message, client_id)
                
                # 处理订阅/取消订阅请求
                if message_type == "subscribe":
                    await self._handle_subscribe(client_id, message.get("events", []))
                elif message_type == "unsubscribe":
                    await self._handle_unsubscribe(client_id, message.get("events", []))
                
                # 记录发送的消息（outbound）
                response_type = response.get("type", "")
                log_service.save_websocket_message(
                    client_id=client_id,
                    payload=response,
                    direction="outbound",
                    session_id=session_id,
                    message_type=response_type
                )
                
                # 发布客户端消息发送事件
                try:
                    from services.L1_infrastructure.L1d_events.event_record import Event
                    from services.L1_infrastructure.L1d_events.event_types import EventTypes
                    
                    event_bus = get_event_bus()
                    event_bus.publish(Event(
                        event_type=EventTypes.CLIENT_MESSAGE_SENT,
                        payload={
                            'client_id': client_id,
                            'session_id': session_id,
                            'message_type': response_type,
                            'message_length': len(json.dumps(response)),
                            'source_component': 'L4_websocket_gateway',
                            'source_service': 'WebSocketServer'
                        }
                    ))
                except Exception as e:
                    print(f"❌ 发布客户端消息发送事件失败: {e}")
                
                # 发送响应
                await websocket.send_text(json.dumps(response))
                
        except WebSocketDisconnect:
            self.connection_manager.disconnect(client_id)
            if client_id in self.connection_subscriptions:
                del self.connection_subscriptions[client_id]
            print(f"🔌 Client disconnected: {client_id}")
        except Exception as e:
            # 记录错误消息
            log_service = get_api_log_service()
            log_service.save_websocket_message(
                client_id=client_id,
                payload=None,
                direction="inbound",
                error_message=str(e)
            )
            self.connection_manager.disconnect(client_id)
            if client_id in self.connection_subscriptions:
                del self.connection_subscriptions[client_id]
            print(f"❌ Error handling client {client_id}: {e}")
    
    async def _handle_subscribe(self, client_id: str, events: list):
        """处理客户端订阅事件"""
        if client_id not in self.connection_subscriptions:
            self.connection_subscriptions[client_id] = set()
        
        for event_type in events:
            self.connection_subscriptions[client_id].add(event_type)
        
        print(f"📩 Client {client_id} subscribed to events: {events}")
    
    async def _handle_unsubscribe(self, client_id: str, events: list):
        """处理客户端取消订阅事件"""
        if client_id not in self.connection_subscriptions:
            return
        
        for event_type in events:
            self.connection_subscriptions[client_id].discard(event_type)
        
        print(f"📤 Client {client_id} unsubscribed from events: {events}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息到所有连接的客户端"""
        await self.connection_manager.broadcast(json.dumps(message))
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """向特定客户端发送消息"""
        # 记录发送的消息（outbound）
        log_service = get_api_log_service()
        message_type = message.get("type", "")
        session_id = message.get("session_id")
        
        log_service.save_websocket_message(
            client_id=client_id,
            payload=message,
            direction="outbound",
            session_id=session_id,
            message_type=message_type
        )
        
        await self.connection_manager.send_to(client_id, json.dumps(message))


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """连接客户端"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"🔌 Client connected: {client_id}")
    
    def disconnect(self, client_id: str):
        """断开客户端连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def broadcast(self, message: str):
        """广播消息"""
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"❌ Failed to send to connection: {e}")
    
    async def send_to(self, client_id: str, message: str):
        """向特定客户端发送消息"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                print(f"❌ Failed to send to {client_id}: {e}")


class MessageHandler:
    """消息处理器"""
    
    async def handle(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理WebSocket消息"""
        # 优先检查 action 字段（前端使用），如果不存在再检查 type 字段
        message_type = message.get("action") or message.get("type")
        
        handlers = {
            "ping": self._handle_ping,
            "message": self._handle_message,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "join_session": self._handle_join_session,
            "leave_session": self._handle_leave_session,
            "send_message": self._handle_send_message,
        }
        
        handler = handlers.get(message_type, self._handle_unknown)
        return await handler(message, client_id)
    
    async def _handle_join_session(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理加入会话请求"""
        session_id = message.get("session_id")
        return {
            "type": "join_session_response",
            "status": "success",
            "session_id": session_id,
            "client_id": client_id
        }
    
    async def _handle_leave_session(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理离开会话请求"""
        session_id = message.get("session_id")
        return {
            "type": "leave_session_response",
            "status": "success",
            "session_id": session_id
        }
    
    async def _handle_send_message(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理发送消息请求"""
        session_id = message.get("session_id")
        content = message.get("content", "")
        dialog_id = None
        
        try:
            # 1. 使用DialogManager处理用户输入
            from services.L3_scenario_coordination.L3c_ui_scenarios.DialogManager.dialog_manager import DialogManager
            dialog_manager = DialogManager()
            dialog_result = dialog_manager.process_user_input(session_id, content)
            dialog_id = dialog_result['dialog_id']
            
            # 2. 调用LLM服务获取响应（带超时）
            from services.L3_scenario_coordination.L3a_task_coordination.dialogue_based_llm_service import DialogueBasedLLMService
            llm_service = DialogueBasedLLMService()
            
            # 获取可用工具
            tools = llm_service.get_tools_for_llm()
            
            # 调用LLM执行服务
            llm_response = await self._call_llm_with_timeout(llm_service, session_id, content, tools, timeout=60)
            
            # 检查LLM响应是否成功
            if not llm_response.success:
                raise Exception(f"LLM调用失败: {llm_response.error}")
            
            # 3. 处理工具调用（如果有）
            response_content = llm_response.content
            tool_calls_data = []  # 新增：存储工具调用数据供前端显示
            
            if llm_response.tool_calls:
                # 发布工具调用开始事件
                from services.L1_infrastructure.L1d_events.event_record import Event
                from services.L1_infrastructure.L1d_events.event_types import EventTypes
                from services.L1_infrastructure import get_event_bus
                
                event_bus = get_event_bus()
                
                # 为每个工具调用生成call_id，确保与后续事件匹配
                tool_calls_with_ids = []
                for tc in llm_response.tool_calls:
                    call_id = tc.get('call_id', f'call-{hash(str(tc))}')
                    tool_calls_with_ids.append({
                        'name': tc.get('function', {}).get('name', tc.get('name', '')),
                        'arguments': tc.get('function', {}).get('arguments', tc.get('arguments', '{}')),
                        'call_id': call_id
                    })
                
                event_bus.publish(Event(
                    event_type=EventTypes.TOOL_EXECUTION_STARTED,
                    payload={
                        'dialog_id': dialog_id,
                        'session_id': session_id,
                        'tool_calls': tool_calls_with_ids,
                        'message': f'LLM选择了 {len(llm_response.tool_calls)} 个工具开始执行',
                        'source_component': 'L4_websocket_gateway',
                        'source_service': 'WebSocketServer'
                    }
                ))
                
                # 如果LLM返回了工具调用，执行工具调用
                tool_results = []
                for tool_call in llm_response.tool_calls:
                    # 获取工具名称和参数
                    tool_name = tool_call.get('function', {}).get('name', tool_call.get('name', ''))
                    tool_args = tool_call.get('function', {}).get('arguments', tool_call.get('args', {}))
                    call_id = tool_call.get('call_id', f'call-{hash(str(tool_call))}')
                    
                    # 发布工具调用开始事件
                    print(f"[EVENT DEBUG] 发布事件: {EventTypes.TOOL_CALL_STARTED}, call_id={call_id}")
                    event_bus.publish(Event(
                        event_type=EventTypes.TOOL_CALL_STARTED,
                        payload={
                            'tool_name': tool_name,
                            'tool_id': tool_name,
                            'arguments': tool_args,
                            'call_id': call_id,
                            'session_id': session_id,
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                    ))
                    
                    # 执行工具调用
                    tool_result = await self._execute_tool_call_async(tool_call, session_id)
                    tool_results.append(tool_result)
                    
                    # 发布工具执行输出事件（如果有输出）
                    if tool_result.get('result') or tool_result.get('error'):
                        output_content = tool_result.get('result') or tool_result.get('error', '')
                        event_bus.publish(Event(
                            event_type=EventTypes.TOOL_EXECUTION_OUTPUT,
                            payload={
                                'call_id': call_id,
                                'tool_name': tool_name,
                                'output': output_content,
                                'session_id': session_id,
                                'timestamp': datetime.datetime.now().isoformat()
                            }
                        ))
                    
                    # 发布工具调用完成事件
                    print(f"[TOOL RESULT DEBUG] 发布tool.call_completed事件: tool_result['success']={tool_result['success']}, type={type(tool_result['success'])}")
                    event_bus.publish(Event(
                        event_type=EventTypes.TOOL_CALL_COMPLETED if tool_result['success'] else EventTypes.TOOL_CALL_FAILED,
                        payload={
                            'tool_name': tool_result['tool_name'],
                            'tool_id': tool_name,
                            'call_id': call_id,
                            'success': tool_result['success'],  # 添加 success 字段供前端判断
                            'status': 'completed' if tool_result['success'] else 'failed',
                            'result': tool_result.get('result'),
                            'error': tool_result.get('error'),
                            'session_id': session_id,
                            'timestamp': datetime.datetime.now().isoformat()
                        }
                    ))
                    
                    # 构建工具调用数据结构供前端显示（保留批量数据）
                    tool_call_info = {
                        'tool_name': tool_result['tool_name'],
                        'arguments': tool_args,
                        'call_id': call_id,
                        'status': 'completed' if tool_result['success'] else 'failed',
                        'result': tool_result.get('result'),
                        'error': tool_result.get('error')
                    }
                    tool_calls_data.append(tool_call_info)
                
                # 如果有工具结果，保存工具执行消息到对话历史
                if tool_results:
                    from services.L2_domain.L2b_memory_state.message_service import MessageService
                    message_service = MessageService()
                    
                    for tool_result in tool_results:
                        tool_content = f"工具调用: {tool_result['tool_name']}\n结果: {tool_result.get('result', tool_result.get('error', '未知'))}"
                        message_service.create_message(
                            dialog_id=dialog_id,
                            role='tool',
                            content=tool_content,
                            metadata={
                                'type': 'tool_execution',
                                'tool_name': tool_result['tool_name'],
                                'success': tool_result['success'],
                                'call_id': tool_result.get('call_id')
                            }
                        )
                
                # 如果有工具结果，进行总结
                if tool_results:
                    summary_prompt = f"请总结以下工具执行结果：{tool_results}\n\n用户原始问题：{content}"
                    summary_messages = [
                        {"role": "system", "content": "请用Markdown格式总结工具执行结果并回答用户问题。代码请使用```语言名 ```包裹。"},
                        {"role": "user", "content": summary_prompt}
                    ]
                    summary_response = await self._call_llm_with_timeout(llm_service, session_id, summary_messages, tools=None, timeout=60)
                    response_content = summary_response.content
            
            # 4. 保存助手消息到对话
            from services.L2_domain.L2b_memory_state.message_service import MessageService
            message_service = MessageService()
            message_service.create_message(
                dialog_id=dialog_id,
                role='assistant',
                content=response_content,
                metadata={
                    'type': 'assistant_response',
                    'source': 'llm'
                }
            )
            
            # 5. 完成对话
            dialog_manager.finish_dialog(dialog_id, compress=False)
            
            # 6. 返回分类型的响应数据
            return {
                "type": "message_response",
                "status": "success",
                "session_id": session_id,
                "data": {
                    "content": response_content,
                    "type": "text",  # 默认类型为文本
                    "tool_calls": tool_calls_data  # 新增：工具调用数据
                }
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] _handle_send_message failed: {error_trace}")
            
            # 返回错误响应，不再提供模拟响应
            return {
                "type": "message_response",
                "status": "error",
                "session_id": session_id,
                "data": {"content": f"服务暂时不可用，请稍后重试。错误信息：{str(e)[:100]}"}
            }
    
    async def _call_llm_with_timeout(self, llm_service, session_id: str, content_or_messages, 
                                      tools: list = None, timeout: int = 60) -> Any:
        """
        异步调用LLM并带有超时保护
        
        Args:
            llm_service: LLM服务实例
            session_id: 会话ID
            content_or_messages: 用户内容或消息列表
            tools: 工具定义列表
            timeout: 超时时间(秒)
            
        Returns:
            LLM响应
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _call_llm():
            if isinstance(content_or_messages, str):
                return llm_service.call_llm(session_id, content_or_messages, tools=tools, stream=False)
            else:
                return llm_service.call_llm(session_id, content_or_messages, tools=tools, stream=False)
        
        try:
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as executor:
                result = await asyncio.wait_for(
                    loop.run_in_executor(executor, _call_llm),
                    timeout=timeout
                )
            return result
        except asyncio.TimeoutError:
            from services.L3_scenario_coordination.L3a_task_coordination.dialogue_based_llm_service import LLMResponse
            return LLMResponse(
                success=False,
                error=f"LLM调用超时({timeout}秒)"
            )
        except Exception as e:
            from services.L3_scenario_coordination.L3a_task_coordination.dialogue_based_llm_service import LLMResponse
            return LLMResponse(
                success=False,
                error=f"LLM调用异常: {str(e)}"
            )
    
    async def _execute_tool_call_async(self, tool_call: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        异步执行工具调用
        
        Args:
            tool_call: 工具调用信息
            session_id: 会话ID
            
        Returns:
            工具执行结果
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        def _execute():
            return self._execute_tool_call(tool_call, session_id)
        
        try:
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as executor:
                result = await asyncio.wait_for(
                    loop.run_in_executor(executor, _execute),
                    timeout=120  # 工具执行超时120秒
                )
            return result
        except asyncio.TimeoutError:
            tool_name = None
            if "function" in tool_call:
                tool_name = tool_call["function"].get("name")
            else:
                tool_name = tool_call.get("name")
            return {
                "tool_name": tool_name or "未知工具",
                "success": False,
                "error": "工具执行超时(120秒)"
            }
        except Exception as e:
            tool_name = None
            if "function" in tool_call:
                tool_name = tool_call["function"].get("name")
            else:
                tool_name = tool_call.get("name")
            return {
                "tool_name": tool_name or "未知工具",
                "success": False,
                "error": f"工具执行异常: {str(e)}"
            }
    
    def _execute_tool_call(self, tool_call: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            # 处理两种工具调用格式
            if "function" in tool_call:
                # OpenAI 格式: {"function": {"name": "...", "arguments": "..."}}
                tool_name = tool_call["function"].get("name")
                args_str = tool_call["function"].get("arguments", "{}")
                import json
                try:
                    tool_args = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    tool_args = {}
            else:
                # 简单格式: {"name": "...", "args": {...}}
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
            
            # 直接使用 ToolExecutor 执行工具
            from services.L2_domain.L2c_tool_execution import ToolExecutor
            executor = ToolExecutor()
            
            # 获取工具定义
            from services.L2_domain.L2f_tool_management import ToolManagementService
            tool_management = ToolManagementService()
            tool_def = tool_management.get_tool(tool_name)
            
            if not tool_def:
                return {"tool_name": tool_name, "success": False, "error": f"工具 {tool_name} 未找到"}
            
            # 执行工具（使用 session_id 作为 dialog_id 和 task_id）
            result = executor.execute_tool(
                tool_name=tool_name,
                dialog_id=session_id,
                task_id=session_id,
                params=tool_args
            )

            print(f"[TOOL EXECUTE DEBUG] 工具执行完成: tool_name={tool_name}, result.success={result.success}, result.result={result.result}")

            return {
                "tool_name": tool_name,
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None,
                "call_id": result.call_id
            }
            
        except Exception as e:
            tool_name = None
            if "function" in tool_call:
                tool_name = tool_call["function"].get("name")
            else:
                tool_name = tool_call.get("name")
            return {"tool_name": tool_name or "未知工具", "success": False, "error": str(e)}
    
    async def _handle_ping(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理心跳消息"""
        return {"type": "pong", "timestamp": message.get("timestamp")}
    
    async def _handle_message(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理业务消息"""
        # 这里可以扩展为实际的消息处理逻辑
        return {
            "type": "message_response",
            "status": "success",
            "data": message.get("data"),
            "client_id": client_id
        }
    
    async def _handle_subscribe(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理订阅请求"""
        events = message.get("events", [])
        return {
            "type": "subscribe_response",
            "status": "success",
            "events": events
        }
    
    async def _handle_unsubscribe(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理取消订阅请求"""
        events = message.get("events", [])
        return {
            "type": "unsubscribe_response",
            "status": "success",
            "events": events
        }
    
    async def _handle_unknown(self, message: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """处理未知消息类型"""
        return {
            "type": "error",
            "status": "error",
            "message": f"Unknown message type: {message.get('type')}"
        }
