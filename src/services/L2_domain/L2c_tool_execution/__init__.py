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

from .tool_executor import ToolExecutor, ToolCall, ToolResult


def get_tool_executor() -> ToolExecutor:
    """获取工具执行器实例"""
    return ToolExecutor()
