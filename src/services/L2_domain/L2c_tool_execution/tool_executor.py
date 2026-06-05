"""
L2c Tool Execution Service - ToolExecutor Implementation

工具执行服务负责统一的工具执行调度和结果返回。
"""

import time
import asyncio
import threading
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.L1_infrastructure.L1a_id_generator.id_generator import generate_call_id
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes
from services.L2_domain.L2f_tool_management import ToolManagementService, ToolDefinition
from src.tools.implement.tool_registry import ToolRegistry


@dataclass
class ToolCall:
    call_id: str
    tool_call_id: str  # LLM返回的原始工具调用ID（符合OpenAI API标准）
    tool_id: str
    tool_name: str
    dialog_id: str
    task_id: str
    input_params: Dict[str, Any] = field(default_factory=dict)
    output_result: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0

    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCall':
        return cls(**data)


@dataclass
class ToolResult:
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    call_id: str = ""
    status: str = "done"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolResult':
        return cls(**data)

    @staticmethod
    def done(result: str, call_id: str = "") -> 'ToolResult':
        return ToolResult(success=True, result=result, call_id=call_id, status="done")

    @staticmethod
    def failed(error: str, call_id: str = "") -> 'ToolResult':
        return ToolResult(success=False, error=error, call_id=call_id, status="failed")

    @staticmethod
    def timeout(call_id: str = "") -> 'ToolResult':
        return ToolResult(success=False, error="Tool execution timeout", call_id=call_id, status="timeout")

    @staticmethod
    def cancelled(call_id: str = "") -> 'ToolResult':
        return ToolResult(success=False, error="Tool execution cancelled", call_id=call_id, status="cancelled")

    @staticmethod
    def invalid_params(error: str, call_id: str = "") -> 'ToolResult':
        return ToolResult(success=False, error=error, call_id=call_id, status="invalid_params")

    @staticmethod
    def partial_done(result: str, call_id: str = "") -> 'ToolResult':
        return ToolResult(success=True, result=result, call_id=call_id, status="partial_done")


