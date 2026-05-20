"""
SearchReplace工具实现
"""
import os
from typing import Dict, Any
from .base_tool import BaseTool


class SearchReplaceTool(BaseTool):
    """
    搜索替换工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T10"
        self.name = "SearchReplace"
        self.category = "File"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行搜索替换
        
        Args:
            params: 工具参数，包含 file_path, old_str, new_str 字段
            
        Returns:
            替换结果
        """
        file_path = params.get("file_path", "")
        old_str = params.get("old_str", "")
        new_str = params.get("new_str", "")
        
        if not file_path:
            return {"error": "文件路径不能为空"}
        
        if old_str == "":
            return {"error": "搜索内容不能为空"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_str not in content:
                return {
                    "success": False,
                    "error": "未找到匹配的内容"
                }
            
            # 替换第一个匹配
            new_content = content.replace(old_str, new_str, 1)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "file_path": file_path,
                "replaced_count": 1,
                "message": "替换成功"
            }
        except Exception as e:
            return {"error": str(e)}
