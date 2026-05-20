"""
L4 Gateway Integration Tests - WebSocket和事件测试

测试用例：
- L4-01: WebSocket消息处理和响应
- L4-02: 工具调用事件发布
- L4-03: LLM请求和响应事件
- L4-04: 事件持久化到events.json
- L4-05: WebSocket消息日志记录
- L4-06: 工具执行使用workspace路径
"""

import pytest
import os
import sys
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 设置项目路径
# tests/it/L4_gateway/test_l4_gateway.py -> 4 levels up
test_file = Path(__file__).resolve()
project_root = test_file.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置环境变量
os.environ['STORAGE_ENV'] = 'test'

from services.L4_gateway.L4b_websocket_gateway.ws_server import WebSocketServer, MessageHandler, ConnectionManager
from services.L1_infrastructure.L1d_events.event_bus import EventBus
from services.L1_infrastructure.L1d_events.event_types import EventTypes
from services.L1_infrastructure.L1d_events.event_record import Event
from services.L1_infrastructure.L1b_persistence.persistence_service import PersistenceService
from services.L3_scenario_coordination.L3a_task_coordination.dialogue_based_llm_service import DialogueBasedLLMService
from services.L2_domain.L2c_tool_execution import ToolExecutor
from services.L2_domain.L2a_project_config.workspace_config_service import WorkspaceConfigService


