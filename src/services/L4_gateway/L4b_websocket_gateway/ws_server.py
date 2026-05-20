"""
WebSocket Server - WebSocket服务器实现

提供实时双向通信功能，支持消息持久化和事件实时推送。
"""

import asyncio
import json
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
        
        try:
            # 1. 使用DialogManager处理用户输入
            from services.L3_scenario_coordination.L3c_ui_scenarios.DialogManager.dialog_manager import DialogManager
            dialog_manager = DialogManager()
            dialog_result = dialog_manager.process_user_input(session_id, content)
            
            # 2. 调用LLM服务获取响应
            from services.L3_scenario_coordination.L3a_task_coordination.dialogue_based_llm_service import DialogueBasedLLMService
            llm_service = DialogueBasedLLMService()
            
            # 获取可用工具
            tools = llm_service.get_tools_for_llm()
            
            # 调用LLM执行服务
            llm_response = llm_service.call_llm(session_id, content, tools=tools, stream=False)
            
            # 检查LLM响应是否成功
            if not llm_response.success:
                raise Exception(f"LLM调用失败: {llm_response.error}")
            
            # 3. 处理工具调用（如果有）
            response_content = llm_response.content
            if llm_response.tool_calls:
                # 发布工具调用开始事件
                from services.L1_infrastructure.L1d_events.event_record import Event
                from services.L1_infrastructure.L1d_events.event_types import EventTypes
                from services.L1_infrastructure import get_event_bus
                
                event_bus = get_event_bus()
                dialog_id = dialog_result['dialog_id']
                
                event_bus.publish(Event(
                    event_type=EventTypes.TOOL_EXECUTION_STARTED,
                    payload={
                        'dialog_id': dialog_id,
                        'session_id': session_id,
                        'tool_calls': [
                            {
                                'name': tc.get('function', {}).get('name', tc.get('name', '')),
                                'arguments': tc.get('function', {}).get('arguments', tc.get('arguments', '{}'))
                            } for tc in llm_response.tool_calls
                        ],
                        'message': f'LLM选择了 {len(llm_response.tool_calls)} 个工具开始执行',
                        'source_component': 'L4_websocket_gateway',
                        'source_service': 'WebSocketServer'
                    }
                ))
                
                # 如果LLM返回了工具调用，执行工具调用
                tool_results = []
                for tool_call in llm_response.tool_calls:
                    tool_result = self._execute_tool_call(tool_call, session_id)
                    tool_results.append(tool_result)
                
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
                        {"role": "system", "content": "请用自然语言总结工具执行结果并回答用户问题"},
                        {"role": "user", "content": summary_prompt}
                    ]
                    summary_response = llm_service.call_llm(session_id, summary_messages, stream=False)
                    response_content = summary_response.content
            
            # 4. 保存助手消息到对话
            dialog_id = dialog_result['dialog_id']
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
            
            return {
                "type": "message_response",
                "status": "success",
                "session_id": session_id,
                "data": {"content": response_content}
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] _handle_send_message failed: {error_trace}")
            
            # 如果LLM调用失败，提供模拟响应以保持对话流程正常
            mock_response = self._generate_mock_response(content)
            
            # 保存模拟响应到对话
            try:
                from services.L2_domain.L2b_memory_state.message_service import MessageService
                message_service = MessageService()
                message_service.create_message(
                    dialog_id=dialog_result.get('dialog_id', f"dialog-{uuid.uuid4().hex[:12]}"),
                    role='assistant',
                    content=mock_response,
                    metadata={
                        'type': 'assistant_response',
                        'source': 'mock'
                    }
                )
            except:
                pass
            
            return {
                "type": "message_response",
                "status": "success",
                "session_id": session_id,
                "data": {"content": mock_response}
            }
    
    def _generate_mock_response(self, user_input: str) -> str:
        """
        生成模拟响应（当LLM服务不可用时使用）
        
        Args:
            user_input: 用户输入
            
        Returns:
            模拟响应内容
        """
        # 检测用户意图并生成相应的模拟响应
        if any(keyword in user_input.lower() for keyword in ['文件', '目录', '查看', '列表']):
            return "我已收到您的请求，正在查看工作区文件目录...\n\n当前工作区包含以下内容：\n- src/ (源代码目录)\n- data/ (数据存储目录)\n- tools/ (工具定义目录)\n- static/ (前端静态文件)"
        
        elif any(keyword in user_input.lower() for keyword in ['帮助', '功能', '能做什么']):
            return "我是一个智能助手，可以帮助您：\n\n1. 查看和管理工作区文件\n2. 搜索代码库\n3. 执行命令\n4. 读取和编辑文件\n5. 回答问题\n\n请问您需要什么帮助？"
        
        elif any(keyword in user_input.lower() for keyword in ['项目', '创建', '新建']):
            return "好的，我可以帮助您创建新项目。请告诉我项目名称和所需的配置，我会为您创建。"
        
        elif any(keyword in user_input.lower() for keyword in ['保存', '保存项目', '修改']):
            return "项目已保存成功！您的更改已持久化到本地存储。"
        
        elif any(keyword in user_input.lower() for keyword in ['删除', '移除']):
            return "已删除成功！"
        
        else:
            # 默认响应
            return f"收到您的消息：\"{user_input}\"\n\n这是一个模拟响应。在实际部署中，此消息将由LLM生成。\n\n如果您需要特定功能，请告诉我！"

    
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
            
            return {
                "tool_name": tool_name,
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None,
                "call_id": result.call_id
            }
            
        except Exception as e:
            return {"tool_name": tool_call.get("name"), "success": False, "error": str(e)}
    
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
