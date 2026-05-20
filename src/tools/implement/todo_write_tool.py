"""
TodoWrite工具实现
"""
import json
from typing import Dict, Any, List
from .base_tool import BaseTool


class TodoWriteTool(BaseTool):
    """
    待办事项管理工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T16"
        self.name = "TodoWrite"
        self.category = "Task"
        self.load_description()
        self.todo_items: List[Dict[str, Any]] = []
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建或更新待办事项
        
        Args:
            params: 工具参数，包含 merge, todos 字段
            
        Returns:
            操作结果
        """
        merge = params.get("merge", False)
        todos_str = params.get("todos", "")
        
        if not todos_str:
            return {"error": "待办事项数据不能为空"}
        
        try:
            todos = json.loads(todos_str)
            
            if not isinstance(todos, list):
                return {"error": "待办事项必须是数组格式"}
            
            if merge:
                # 合并现有待办事项
                existing_ids = {item["id"] for item in self.todo_items}
                for todo in todos:
                    if todo["id"] in existing_ids:
                        # 更新现有项
                        index = next(i for i, item in enumerate(self.todo_items) if item["id"] == todo["id"])
                        self.todo_items[index] = todo
                    else:
                        # 添加新项
                        self.todo_items.append(todo)
            else:
                # 替换所有待办事项
                self.todo_items = todos
            
            return {
                "success": True,
                "todos": self.todo_items,
                "count": len(self.todo_items),
                "message": "待办事项已更新"
            }
        except json.JSONDecodeError:
            return {"error": "待办事项JSON格式无效"}
        except Exception as e:
            return {"error": str(e)}
