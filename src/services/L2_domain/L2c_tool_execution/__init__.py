"""
L2c Tool Execution Service

L2c 工具执行服务负责统一的工具执行调度和结果返回。

职责：
- 执行工具调用（同步/异步）
- 处理工具返回结果
- 管理工具执行状态
- 提供工具调用记录
- 调度到具体的工具实现

依赖 L1 层：
- L1b 持久化服务：用于存储工具调用记录
- L1d 事件系统：发布工具调用事件

依赖 L2 层：
- L2f 工具管理服务：获取工具定义和配置
- L2a 领域实体管理：更新任务状态
"""

import uuid
import time
import asyncio
import threading
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from concurrent.futures import ThreadPoolExecutor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes
from services.L2_domain.L2f_tool_management import ToolManagementService, ToolRegistry, ToolDefinition


@dataclass
class ToolCall:
    call_id: str
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

    def _generate_call_id(self) -> str:
        return f"call-{uuid.uuid4().hex[:12]}"

    def _validate_params(self, tool: ToolDefinition, params: Dict[str, Any]) -> Optional[str]:
        required_params = tool.parameters.get('required', [])
        for param in required_params:
            if param not in params:
                return f"Missing required parameter: {param}"
        return None

    def execute_tool(self, tool_name: str, dialog_id: str, task_id: str,
                    params: Dict[str, Any]) -> ToolResult:
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
            call_id=self._generate_call_id(),
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
                    'tool_name': tool_name,
                    'dialog_id': dialog_id,
                    'task_id': task_id,
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
                # ToolRegistry的get_tool返回ToolDefinition，需要用get_implementation获取实际函数
                tool_instance = self.registry.get_implementation(tool.tool_id)
                if not tool_instance:
                    tool_instance = self.registry.get_implementation(tool_name)
            
            if tool_instance:
                # 检查是否有execute方法（配置驱动的工具）
                if hasattr(tool_instance, 'execute'):
                    result = tool_instance.execute(params_with_workspace)
                else:
                    # 直接调用工具函数（用于测试注册的函数）
                    result = tool_instance(**params_with_workspace)
            else:
                raise Exception(f"Tool implementation not found for: {tool_name} (ID: {tool.tool_id})")
            
            # 发送输出结束事件
            self._publish_output_end(call.call_id, tool_name)

            end_time = time.time()
            duration = end_time - start_time

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
                    'tool_name': tool_name,
                    'success': True,
                    'duration': duration,
                    'workspace': workspace_path,
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
                    'tool_name': tool_name,
                    'success': False,
                    'error': str(e),
                    'duration': duration,
                    'source_component': 'L2_tool_execution',
                    'source_service': 'ToolExecutor'
                }
            ))

            return ToolResult.failed(str(e), call.call_id)
    
    def execute_tool_with_message_format(self, tool_call: Dict, context: Dict) -> Dict:
        """
        执行工具调用并返回role: "tool"消息格式的结果
        
        Args:
            tool_call: 工具调用定义，包含id、name、arguments
            context: 执行上下文
            
        Returns:
            工具执行结果，格式为role: "tool"的消息
        """
        tool_call_id = tool_call.get('id', '') or tool_call.get('call_id', '')
        # 如果没有提供tool_call_id，则生成一个
        if not tool_call_id:
            tool_call_id = self._generate_call_id()
        
        tool_name = tool_call.get('name', '')
        arguments = tool_call.get('arguments', {})
        
        # 解析arguments（可能是字符串或字典）
        if isinstance(arguments, str):
            try:
                import json
                arguments = json.loads(arguments)
            except:
                arguments = {}
        
        # 获取dialog_id和task_id
        dialog_id = context.get('dialog_id', '')
        task_id = context.get('task_id', '')
        
        # 执行工具
        result = self.execute_tool(tool_name, dialog_id, task_id, arguments)
        
        # 封装为tool role消息
        tool_message = {
            "role": "tool",
            "tool_call_id": tool_call_id,
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
        import os
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
            call_id=self._generate_call_id(),
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

        result = self.execute_tool(tool_name, call.dialog_id, call.task_id, params)

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
        处理工具实时输出
        
        Args:
            call_id: 工具调用ID
            tool_name: 工具名称
            chunk: 输出块内容
        """
        if chunk and len(chunk.strip()) > 0:
            self.event_bus.publish(Event(
                event_type=EventTypes.TOOL_EXECUTION_OUTPUT,
                payload={
                    'call_id': call_id,
                    'tool_name': tool_name,
                    'output': chunk,
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
        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_EXECUTION_OUTPUT_END,
            payload={
                'call_id': call_id,
                'tool_name': tool_name,
                'source_component': 'L2_tool_execution',
                'source_service': 'ToolExecutor'
            }
        ))


def get_tool_executor() -> ToolExecutor:
    return ToolExecutor()
