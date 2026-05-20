"""
Linux平台LS工具实现
使用os.listdir进行目录列表
"""
import os
from typing import Dict, Any, List
from .base_tool import BaseTool


class LinuxLsTool(BaseTool):
    """
    Linux平台列出目录内容
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T04"
        self.name = "LS"
        self.category = "File"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        列出目录内容 - Linux版本
        
        Args:
            params: 工具参数，包含 path 和 ignore 字段
            
        Returns:
            目录内容列表
        """
        path = params.get("path", "")
        ignore: List[str] = params.get("ignore", [])
        
        if not path:
            return {"error": "路径不能为空"}
        
        try:
            entries = os.listdir(path)
            filtered_entries = []
            
            for entry in entries:
                # 检查是否需要忽略
                should_ignore = False
                for pattern in ignore:
                    if pattern in entry:
                        should_ignore = True
                        break
                
                if should_ignore:
                    continue
                
                entry_path = os.path.join(path, entry)
                is_dir = os.path.isdir(entry_path)
                size = os.path.getsize(entry_path) if not is_dir else 0
                
                filtered_entries.append({
                    "name": entry,
                    "type": "directory" if is_dir else "file",
                    "size": size,
                    "path": entry_path
                })
            
            # 按名称排序，目录优先
            filtered_entries.sort(key=lambda x: (x["type"] != "directory", x["name"]))
            
            return {
                "path": path,
                "entries": filtered_entries,
                "total": len(filtered_entries),
                "directories": sum(1 for e in filtered_entries if e["type"] == "directory"),
                "files": sum(1 for e in filtered_entries if e["type"] == "file")
            }
        except Exception as e:
            return {"error": str(e)}


class MacOsLsTool(LinuxLsTool):
    """
    macOS平台列出目录内容
    继承自Linux实现，macOS与Linux使用相同的POSIX接口
    """
    pass
