"""
Skill工具实现
"""
from typing import Dict, Any
from .base_tool import BaseTool


class SkillTool(BaseTool):
    """
    在主对话中执行技能
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T01"
        self.name = "Skill"
        self.category = "System"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行技能
        
        Args:
            params: 工具参数，包含 name 字段
            
        Returns:
            执行结果
        """
        skill_name = params.get("name", "")
        
        if not skill_name:
            return {"error": "技能名称不能为空"}
        
        return {
            "skill_name": skill_name,
            "message": f"技能 '{skill_name}' 已触发",
            "status": "executing"
        }
