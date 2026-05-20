"""
Read工具实现
"""
import os
from typing import Dict, Any
from .base_tool import BaseTool


class ReadTool(BaseTool):
    """
    读取文件内容
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T06"
        self.name = "Read"
        self.category = "File"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            params: 工具参数，包含 file_path, offset, limit 字段
            
        Returns:
            文件内容
        """
        file_path = params.get("file_path", "")
        offset = params.get("offset", 1)
        limit = params.get("limit", 200)
        
        if not file_path:
            return {"error": "文件路径不能为空"}
        
        if limit < 1 or limit > 1000:
            return {"error": "读取行数必须在1-1000之间"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # 处理偏移量
            start_line = max(1, offset)
            end_line = min(start_line + limit - 1, total_lines)
            
            # 提取指定范围的行
            content = ''.join(lines[start_line - 1:end_line])
            
            return {
                "file_path": file_path,
                "total_lines": total_lines,
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "line_count": end_line - start_line + 1
            }
        except Exception as e:
            return {"error": str(e)}