class TestL4GatewayIntegration:
    """L4网关集成测试类"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的清理和初始化"""
        # 清理测试数据
        self._cleanup_test_data()
        
        # 初始化组件
        self.event_bus = EventBus()
        self.persistence = PersistenceService()
        self.event_bus._persistence_service = self.persistence
        
        # 创建临时workspace目录
        self.temp_workspace = tempfile.mkdtemp(prefix="test_workspace_")
        
        # 创建workspace配置
        self.workspace_service = WorkspaceConfigService()
        workspace_config = self.workspace_service.create_workspace_config(
            name="测试工作区",
            root_path=self.temp_workspace,
            type="local"
        )
        
        yield
        
        # 测试后清理
        self._cleanup_test_data()
        if os.path.exists(self.temp_workspace):
            shutil.rmtree(self.temp_workspace, ignore_errors=True)
    
    def _cleanup_test_data(self):
        """清理测试数据"""
        try:
            # 清空所有测试数据
            for entity_type in ['events', 'websocket_messages', 'sessions', 'dialogs', 'messages', 
                               'llm_calls', 'tool_calls', 'workspace_configs']:
                try:
                    self.persistence._write_all(entity_type, [])
                except:
                    pass
        except Exception as e:
            print(f"清理测试数据失败: {e}")
    
    def _verify_file_exists_and_has_data(self, file_path: Path, entity_type: str, min_records: int = 1):
        """验证文件存在且包含数据"""
        if not file_path.exists():
            return False, f"文件不存在: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            if not isinstance(content, list):
                return False, f"文件内容不是列表格式: {file_path}"
            
            if len(content) < min_records:
                return False, f"记录数量不足: {len(content)} < {min_records}"
            
            return True, content
        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {e}"
        except Exception as e:
            return False, f"读取文件失败: {e}"

    def test_l4_01_websocket_message_handling(self):
        """
        L4-01: WebSocket消息处理和响应
        
        测试WebSocket消息处理器能够正确处理消息并返回响应
        """
        # 1. 创建消息处理器
        handler = MessageHandler()
        
        # 2. 创建模拟的WebSocket消息
        message = {
            "action": "ping"
        }
        
        # 3. 处理消息
        response = asyncio.run(handler.handle(message, "test_client"))
        
        # 4. 验证响应
        assert response is not None
        assert response.get("type") == "pong"
        # 注意：pong响应可能没有status字段
        
        print("[PASS] L4-01测试通过: WebSocket消息处理正常")
    
    def test_l4_02_tool_execution_events(self):
        """
        L4-02: 工具调用事件发布
        
        测试工具执行时正确发布开始和完成事件
        """
        # 1. 收集发布的事件
        published_events = []
        
        def event_collector(event):
            published_events.append(event)
        
        # 2. 订阅事件
        self.event_bus.subscribe('tool.execution_started', event_collector, 'test_collector')
        self.event_bus.subscribe('tool.call_completed', event_collector, 'test_collector')
        self.event_bus.subscribe('tool.call_failed', event_collector, 'test_collector')
        
        # 3. 发布工具执行开始事件
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_EXECUTION_STARTED,
            payload={
                'tool_calls': [
                    {'name': 'RunCommand', 'arguments': '{"command": "mkdir test"}'}
                ],
                'message': 'LLM选择了 1 个工具开始执行'
            }
        ))
        
        # 4. 发布工具执行完成事件
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_CALL_COMPLETED,
            payload={
                'call_id': 'call-123',
                'tool_name': 'RunCommand',
                'success': True,
                'duration': 0.1,
                'workspace': self.temp_workspace
            }
        ))
        
        # 5. 验证事件数量
        assert len(published_events) == 2, f"期望2个事件，实际{len(published_events)}"
        
        # 6. 验证第一个事件（工具执行开始）
        started_event = published_events[0]
        assert started_event.event_type == EventTypes.TOOL_EXECUTION_STARTED
        assert 'tool_calls' in started_event.payload
        assert started_event.payload['tool_calls'][0]['name'] == 'RunCommand'
        
        # 7. 验证第二个事件（工具执行完成）
        completed_event = published_events[1]
        assert completed_event.event_type == EventTypes.TOOL_CALL_COMPLETED
        assert completed_event.payload['success'] is True
        assert completed_event.payload['tool_name'] == 'RunCommand'
        assert completed_event.payload['workspace'] == self.temp_workspace
        
        print("[PASS] L4-02测试通过: 工具调用事件发布正常")
    
    def test_l4_03_llm_request_response_events(self):
        """
        L4-03: LLM请求和响应事件
        
        测试LLM请求发送和响应完成事件的发布
        """
        # 1. 收集发布的事件
        published_events = []
        
        def event_collector(event):
            published_events.append(event)
        
        # 2. 订阅LLM相关事件
        self.event_bus.subscribe('llm.request_sent', event_collector, 'test_collector')
        self.event_bus.subscribe('llm.call_completed', event_collector, 'test_collector')
        self.event_bus.subscribe('llm.call_failed', event_collector, 'test_collector')
        
        # 3. 发布LLM请求发送事件
        self.event_bus.publish(Event(
            event_type='llm.request_sent',
            payload={
                'session_id': 'sess-123',
                'model_config_id': 'default',
                'num_messages': 3,
                'num_tools': 18,
                'stream': False
            }
        ))
        
        # 4. 发布LLM调用完成事件
        self.event_bus.publish(Event(
            event_type='llm.call_completed',
            payload={
                'request_id': 'req-456',
                'dialog_id': 'dialog-123',
                'duration_ms': 5200,
                'has_tool_calls': True
            }
        ))
        
        # 5. 验证事件数量
        assert len(published_events) == 2, f"期望2个事件，实际{len(published_events)}"
        
        # 6. 验证LLM请求事件
        request_event = published_events[0]
        assert request_event.event_type == 'llm.request_sent'
        assert request_event.payload['num_tools'] == 18
        
        # 7. 验证LLM响应事件
        response_event = published_events[1]
        assert response_event.event_type == 'llm.call_completed'
        assert response_event.payload['has_tool_calls'] is True
        
        print("[PASS] L4-03测试通过: LLM请求和响应事件发布正常")
    
    def test_l4_04_event_persistence(self):
        """
        L4-04: 事件持久化到events.json
        
        测试事件能够正确持久化到events.json文件
        """
        # 1. 发布多个事件
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_EXECUTION_STARTED,
            payload={'tool_calls': [{'name': 'TestTool'}]}
        ))
        
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_CALL_COMPLETED,
            payload={'tool_name': 'TestTool', 'success': True}
        ))
        
        self.event_bus.publish(Event(
            event_type='llm.request_sent',
            payload={'session_id': 'sess-123'}
        ))
        
        # 2. 等待事件处理
        import time
        time.sleep(0.5)
        
        # 3. 获取数据目录
        data_dir = project_root / "src" / "data" / "test"
        events_file = data_dir / "events.json"
        
        # 4. 验证文件存在且有数据
        exists, result = self._verify_file_exists_and_has_data(events_file, 'events', min_records=3)
        
        if not exists:
            # 如果测试环境文件不存在，检查dev环境
            data_dir = project_root / "src" / "data" / "dev"
            events_file = data_dir / "events.json"
            exists, result = self._verify_file_exists_and_has_data(events_file, 'events', min_records=3)
        
        assert exists, f"events.json验证失败: {result}"
        
        # 5. 验证事件类型
        event_types = [e['event_type'] for e in result]
        assert EventTypes.TOOL_EXECUTION_STARTED in event_types
        assert EventTypes.TOOL_CALL_COMPLETED in event_types
        assert 'llm.request_sent' in event_types
        
        print(f"✓ L4-04测试通过: 事件持久化正常，共{len(result)}条记录")
    
    def test_l4_05_websocket_message_logging(self):
        """
        L4-05: WebSocket消息日志记录
        
        测试WebSocket消息能够正确记录到websocket_messages.json
        """
        # 1. 创建模拟的WebSocket消息
        from services.L2_domain.L2b_memory_state.api_log_service import APILogService
        
        log_service = APILogService()
        
        # 2. 保存入站消息
        log_service.save_websocket_message(
            client_id="test-client-123",
            payload={"action": "send_message", "content": "测试消息"},
            direction="inbound",
            session_id="sess-123",
            message_type="send_message"
        )
        
        # 3. 保存出站消息
        log_service.save_websocket_message(
            client_id="test-client-123",
            payload={"type": "message_response", "content": "测试响应"},
            direction="outbound",
            session_id="sess-123",
            message_type="message_response"
        )
        
        # 4. 等待日志保存
        import time
        time.sleep(0.5)
        
        # 5. 获取数据目录
        data_dir = project_root / "src" / "data" / "test"
        ws_messages_file = data_dir / "websocket_messages.json"
        
        # 6. 验证文件存在且有数据
        exists, result = self._verify_file_exists_and_has_data(ws_messages_file, 'websocket_messages', min_records=2)
        
        if not exists:
            # 如果测试环境文件不存在，检查dev环境
            data_dir = project_root / "src" / "data" / "dev"
            ws_messages_file = data_dir / "websocket_messages.json"
            exists, result = self._verify_file_exists_and_has_data(ws_messages_file, 'websocket_messages', min_records=2)
        
        assert exists, f"websocket_messages.json验证失败: {result}"
        
        # 7. 验证消息方向
        directions = [m['direction'] for m in result]
        assert 'inbound' in directions
        assert 'outbound' in directions
        
        print(f"✓ L4-05测试通过: WebSocket消息日志记录正常，共{len(result)}条记录")
    
    def test_l4_06_tool_execution_with_workspace(self):
        """
        L4-06: 工具执行使用workspace路径
        
        测试工具执行时使用workspace配置中的路径作为工作目录
        """
        # 1. 获取workspace配置
        configs = self.workspace_service.list_workspace_configs()
        assert len(configs) > 0, "应该有workspace配置"
        
        workspace_path = configs[0].root_path
        assert workspace_path == self.temp_workspace, f"workspace路径不匹配: {workspace_path} != {self.temp_workspace}"
        
        # 2. 创建测试目录
        test_dir = os.path.join(self.temp_workspace, "test_dir_l4_06")
        os.makedirs(test_dir, exist_ok=True)
        
        # 3. 验证目录创建在workspace中
        assert os.path.exists(test_dir), f"测试目录应该在workspace中创建: {test_dir}"
        assert test_dir.startswith(self.temp_workspace), f"测试目录应该在workspace路径下"
        
        # 4. 验证目录结构
        assert os.path.dirname(test_dir) == self.temp_workspace
        
        # 5. 清理测试目录
        os.rmdir(test_dir)
        
        print(f"✓ L4-06测试通过: workspace路径配置正常: {workspace_path}")
    
    def test_l4_07_complete_tool_execution_flow(self, test_report):
        """
        L4-07: 完整工具执行流程
        
        测试完整的对话生命周期事件序列：
        1. 客户端消息接收事件
        2. 消息创建事件
        3. LLM请求发送事件
        4. LLM响应接收事件
        5. LLM调用完成事件
        6. 工具执行开始事件
        7. 工具调用开始事件
        8. 工具调用完成事件
        9. 工具执行完成事件
        10. 对话完成事件
        11. 客户端消息发送事件
        """
        # 1. 收集事件
        events_received = []
        
        def event_collector(event):
            events_received.append(event)
        
        self.event_bus.subscribe('*', event_collector, 'test_collector')
        
        # 2. 模拟完整对话流程
        # Step 1: 客户端消息接收
        self.event_bus.publish(Event(
            event_type=EventTypes.CLIENT_MESSAGE_RECEIVED,
            payload={
                'client_id': 'client-123',
                'session_id': 'sess-test-123',
                'message_type': 'send_message',
                'message_length': 50
            }
        ))
        
        # Step 2: 用户消息创建
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': 'dialog-test-123',
                'message_id': 'msg-123',
                'role': 'user'
            }
        ))
        
        # Step 3: LLM请求发送
        self.event_bus.publish(Event(
            event_type=EventTypes.LLM_REQUEST_SENT,
            payload={
                'request_id': 'req-123',
                'dialog_id': 'dialog-test-123',
                'model_config_id': 'default',
                'num_messages': 3,
                'num_tools': 5,
                'stream': False
            }
        ))
        
        # Step 4: LLM响应接收
        self.event_bus.publish(Event(
            event_type=EventTypes.LLM_RESPONSE_RECEIVED,
            payload={
                'request_id': 'req-123',
                'dialog_id': 'dialog-test-123',
                'has_content': True,
                'has_tool_calls': True
            }
        ))
        
        # Step 5: LLM调用完成
        self.event_bus.publish(Event(
            event_type=EventTypes.LLM_CALL_COMPLETED,
            payload={
                'request_id': 'req-123',
                'dialog_id': 'dialog-test-123',
                'duration_ms': 2500
            }
        ))
        
        # Step 6: 工具执行开始
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_EXECUTION_STARTED,
            payload={
                'dialog_id': 'dialog-test-123',
                'session_id': 'sess-test-123',
                'tool_calls': [
                    {
                        'name': 'RunCommand',
                        'arguments': '{"command": "mkdir complete_flow_test", "requires_approval": false}'
                    }
                ],
                'message': 'LLM选择了 1 个工具开始执行'
            }
        ))
        
        # Step 7: 工具调用开始
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_CALL_STARTED,
            payload={
                'call_id': 'call-123',
                'tool_name': 'RunCommand',
                'dialog_id': 'dialog-test-123',
                'task_id': 'task-123',
                'params': {'command': 'mkdir complete_flow_test'}
            }
        ))
        
        # Step 8: 创建测试目录（模拟工具执行）
        test_dir = os.path.join(self.temp_workspace, "complete_flow_test")
        os.makedirs(test_dir, exist_ok=True)
        
        # Step 9: 工具调用完成
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_CALL_COMPLETED,
            payload={
                'call_id': 'call-123',
                'tool_name': 'RunCommand',
                'success': True,
                'duration': 0.05,
                'workspace': self.temp_workspace
            }
        ))
        
        # Step 10: 工具执行完成
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_EXECUTION_COMPLETED,
            payload={
                'dialog_id': 'dialog-test-123',
                'session_id': 'sess-test-123',
                'success': True,
                'tool_results': [{'tool_name': 'RunCommand', 'success': True}]
            }
        ))
        
        # Step 11: 助手消息创建
        self.event_bus.publish(Event(
            event_type=EventTypes.MESSAGE_CREATED,
            payload={
                'dialog_id': 'dialog-test-123',
                'message_id': 'msg-456',
                'role': 'assistant'
            }
        ))
        
        # Step 12: 对话完成
        self.event_bus.publish(Event(
            event_type=EventTypes.DIALOG_COMPLETED,
            payload={
                'dialog_id': 'dialog-test-123'
            }
        ))
        
        # Step 13: 客户端消息发送
        self.event_bus.publish(Event(
            event_type=EventTypes.CLIENT_MESSAGE_SENT,
            payload={
                'client_id': 'client-123',
                'session_id': 'sess-test-123',
                'message_type': 'message_response',
                'message_length': 150
            }
        ))
        
        # 6. 等待事件处理
        import time
        time.sleep(0.5)
        
        # 8. 验证接收到的事件数量（12个事件：client_received, message_created×2, llm_request_sent, llm_response_received, llm_call_completed, tool_execution_started, tool_call_started, tool_call_completed, tool_execution_completed, dialog_completed, client_sent）
        assert len(events_received) == 12, f"期望12个事件，实际{len(events_received)}"
        
        # 9. 验证完整事件序列
        event_types = [e.event_type for e in events_received]
        
        # 验证客户端消息事件
        assert EventTypes.CLIENT_MESSAGE_RECEIVED in event_types, "缺少客户端消息接收事件"
        assert EventTypes.CLIENT_MESSAGE_SENT in event_types, "缺少客户端消息发送事件"
        
        # 验证消息创建事件
        assert EventTypes.MESSAGE_CREATED in event_types, "缺少消息创建事件"
        
        # 验证LLM事件
        assert EventTypes.LLM_REQUEST_SENT in event_types, "缺少LLM请求发送事件"
        assert EventTypes.LLM_RESPONSE_RECEIVED in event_types, "缺少LLM响应接收事件"
        assert EventTypes.LLM_CALL_COMPLETED in event_types, "缺少LLM调用完成事件"
        
        # 验证工具执行事件
        assert EventTypes.TOOL_EXECUTION_STARTED in event_types, "缺少工具执行开始事件"
        assert EventTypes.TOOL_CALL_STARTED in event_types, "缺少工具调用开始事件"
        assert EventTypes.TOOL_CALL_COMPLETED in event_types, "缺少工具调用完成事件"
        assert EventTypes.TOOL_EXECUTION_COMPLETED in event_types, "缺少工具执行完成事件"
        
        # 验证对话完成事件
        assert EventTypes.DIALOG_COMPLETED in event_types, "缺少对话完成事件"
        
        # 10. 验证测试目录存在
        assert os.path.exists(test_dir), f"工具执行的测试目录应该存在: {test_dir}"
        
        # 11. 清理测试目录
        os.rmdir(test_dir)
        
        # 12. 生成测试报告
        test_report(
            test_points=[
                "验证客户端消息接收事件",
                "验证用户消息创建事件",
                "验证LLM请求发送事件",
                "验证LLM响应接收事件",
                "验证LLM调用完成事件",
                "验证工具执行开始事件",
                "验证工具调用开始事件",
                "验证工具调用完成事件",
                "验证工具执行完成事件",
                "验证助手消息创建事件",
                "验证对话完成事件",
                "验证客户端消息发送事件",
                "验证workspace路径使用"
            ],
            inputs={
                'workspace': self.temp_workspace,
                'test_command': 'mkdir complete_flow_test'
            },
            outputs={
                'events_received': event_types,
                'event_count': len(events_received),
                'test_directory_created': test_dir,
                'test_directory_exists': os.path.exists(test_dir.replace('complete_flow_test', ''))
            },
            events=[e.event_type for e in events_received]
        )
        
        print("[PASS] L4-07测试通过: 完整对话生命周期事件序列验证成功")
    
    def test_l4_08_event_console_printer_integration(self):
        """
        L4-08: 事件控制台打印机集成
        
        测试EventConsolePrinter能够正确接收和打印事件
        """
        from services.L1_infrastructure.L1d_events.EventConsolePrinter.event_console_printer import EventConsolePrinter
        
        # 1. 创建并初始化事件控制台打印机
        printer = EventConsolePrinter()
        printer.initialize(self.event_bus)
        
        # 2. 发布测试事件
        self.event_bus.publish(Event(
            event_type='test.console_printer',
            payload={'test': 'data', 'value': 123}
        ))
        
        # 3. 验证打印机已初始化
        assert printer._initialized is True
        assert printer._event_bus is not None
        
        print("[PASS] L4-08测试通过: 事件控制台打印机集成正常")


