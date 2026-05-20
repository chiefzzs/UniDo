"""
StopCommand工具实现
"""
from typing import Dict, Any
from .base_tool import BaseTool


class StopCommandTool(BaseTool):
    """
    停止命令工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T14"
        self.name = "StopCommand"
        self.category = "System"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        停止命令
        
        Args:
            params: 工具参数，包含 command_id 字段
            
        Returns:
            停止结果
        """
        command_id = params.get("command_id", "")
        
        if not command_id:
            return {"error": "命令ID不能为空"}
        
        # 模拟停止命令
        return {
            "command_id": command_id,
            "status": "stopped",
            "message": "命令已停止"
        }
