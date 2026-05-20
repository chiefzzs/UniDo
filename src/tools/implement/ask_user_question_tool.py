"""
AskUserQuestion工具实现
"""
import json
from typing import Dict, Any, List
from .base_tool import BaseTool


class AskUserQuestionTool(BaseTool):
    """
    询问用户问题工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T18"
        self.name = "AskUserQuestion"
        self.category = "UI"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        询问用户问题
        
        Args:
            params: 工具参数，包含 questions, title 字段
            
        Returns:
            问题提交结果
        """
        questions_str = params.get("questions", "")
        title = params.get("title", "")
        
        if not questions_str:
            return {"error": "问题数据不能为空"}
        
        try:
            questions = json.loads(questions_str)
            
            if not isinstance(questions, list):
                return {"error": "问题必须是数组格式"}
            
            # 验证问题格式
            for q in questions:
                if "id" not in q or "question" not in q or "options" not in q:
                    return {"error": "每个问题必须包含 id, question 和 options 字段"}
            
            return {
                "success": True,
                "title": title,
                "questions": questions,
                "count": len(questions),
                "message": "问题已提交等待用户回答"
            }
        except json.JSONDecodeError:
            return {"error": "问题JSON格式无效"}
        except Exception as e:
            return {"error": str(e)}
