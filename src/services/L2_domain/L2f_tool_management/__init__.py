"""
L2f Tool Management Service

L2f 工具管理服务负责管理工具的定义、注册、配置和查询。

职责：
- 工具注册：注册新的工具及其实现
- 工具配置：管理工具的参数配置和元数据
- 工具查询：按类别、名称等条件查询工具
- 工具调度：判断工具类型并调度执行

依赖 L1 层：
- L1b 持久化服务：用于存储工具配置
- L1d 事件系统：发布工具注册事件
"""

from .tool_management import (
    ToolManagementService,
    ToolRegistry,
    ToolDefinition,
    ToolExecutionRecord
)


def get_tool_management_service() -> ToolManagementService:
    """获取工具管理服务实例"""
    return ToolManagementService()


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    return ToolRegistry.get_instance()
