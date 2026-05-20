"""
WebFetch工具实现
"""
from typing import Dict, Any
import requests
from .base_tool import BaseTool


class WebFetchTool(BaseTool):
    """
    获取网页内容工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T08"
        self.name = "WebFetch"
        self.category = "Internet"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取网页内容
        
        Args:
            params: 工具参数，包含 url 字段
            
        Returns:
            网页内容
        """
        url = params.get("url", "")
        
        if not url:
            return {"error": "URL不能为空"}
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 简单的HTML转Markdown
            content = response.text
            
            # 限制内容长度
            max_length = 5000
            if len(content) > max_length:
                content = content[:max_length] + "\n\n... (内容已截断)"
            
            return {
                "url": url,
                "status_code": response.status_code,
                "content": content,
                "content_length": len(content)
            }
        except Exception as e:
            return {"error": str(e)}
