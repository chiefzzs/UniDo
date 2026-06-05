"""
WebSocket服务器模块

负责处理WebSocket连接和消息路由。
使用事件分发器模式，每个连接注册到事件分发器，事件分发器负责将事件推送给所有连接。
"""

import json
from typing import Dict, Set, Any, Optional
from starlette.websockets import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """添加连接"""
        self.active_connections[client_id] = websocket
    
    async def disconnect(self, client_id: str):
        """移除连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]


class MessageHandler:
    """消息处理器"""
    
    async def handle_message(self, data: Dict[str, Any], client_id: str):
        """处理消息"""
        action = data.get('action')
        
        if action == 'join_session':
            return {
                'version': '1.0',
                'type': 'response',
                'action': 'join_session_response',
                'message_id': f"msg-{id(data)}",
                'session_id': data.get('session_id'),
                'timestamp': data.get('timestamp', ''),
                'data': {'status': 'success', 'project_id': None}
            }
        elif action == 'send_message':
            # 消息处理由L3服务处理，这里只返回确认
            return None
        
        return None


class WebSocketServer:
    """
    WebSocket服务器
    
    处理WebSocket连接的建立、消息处理和断开。
    使用事件分发器模式来推送事件到所有连接。
    """
    
    # 内部事件列表（不推送到前端）
    INTERNAL_EVENTS = {
        'system.initialized',       # 系统初始化完成
        'system.shutdown',          # 系统关闭
        'memory.saved',             # 记忆保存
        'memory.compressed',        # 记忆压缩
        'memory.cleared',           # 记忆清除
    }
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of event types
        self.connection_manager = ConnectionManager()
        self.message_handler = MessageHandler()
    
    def _generate_message_id(self) -> str:
        """生成唯一消息ID"""
        import uuid
        return f"msg-{uuid.uuid4().hex[:8]}"
    
    async def handle_connection(self, websocket: WebSocket, client_id: str, plugin=None):
        """处理WebSocket连接"""
        await self.connection_manager.connect(websocket, client_id)
        self.active_connections[client_id] = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                await self._handle_message(websocket, client_id, data)
        except WebSocketDisconnect:
            print(f"WebSocket disconnected: {client_id}")
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            # 从插件注销连接
            if plugin:
                plugin.unregister_connection(websocket)
            
            await self.connection_manager.disconnect(client_id)
            if client_id in self.active_connections:
                del self.active_connections[client_id]
    
    async def _route_to_service(self, data: Dict[str, Any], client_id: str):
        """
        将消息路由到 L3 服务
        
        Args:
            data: 消息数据（格式: { action, data: { session_id, content } }）
            client_id: 客户端ID
        
        Returns:
            响应数据
        """
        try:
            from services.L4_gateway.L4a_http_gateway.api_server import api_server_instance
            
            if not api_server_instance:
                print("[WS-SERVER] API server instance not available")
                return {
                    'type': 'error',
                    'action': 'send_message_response',
                    'message': 'Server not ready'
                }
            
            # 获取消息内容 - 前端发送的格式是 { action: 'send_message', data: { session_id, content } }
            message_data = data.get('data', {})
            session_id = message_data.get('session_id')
            content = message_data.get('content', '')
            
            print(f"[WS-SERVER] Routing message: session={session_id}, content={content[:50]}...")
            
            # 如果有 session_id 和 content，处理用户消息
            if session_id and content:
                # 在新线程中异步处理用户消息，不阻塞 WebSocket 连接
                import threading
                from services.L3_scenario_coordination.L3c_ui_scenarios.DialogManager.dialog_manager import DialogManager
                
                print(f"[WS-SERVER] Starting background thread for session: {session_id}")
                
                def process_message_in_thread():
                    try:
                        print(f"[WS-SERVER] [Thread] Processing message for session: {session_id}")
                        dialog_manager = DialogManager()
                        result = dialog_manager.process_user_input(session_id, content)
                        print(f"[WS-SERVER] [Thread] DialogManager result: {result}")
                    except Exception as e:
                        print(f"[WS-SERVER] [Thread] DialogManager error: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 在后台线程中处理消息
                thread = threading.Thread(target=process_message_in_thread)
                thread.start()
                print(f"[WS-SERVER] Thread started for session: {session_id}")
                
                return {
                    'type': 'ack',
                    'action': 'send_message_response',
                    'session_id': session_id,
                    'status': 'processing'
                }
            else:
                return {
                    'type': 'error',
                    'action': 'send_message_response',
                    'message': 'Missing session_id or content in message'
                }
                
        except Exception as e:
            import traceback
            print(f"[WS-SERVER] Error routing message: {e}")
            traceback.print_exc()
            return {
                'type': 'error',
                'action': 'send_message_response',
                'message': str(e)
            }
    
    async def _handle_message(self, websocket: WebSocket, client_id: str, message: str):
        """处理收到的消息"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            # 处理 ping 心跳消息 - 直接返回，不记录不发布事件也不打印
            if action == 'ping':
                return
            
            print(f"\n{'='*60}")
            print(f"[WS-SERVER] >>> Received Message <<<")
            print(f"  Client ID: {client_id}")
            print(f"  Action: {action}")
            print(f"  Full message: {message[:500]}...")
            
            # 发布 client.message_received 事件 - 只在 send_message 动作时发布（用户输入场景）
            # switch_session 等其他动作不应该发布此事件，避免与用户消息混淆
            session_id = data.get('session_id') or data.get('data', {}).get('session_id')
            if action == 'send_message':
                # 获取用户输入内容
                message_data = data.get('data', {})
                content = message_data.get('content', '')
                
                from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
                from services.L1_infrastructure.L1d_events.event_types import EventTypes
                EventBus.get_instance().publish(Event(
                    event_type=EventTypes.CLIENT_MESSAGE_RECEIVED,
                    payload={
                        'client_id': client_id,
                        'session_id': session_id,
                        'action': action,
                        'message_id': data.get('message_id'),
                        'content': content  # 携带用户输入内容
                    }
                ))
            
            # 记录收到的消息
            from services.L4_gateway.L4a_http_gateway.middleware.api_logging import get_api_log_service
            log_service = get_api_log_service()
            log_service.save_websocket_message(
                client_id=client_id,
                payload=data,
                direction='inbound',
                session_id=data.get('session_id'),
                message_type=action
            )
            
            # 处理 send_message 动作 - 发送到 L3 服务
            if action == 'send_message':
                print(f"[WS-SERVER] Routing send_message to L3 service")
                response = await self._route_to_service(data, client_id)
                if response:
                    await websocket.send_text(json.dumps(response, ensure_ascii=False))
                return
            
            # 处理 switch_session 动作 - 触发历史消息回放
            if action == 'switch_session':
                print(f"[WS-SERVER] Handling switch_session")
                session_id = data.get('data', {}).get('session_id')
                if session_id:
                    # 发布SESSION_SWITCHED事件，触发后端历史回放
                    try:
                        from services.L1_infrastructure.L1d_events.event_bus import EventBus
                        from services.L1_infrastructure.L1d_events.event_types import EventTypes
                        from services.L1_infrastructure.L1d_events.event_record import Event
                        
                        event_bus = EventBus.get_instance()
                        event_bus.publish(Event(
                            event_type=EventTypes.SESSION_SWITCHED,
                            payload={
                                'session_id': session_id,
                                'client_id': client_id,
                                'source_component': 'websocket_server'
                            }
                        ))
                        print(f"[WS-SERVER] Published SESSION_SWITCHED event for session: {session_id}")
                        
                        # 返回确认
                        await websocket.send_text(json.dumps({
                            'type': 'ack',
                            'action': 'switch_session_response',
                            'session_id': session_id,
                            'status': 'switching'
                        }, ensure_ascii=False))
                    except Exception as e:
                        print(f"[WS-SERVER] Error publishing SESSION_SWITCHED event: {e}")
                return
            
            # 处理其他消息
            response = await self.message_handler.handle_message(data, client_id)
            
            # 发送响应
            if response:
                # 确保响应有正确的格式
                if isinstance(response, dict) and 'type' not in response:
                    response['type'] = 'response'
                
                await websocket.send_text(json.dumps(response, ensure_ascii=False))
                
                # 记录发送的响应
                log_service.save_websocket_message(
                    client_id=client_id,
                    payload=response,
                    direction='outbound',
                    session_id=response.get('session_id'),
                    message_type=response.get('action', 'response')
                )
                
        except json.JSONDecodeError:
            print(f"Invalid JSON message: {message}")
            await websocket.send_text(json.dumps({
                'type': 'error',
                'message': '无效的JSON格式'
            }))
        except Exception as e:
            print(f"处理消息失败: {e}")
            await websocket.send_text(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """发送消息给指定客户端"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(
                    json.dumps(message, ensure_ascii=False)
                )
                
                # 发布 client.message_sent 事件
                from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
                from services.L1_infrastructure.L1d_events.event_types import EventTypes
                EventBus.get_instance().publish(Event(
                    event_type=EventTypes.CLIENT_MESSAGE_SENT,
                    payload={
                        'client_id': client_id,
                        'session_id': message.get('session_id'),
                        'message_type': message.get('type'),
                        'action': message.get('action'),
                        'message_id': message.get('message_id')
                    }
                ))
                
                return True
            except Exception as e:
                print(f"发送消息给客户端失败: {e}")
                return False
        return False
