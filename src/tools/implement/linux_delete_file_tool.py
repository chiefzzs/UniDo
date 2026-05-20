"""
Linux平台DeleteFile工具实现
"""
import os
from typing import Dict, Any, List
from .base_tool import BaseTool


class LinuxDeleteFileTool(BaseTool):
    """
    Linux平台删除文件工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T09"
        self.name = "DeleteFile"
        self.category = "File"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        删除文件 - Linux版本
        
        Args:
            params: 工具参数，包含 file_paths 字段
            
        Returns:
            删除结果
        """
        file_paths: List[str] = params.get("file_paths", [])
        
        if not file_paths:
            return {"error": "文件路径列表不能为空"}
        
        success_count = 0
        failed_count = 0
        results = []
        
        for file_path in file_paths:
            try:
                # 规范化路径分隔符
                normalized_path = file_path.replace('\\', '/')
                
                if os.path.exists(normalized_path):
                    if os.path.isdir(normalized_path):
                        import shutil
                        shutil.rmtree(normalized_path)
                    else:
                        os.remove(normalized_path)
                    
                    results.append({
                        "file_path": file_path,
                        "success": True,
                        "message": "删除成功"
                    })
                    success_count += 1
                else:
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "message": "文件不存在"
                    })
                    failed_count += 1
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "message": str(e)
                })
                failed_count += 1
        
        return {
            "results": results,
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(file_paths)
        }


class MacOsDeleteFileTool(LinuxDeleteFileTool):
    """
    macOS平台删除文件工具
    继承自Linux实现
    """
    pass
