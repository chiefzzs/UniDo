"""
GetDiagnostics工具实现
"""
from typing import Dict, Any
from .base_tool import BaseTool


class GetDiagnosticsTool(BaseTool):
    """
    获取诊断信息工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T15"
        self.name = "GetDiagnostics"
        self.category = "System"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取诊断信息
        
        Args:
            params: 工具参数，包含 path 字段
            
        Returns:
            诊断信息
        """
        path = params.get("path", "")
        
        # 模拟诊断结果
        diagnostics = [
            {
                "file": "/path/to/main.py",
                "line": 15,
                "column": 10,
                "severity": "error",
                "message": "未定义的变量 'undefined_var'"
            },
            {
                "file": "/path/to/utils.py",
                "line": 28,
                "column": 5,
                "severity": "warning",
                "message": "未使用的导入 'os'"
            },
            {
                "file": "/path/to/config.py",
                "line": 8,
                "column": 1,
                "severity": "hint",
                "message": "可以简化的条件表达式"
            }
        ]
        
        # 如果指定了路径，过滤结果
        if path:
            diagnostics = [d for d in diagnostics if d["file"] == path]
        
        return {
            "path": path,
            "diagnostics": diagnostics,
            "total": len(diagnostics),
            "errors": sum(1 for d in diagnostics if d["severity"] == "error"),
            "warnings": sum(1 for d in diagnostics if d["severity"] == "warning"),
            "hints": sum(1 for d in diagnostics if d["severity"] == "hint")
        }
