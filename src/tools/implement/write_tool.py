"""
Write工具实现
"""
import os
from typing import Dict, Any
from .base_tool import BaseTool


class WriteTool(BaseTool):
    """
    写入文件工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T11"
        self.name = "Write"
        self.category = "File"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        写入文件
        
        Args:
            params: 工具参数，包含 file_path, content 字段
            
        Returns:
            写入结果
        """
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        
        # 实时打印 content 内容到控制台
        print(f"\n{'='*80}")
        print(f"[WriteTool] 正在写入文件: {file_path}")
        print(f"[WriteTool] 内容长度: {len(content)} 字符")
        print(f"[WriteTool] 内容:\n{content}")
        print(f"{'='*80}\n")
        
        if not file_path:
            return {"error": "文件路径不能为空"}
        
        try:
            # 确保父目录存在
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "file_path": file_path,
                "content_length": len(content),
                "message": "写入成功"
            }
        except Exception as e:
            return {"error": str(e)}
