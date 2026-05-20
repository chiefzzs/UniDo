"""
OpenPreview工具实现
"""
from typing import Dict, Any
from .base_tool import BaseTool


class OpenPreviewTool(BaseTool):
    """
    打开预览工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T17"
        self.name = "OpenPreview"
        self.category = "UI"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        打开预览
        
        Args:
            params: 工具参数，包含 url 字段
            
        Returns:
            操作结果
        """
        url = params.get("url", "")
        
        if not url:
            return {"error": "URL不能为空"}
        
        # 验证URL格式
        if not (url.startswith("http://") or url.startswith("https://")):
            return {"error": "URL必须是有效的HTTP/HTTPS地址"}
        
        return {
            "success": True,
            "url": url,
            "message": f"预览已打开: {url}"
        }
