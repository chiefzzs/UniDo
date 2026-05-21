"""
Tool Group Executor - 工具组执行器

负责管理和执行大模型返回的多个工具调用，保留原始tool_call_id，统一工具结果格式。
"""

from typing import List, Dict, Any, Optional
from services.L2_domain.L2c_tool_execution import get_tool_executor, ToolExecutor


class ToolGroupExecutor:
    """工具组执行器 - 管理和执行大模型返回的多个工具调用"""
    
    def __init__(self, tool_execution_service: ToolExecutor = None):
        self.tool_execution_service = tool_execution_service or get_tool_executor()
    
    def execute(self, tool_calls: List[Dict], session_id: str, 
                dialog_id: str = "", task_id: str = "") -> List[Dict]:
        """
        执行工具组
        
        Args:
            tool_calls: LLM返回的工具调用列表（保留原始ID）
            session_id: 当前会话ID
            dialog_id: 对话ID（可选）
            task_id: 任务ID（可选）
        
        Returns:
            工具执行结果列表，格式为role="tool"消息
        """
        results = []
        
        for tool_call in tool_calls:
            # 使用LLM生成的原始ID，不修改
            tool_call_id = tool_call.get('id', '')
            tool_name = ''
            arguments = {}
            
            # 支持两种工具调用格式
            if 'function' in tool_call:
                tool_name = tool_call['function'].get('name', '')
                arguments = tool_call['function'].get('arguments', {})
            else:
                tool_name = tool_call.get('name', '')
                arguments = tool_call.get('arguments', {})
            
            # 解析arguments（可能是字符串）
            if isinstance(arguments, str):
                try:
                    import json
                    arguments = json.loads(arguments)
                except:
                    arguments = {}
            
            # 执行工具，使用execute_tool_with_message_format获取role:tool消息格式
            result = self.tool_execution_service.execute_tool_with_message_format(
                tool_call={
                    'id': tool_call_id,
                    'name': tool_name,
                    'arguments': arguments
                },
                context={
                    'session_id': session_id,
                    'dialog_id': dialog_id,
                    'task_id': task_id
                }
            )
            
            results.append(result)
        
        return results


def get_tool_group_executor() -> ToolGroupExecutor:
    """获取工具组执行器实例"""
    return ToolGroupExecutor()
