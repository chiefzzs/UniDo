"""
Glob工具实现
"""
import glob
from typing import Dict, Any
from .base_tool import BaseTool


class GlobTool(BaseTool):
    """
    快速文件模式匹配工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T03"
        self.name = "Glob"
        self.category = "File"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文件模式匹配
        
        Args:
            params: 工具参数，包含 pattern 和 path 字段
            
        Returns:
            匹配的文件列表
        """
        pattern = params.get("pattern", "")
        path = params.get("path", "")
        
        if not pattern:
            return {"error": "模式不能为空"}
        
        # 构建完整的搜索路径
        if path:
            search_pattern = f"{path}/{pattern}"
        else:
            search_pattern = pattern
        
        try:
            matches = glob.glob(search_pattern, recursive=True)
            matches.sort()
            
            return {
                "pattern": pattern,
                "path": path,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"error": str(e)}