class ToolExecutor:
    def __init__(self, persistence_service=None, event_bus=None, tool_service: ToolManagementService = None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()
        self.tool_service = tool_service or ToolManagementService()
        self.registry = ToolRegistry.get_instance()
        self.executor = ThreadPoolExecutor(max_workers=10)
        self._async_calls: Dict[str, ToolCall] = {}
        self._current_session_id = ""
        self._current_request_id = ""  # 驱动当前工具调用的LLM请求ID
        # 用于跟踪每个工具调用的已输出内容长度（实现增量输出）
        self._output_tracker: Dict[str, int] = {}

    def _validate_params(self, tool: ToolDefinition, params: Dict[str, Any]) -> Optional[str]:
        required_params = tool.parameters.get('required', [])
        for param in required_params:
            if param not in params:
                return f"Missing required parameter: {param}"
        return None

    def execute_tool(self, tool_name: str, dialog_id: str, task_id: str,
                    params: Dict[str, Any], session_id: str = "", tool_call_id: str = "",
                    request_id: str = "") -> ToolResult:
        # 设置当前会话ID（用于事件发布）
        if session_id:
            self._current_session_id = session_id
        
        # 保存request_id（驱动当前工具调用的LLM请求ID）
        self._current_request_id = request_id
        
        tool = self.tool_service.get_tool(tool_name)
        if not tool:
            tool = self.registry.get_tool(tool_name)
        if not tool:
            # 尝试使用配置驱动的注册表
            config_registry = self._get_config_driven_registry()
            if config_registry:
                config_tool = config_registry.get_tool(tool_name)
                if config_tool:
                    # 创建临时的ToolDefinition对象用于验证参数
                    from src.services.L2_domain.L2f_tool_management import ToolDefinition
                    tool = ToolDefinition(
                        tool_id=config_tool.tool_id,
                        tool_name=config_tool.name,
                        category=config_tool.category,
                        description=config_tool.description,
                        parameters=config_tool.parameters
                    )

        if not tool:
            return ToolResult.failed(f"Tool not found: {tool_name}")

        validation_error = self._validate_params(tool, params)
        if validation_error:
            return ToolResult.invalid_params(validation_error)

        call = ToolCall(
            call_id=generate_call_id(),
            tool_call_id=tool_call_id,  # 传递LLM原始调用ID（符合OpenAI API标准）
            tool_id=tool.tool_id,
            tool_name=tool_name,
            dialog_id=dialog_id,
            task_id=task_id,
            input_params=params,
            status="executing"
        )

        self._save_call_record(call)

        start_time = time.time()

        try:
            # 发布工具调用开始事件
            self.event_bus.publish(Event(
                event_type=EventTypes.TOOL_CALL_STARTED,
                payload={
                    'call_id': call.call_id,
                    'tool_call_id': tool_call_id,  # 传递LLM原始调用ID（符合OpenAI API标准），用于前后台映射
                    'request_id': self._current_request_id,  # 驱动当前工具调用的LLM请求ID
                    'tool_name': tool_name,
                    'dialog_id': dialog_id,
                    'task_id': task_id,
                    'session_id': self._current_session_id,
                    'params': params,
                    'source_component': 'L2_tool_execution',
                    'source_service': 'ToolExecutor'
                }
            ))
            
            # 获取workspace路径并注入到参数中
            workspace_path = self._get_workspace_path()
            
            # 创建输出回调函数，用于实时捕获工具输出
            output_callback = lambda chunk: self._on_tool_output(call.call_id, tool_name, chunk)
            params_with_workspace = {**params, 'workspace': workspace_path, 'output_callback': output_callback}
            
            print(f"[ToolExecutor] 执行工具 {tool_name}，workspace: {workspace_path}")
            
            # 使用配置驱动的注册表获取真实工具实现
            config_registry = self._get_config_driven_registry()
            tool_instance = None
            
            # 优先使用配置驱动的注册表
            if config_registry:
                tool_instance = config_registry.get_tool(tool.tool_id)
                if not tool_instance:
                    tool_instance = config_registry.get_tool(tool_name)
            
            # 如果配置驱动注册表中找不到，回退到普通注册表获取实现
            if not tool_instance:
                # 使用 ToolRegistry 的 get_tool 方法获取工具实例
                tool_instance = self.registry.get_tool(tool.tool_id)
                if not tool_instance:
                    tool_instance = self.registry.get_tool(tool_name)
            
            if tool_instance:
                # 检查是否有execute方法（配置驱动的工具）
                if hasattr(tool_instance, 'execute'):
                    result = tool_instance.execute(params_with_workspace)
                else:
                    # 直接调用工具函数（用于测试注册的函数）
                    result = tool_instance(**params_with_workspace)
            else:
                raise Exception(f"Tool implementation not found for: {tool_name} (ID: {tool.tool_id})")
            
            # 注意：实时输出已通过 output_callback 回调在工具执行过程中实时发送
            # 这里不再需要额外发布输出事件
            
            # 发送输出结束事件
            self._publish_output_end(call.call_id, tool_name)

            end_time = time.time()
            duration = end_time - start_time

            # 检查工具返回结果是否表示失败
            # 工具可能执行成功（没有抛异常），但返回结果中包含错误信息
            is_failure = False
            error_message = None
            error_detail = None

            if isinstance(result, dict):
                # 检查 success 字段
                if result.get('success') is False:
                    is_failure = True
                    error_message = f"Tool execution failed: {result.get('error', 'Unknown error')}"
                    error_detail = result.get('stderr') or result.get('error')
                # 检查 return_code 字段（Unix命令）
                elif result.get('return_code') is not None and result.get('return_code') != 0:
                    is_failure = True
                    error_message = f"Command failed with return code {result.get('return_code')}"
                    error_detail = result.get('stderr')
                # 检查 error 字段（某些工具可能直接返回 error 字段）
                elif result.get('error') is not None and result.get('error') != '':
                    is_failure = True
                    error_message = f"Tool execution failed: {result.get('error')}"
                    error_detail = result.get('error')

            if is_failure:
                # 工具执行失败
                call.status = "failed"
                call.output_result = str(result)
                call.error_message = error_message
                call.end_time = datetime.now().isoformat()
                call.duration = duration
                self._update_call_record(call)

                # 保存工具执行结果到 tool_result.json
                self._save_tool_result(call.call_id, result, "failed")

                self.event_bus.publish(Event(
                    event_type=EventTypes.TOOL_CALL_COMPLETED,
                    payload={
                        'call_id': call.call_id,
                        'tool_call_id': tool_call_id,  # 传递LLM原始调用ID（符合OpenAI API标准），用于前后台映射
                        'request_id': self._current_request_id,  # 驱动当前工具调用的LLM请求ID
                        'tool_name': tool_name,
                        'success': False,  # 修正：标记为失败
                        'duration': duration,
                        'workspace': workspace_path,
                        'result': None,  # 失败时不返回结果
                        'error': error_detail or error_message,  # 修正：错误信息放入 error 字段
                        'session_id': self._current_session_id,
                        'source_component': 'L2_tool_execution',
                        'source_service': 'ToolExecutor'
                    }
                ))

                return ToolResult.failed(error_detail or error_message, call.call_id)
            else:
                # 工具执行成功
                call.status = "completed"
                call.output_result = str(result)
                call.end_time = datetime.now().isoformat()
                call.duration = duration
                self._update_call_record(call)

                # 保存工具执行结果到 tool_result.json
                self._save_tool_result(call.call_id, result, "done")

                self.event_bus.publish(Event(
                    event_type=EventTypes.TOOL_CALL_COMPLETED,
                    payload={
                        'call_id': call.call_id,
                        'tool_call_id': tool_call_id,  # 传递LLM原始调用ID（符合OpenAI API标准），用于前后台映射
                        'request_id': self._current_request_id,  # 驱动当前工具调用的LLM请求ID
                        'tool_name': tool_name,
                        'success': True,
                        'duration': duration,
                        'workspace': workspace_path,
                        'result': str(result),
                        'error': None,
                        'session_id': self._current_session_id,
                        'source_component': 'L2_tool_execution',
                        'source_service': 'ToolExecutor'
                    }
                ))

                return ToolResult.done(str(result), call.call_id)

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            call.status = "failed"
            call.error_message = str(e)
            call.end_time = datetime.now().isoformat()
            call.duration = duration
            self._update_call_record(call)
            
            # 保存工具执行结果到 tool_result.json
            self._save_tool_result(call.call_id, str(e), "failed")

            self.event_bus.publish(Event(
                event_type=EventTypes.TOOL_CALL_FAILED,
                payload={
                    'call_id': call.call_id,
                    'tool_call_id': tool_call_id,  # 传递LLM原始调用ID（符合OpenAI API标准），用于前后台映射
                    'request_id': self._current_request_id,  # 驱动当前工具调用的LLM请求ID
                    'tool_name': tool_name,
                    'success': False,
                    'error': str(e),
                    'duration': duration,
                    'session_id': self._current_session_id,
                    'source_component': 'L2_tool_execution',
                    'source_service': 'ToolExecutor'
                }
            ))

            return ToolResult.failed(str(e), call.call_id)
    
    def execute_tool_with_message_format(self, tool_call: Dict, context: Dict) -> Dict:
        """
        执行工具调用并返回role: "tool"消息格式的结果
        
        Args:
            tool_call: 工具调用定义，包含id、name、arguments（支持LLM返回的格式）
            context: 执行上下文
            
        Returns:
            工具执行结果，格式为role: "tool"的消息
        """
        # 使用LLM生成的原始ID，不改写（优先从不同字段获取）
        tool_call_id = tool_call.get('id') or tool_call.get('call_id', '')
        
        # 如果仍没有提供tool_call_id，则生成一个（作为降级方案）
        # 注意：这里生成的是符合LLM格式的ID（call_xxx），不是系统call_id
        if not tool_call_id:
            import uuid
            tool_call_id = f"call_{uuid.uuid4().hex[:12]}"
        
        # 支持多种工具调用格式
        # 格式1: {"id": "call_xxx", "name": "tool_name", "arguments": {...}}
        # 格式2: {"function": {"name": "tool_name", "arguments": {...}}}
        # 格式3: {"tool_calls": [{"id": "call_xxx", "function": {...}}]}
        
        tool_name = ""
        arguments = {}
        
        # 尝试从不同格式中提取工具名称和参数
        if 'function' in tool_call:
            # 格式2
            tool_name = tool_call['function'].get('name', '')
            arguments = tool_call['function'].get('arguments', {})
        elif 'name' in tool_call:
            # 格式1
            tool_name = tool_call['name']
            arguments = tool_call.get('arguments', {})
        elif 'tool_calls' in tool_call and tool_call['tool_calls']:
            # 格式3 - 多个工具调用（取第一个）
            first_call = tool_call['tool_calls'][0]
            if 'function' in first_call:
                tool_name = first_call['function'].get('name', '')
                arguments = first_call['function'].get('arguments', {})
                # 从第一个工具调用获取ID
                tool_call_id = first_call.get('id') or tool_call_id
        
        # 解析arguments（可能是字符串或字典）
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}
        
        # 获取dialog_id和task_id
        dialog_id = context.get('dialog_id', '')
        task_id = context.get('task_id', '')
        session_id = context.get('session_id', '')
        request_id = context.get('request_id', '')  # 获取驱动当前工具调用的LLM请求ID
        
        # 执行工具，传递LLM原始调用ID和request_id（符合OpenAI API标准）
        result = self.execute_tool(tool_name, dialog_id, task_id, arguments, session_id, tool_call_id, request_id)
        
        # 封装为tool role消息（符合OpenAI API标准）
        tool_message = {
            "role": "tool",
            "tool_call_id": tool_call_id,  # 使用LLM原始调用ID（符合OpenAI API标准）
            "content": self._format_tool_result_for_message(result)
        }
        
        return tool_message
    
    def _format_tool_result_for_message(self, result: ToolResult) -> str:
        """
        将工具执行结果格式化为消息内容
        
        Args:
            result: 工具执行结果
            
        Returns:
            格式化的工具结果内容
        """
        if result.success:
            return f'<toolcall_status>done</toolcall_status>\n<toolcall_result>\n{result.result}\n</toolcall_result>'
        else:
            return f'<toolcall_status>failed</toolcall_status>\n<toolcall_result>\n{result.error}\n</toolcall_result>'
    
    def _get_config_driven_registry(self):
        """
        获取配置驱动的工具注册器实例
        
        Returns:
            ConfigDrivenToolRegistry实例，如果加载失败则返回None
        """
        try:
            from src.tools.implement.config_driven_registry import ConfigDrivenToolRegistry
            return ConfigDrivenToolRegistry()
        except Exception as e:
            print(f"[ToolExecutor] 加载配置驱动注册器失败: {e}")
            return None
    
    def _get_workspace_path(self) -> str:
        """
        获取当前workspace路径
        
        优先从workspace配置中获取，如果没有配置则使用应用当前目录
        
        Returns:
            workspace绝对路径
        """
        try:
            # 尝试从workspace配置服务获取
            from services.L2_domain.L2a_project_config.workspace_config_service import WorkspaceConfigService
            
            workspace_service = WorkspaceConfigService()
            configs = workspace_service.list_workspace_configs()
            
            if configs:
                # 返回第一个配置的路径（可以优化为根据session/dialog获取对应的workspace）
                return configs[0].root_path
        except Exception as e:
            print(f"[ToolExecutor] 获取workspace配置失败: {e}")
        
        # 降级：使用应用当前目录
        return os.path.abspath(os.getcwd())

    def execute_async(self, tool_name: str, dialog_id: str, task_id: str,
                     params: Dict[str, Any]) -> str:
        tool = self.tool_service.get_tool(tool_name)
        if not tool:
            return ""

        call = ToolCall(
            call_id=generate_call_id(),
            tool_id=tool.tool_id,
            tool_name=tool_name,
            dialog_id=dialog_id,
            task_id=task_id,
            input_params=params,
            status="pending"
        )

        self._async_calls[call.call_id] = call
        self._save_call_record(call)

        self.executor.submit(self._execute_async_task, call.call_id, tool_name, params)

        return call.call_id

    def _execute_async_task(self, call_id: str, tool_name: str, params: Dict[str, Any]):
        call = self._async_calls.get(call_id)
        if not call:
            return

        call.status = "executing"
        self._update_call_record(call)

        # 使用 dialog_id 作为 session_id（在当前设计中它们是相同的）
        result = self.execute_tool(tool_name, call.dialog_id, call.task_id, params, session_id=call.dialog_id)

        call.status = "completed" if result.success else "failed"
        if not result.success:
            call.error_message = result.error
        self._update_call_record(call)

    def get_call_status(self, call_id: str) -> Optional[ToolCall]:
        all_calls = self.persistence.list('tool_calls')
        for c in all_calls:
            if c.get('call_id') == call_id:
                return ToolCall.from_dict(c)
        return self._async_calls.get(call_id)

    def cancel_call(self, call_id: str) -> bool:
        call = self.get_call_status(call_id)
        if not call:
            return False

        if call.status in ["completed", "failed"]:
            return False

        call.status = "cancelled"
        call.end_time = datetime.now().isoformat()
        self._update_call_record(call)

        if call_id in self._async_calls:
            del self._async_calls[call_id]

        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_CALL_CANCELLED,
            payload={'call_id': call_id}
        ))

        return True

    def list_calls(self, dialog_id: str = None, task_id: str = None) -> List[ToolCall]:
        all_calls = self.persistence.list('tool_calls')
        result = [ToolCall.from_dict(c) for c in all_calls]

        if dialog_id:
            result = [c for c in result if c.dialog_id == dialog_id]
        if task_id:
            result = [c for c in result if c.task_id == task_id]

        return result

    def _save_call_record(self, call: ToolCall):
        self.persistence.save('tool_calls', call.to_dict())
    
    def _save_tool_result(self, call_id: str, result: Any, status: str):
        """保存工具执行结果到 tool_result.json"""
        # 读取现有的工具执行结果
        try:
            tool_results = self.persistence.list('tool_result')
        except:
            tool_results = []
        
        # 创建新的工具执行结果记录
        tool_result_record = {
            'role': 'tool',
            'content': f'<toolcall_status>{status}</toolcall_status>\n<toolcall_result>\n{str(result)}\n</toolcall_result>',
            'tool_call_id': call_id
        }
        
        # 添加到列表中
        tool_results.append(tool_result_record)
        
        # 保存到文件
        self.persistence._write_all('tool_result', tool_results)

    def _update_call_record(self, call: ToolCall):
        all_calls = self.persistence.list('tool_calls')
        for i, c in enumerate(all_calls):
            if c.get('call_id') == call.call_id:
                all_calls[i] = call.to_dict()
                break
        else:
            all_calls.append(call.to_dict())
        self.persistence._write_all('tool_calls', all_calls)
    
    def _on_tool_output(self, call_id: str, tool_name: str, chunk: str):
        """
        处理工具实时输出（增量输出模式）
        
        Args:
            call_id: 工具调用ID
            tool_name: 工具名称
            chunk: 输出块内容（可能是完整输出或增量输出）
        """
        if not chunk or len(chunk.strip()) == 0:
            return
        
        # 获取该调用已输出的长度
        last_output_length = self._output_tracker.get(call_id, 0)
        current_length = len(chunk)
        
        # 获取 tool_call_id（从调用记录中查找）
        tool_call_id = self._get_tool_call_id(call_id)
        
        # 计算增量部分
        if current_length > last_output_length:
            # 只发送新增的部分
            incremental_output = chunk[last_output_length:]
            
            # 更新已输出长度
            self._output_tracker[call_id] = current_length
            
            # 只有当有增量时才发布事件
            if incremental_output and len(incremental_output.strip()) > 0:
                self.event_bus.publish(Event(
                    event_type=EventTypes.TOOL_EXECUTION_OUTPUT,
                    payload={
                        'call_id': call_id,
                        'tool_call_id': tool_call_id,  # 添加LLM原始调用ID
                        'tool_name': tool_name,
                        'output': incremental_output,
                        'output_type': 'stdout',
                        'session_id': self._current_session_id,
                        'source_component': 'L2_tool_execution',
                        'source_service': 'ToolExecutor',
                        'is_incremental': True,  # 标识这是增量输出
                        'total_length': current_length  # 当前总长度
                    }
                ))
        else:
            # 如果没有增量或长度减少，不发送输出
            print(f"[ToolExecutor] No incremental output for call {call_id}, last={last_output_length}, current={current_length}")
    
    def _get_tool_call_id(self, call_id: str) -> str:
        """
        根据 call_id 获取对应的 tool_call_id（LLM原始调用ID）
        
        Args:
            call_id: 工具执行实例ID
            
        Returns:
            LLM原始调用ID，如果未找到则返回空字符串
        """
        try:
            all_calls = self.persistence.list('tool_calls')
            for call in all_calls:
                if call.get('call_id') == call_id:
                    return call.get('tool_call_id', '')
        except Exception as e:
            print(f"[ToolExecutor] 获取 tool_call_id 失败: {e}")
        return ""
    
    def _publish_tool_output_from_result(self, call_id: str, tool_name: str, result: Any):
        """
        从工具执行结果中提取输出并发布事件
        
        Args:
            call_id: 工具调用ID
            tool_name: 工具名称
            result: 工具执行结果
        """
        if not result:
            return
        
        # 获取 tool_call_id（从调用记录中查找）
        tool_call_id = self._get_tool_call_id(call_id)
        
        # 从结果中提取输出内容
        output_content = None
        
        # 处理字典格式的结果
        if isinstance(result, dict):
            # 优先从 stdout 字段提取
            if 'stdout' in result and result['stdout']:
                output_content = result['stdout']
            # 其次从 result 字段提取
            elif 'result' in result and result['result']:
                output_content = str(result['result'])
            # 从 content 字段提取
            elif 'content' in result and result['content']:
                output_content = result['content']
            # 从 output 字段提取
            elif 'output' in result and result['output']:
                output_content = result['output']
        
        # 如果没有找到标准输出字段且结果是字符串，直接使用
        if not output_content and isinstance(result, str):
            output_content = result
        
        # 如果有输出内容，发布输出事件
        if output_content and len(output_content.strip()) > 0:
            self.event_bus.publish(Event(
                event_type=EventTypes.TOOL_EXECUTION_OUTPUT,
                payload={
                    'call_id': call_id,
                    'tool_call_id': tool_call_id,  # 添加LLM原始调用ID
                    'tool_name': tool_name,
                    'output': output_content,
                    'output_type': 'stdout',
                    'session_id': self._current_session_id,
                    'source_component': 'L2_tool_execution',
                    'source_service': 'ToolExecutor'
                }
            ))
    
    def _publish_output_end(self, call_id: str, tool_name: str):
        """
        发布工具输出结束事件
        
        Args:
            call_id: 工具调用ID
            tool_name: 工具名称
        """
        # 获取 tool_call_id（从调用记录中查找）
        tool_call_id = self._get_tool_call_id(call_id)
        
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_EXECUTION_OUTPUT_END,
            payload={
                'call_id': call_id,
                'tool_call_id': tool_call_id,  # 添加LLM原始调用ID
                'tool_name': tool_name,
                'session_id': self._current_session_id,
                'source_component': 'L2_tool_execution',
                'source_service': 'ToolExecutor'
            }
        ))
        
        # 清理该调用的输出追踪，避免内存泄漏
        if call_id in self._output_tracker:
            del self._output_tracker[call_id]