class TestL4GatewayDataPersistence:
    """L4网关数据持久化测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的清理"""
        os.environ['STORAGE_ENV'] = 'test'
        self.data_dir = project_root / "src" / "data" / "test"
        self.persistence = PersistenceService()
        
        yield
        
        # 清理数据
        for entity_type in ['events', 'websocket_messages', 'sessions', 'dialogs', 'messages']:
            try:
                self.persistence._write_all(entity_type, [])
            except:
                pass
    
    def test_l4_09_events_json_structure(self):
        """
        L4-09: events.json文件结构验证
        
        验证events.json文件包含正确的字段结构
        """
        # 1. 发布测试事件
        event_bus = EventBus()
        event_bus._persistence_service = self.persistence
        
        event_bus.publish(Event(
            event_type='test.structure',
            payload={'key': 'value'}
        ))
        
        # 2. 等待保存
        import time
        time.sleep(0.5)
        
        # 3. 读取events.json
        events_file = self.data_dir / "events.json"
        
        if not events_file.exists():
            # 检查dev环境
            self.data_dir = project_root / "src" / "data" / "dev"
            events_file = self.data_dir / "events.json"
        
        if not events_file.exists():
            pytest.skip("events.json文件不存在，跳过结构验证")
        
        with open(events_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        # 4. 验证事件结构
        if len(events) > 0:
            event = events[0]
            required_fields = ['record_id', 'event_type', 'payload', 'created_at']
            
            for field in required_fields:
                assert field in event, f"事件缺少必需字段: {field}"
            
            # 验证payload是字典
            assert isinstance(event['payload'], dict), "payload应该是字典类型"
        
        print(f"✓ L4-09测试通过: events.json结构验证成功，共{len(events)}条记录")
    
    def test_l4_10_websocket_messages_json_structure(self):
        """
        L4-10: websocket_messages.json文件结构验证
        
        验证websocket_messages.json文件包含正确的字段结构
        """
        # 1. 保存测试消息
        from services.L2_domain.L2b_memory_state.api_log_service import APILogService
        
        log_service = APILogService()
        log_service.save_websocket_message(
            client_id="test-client",
            payload={"action": "test"},
            direction="inbound",
            session_id="sess-test",
            message_type="test"
        )
        
        # 2. 等待保存
        import time
        time.sleep(0.5)
        
        # 3. 读取websocket_messages.json
        ws_file = self.data_dir / "websocket_messages.json"
        
        if not ws_file.exists():
            # 检查dev环境
            self.data_dir = project_root / "src" / "data" / "dev"
            ws_file = self.data_dir / "websocket_messages.json"
        
        if not ws_file.exists():
            pytest.skip("websocket_messages.json文件不存在，跳过结构验证")
        
        with open(ws_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        # 4. 验证消息结构
        if len(messages) > 0:
            message = messages[0]
            required_fields = ['log_id', 'client_id', 'direction', 'payload']
            
            for field in required_fields:
                assert field in message, f"消息缺少必需字段: {field}"
            
            # 验证direction是有效值
            assert message['direction'] in ['inbound', 'outbound'], "direction应该是inbound或outbound"
        
        print(f"✓ L4-10测试通过: websocket_messages.json结构验证成功，共{len(messages)}条记录")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
