"""
工具实现模块

此模块包含所有工具的具体实现，支持调试模式下的工具执行。
"""

from .base_tool import BaseTool
from .skill_tool import SkillTool
from .search_codebase_tool import SearchCodebaseTool
from .glob_tool import GlobTool
from .ls_tool import LsTool
from .grep_tool import GrepTool
from .read_tool import ReadTool
from .web_search_tool import WebSearchTool
from .web_fetch_tool import WebFetchTool
from .delete_file_tool import DeleteFileTool
from .search_replace_tool import SearchReplaceTool
from .write_tool import WriteTool
from .run_command_tool import RunCommandTool
from .check_command_status_tool import CheckCommandStatusTool
from .stop_command_tool import StopCommandTool
from .get_diagnostics_tool import GetDiagnosticsTool
from .todo_write_tool import TodoWriteTool
from .open_preview_tool import OpenPreviewTool
from .ask_user_question_tool import AskUserQuestionTool
from .tool_registry import ToolRegistry

__all__ = [
    'BaseTool',
    'SkillTool',
    'SearchCodebaseTool',
    'GlobTool',
    'LsTool',
    'GrepTool',
    'ReadTool',
    'WebSearchTool',
    'WebFetchTool',
    'DeleteFileTool',
    'SearchReplaceTool',
    'WriteTool',
    'RunCommandTool',
    'CheckCommandStatusTool',
    'StopCommandTool',
    'GetDiagnosticsTool',
    'TodoWriteTool',
    'OpenPreviewTool',
    'AskUserQuestionTool',
    'ToolRegistry'
]

# 注册所有工具
registry = ToolRegistry()
registry.register_tool(SkillTool())
registry.register_tool(SearchCodebaseTool())
registry.register_tool(GlobTool())
registry.register_tool(LsTool())
registry.register_tool(GrepTool())
registry.register_tool(ReadTool())
registry.register_tool(WebSearchTool())
registry.register_tool(WebFetchTool())
registry.register_tool(DeleteFileTool())
registry.register_tool(SearchReplaceTool())
registry.register_tool(WriteTool())
registry.register_tool(RunCommandTool())
registry.register_tool(CheckCommandStatusTool())
registry.register_tool(StopCommandTool())
registry.register_tool(GetDiagnosticsTool())
registry.register_tool(TodoWriteTool())
registry.register_tool(OpenPreviewTool())
registry.register_tool(AskUserQuestionTool())