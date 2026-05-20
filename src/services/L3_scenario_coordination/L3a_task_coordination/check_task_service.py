from datetime import datetime
from ..schemas import Task, TaskStatus

class CheckTaskService:
    def __init__(self):
        self.max_checks = 3
        self.check_count = 0
    
    def execute(self, task: Task) -> Task:
        self.check_count += 1
        
        if self.check_count >= self.max_checks:
            task.status = TaskStatus.COMPLETED
            task.output_data = {
                "result": "检查任务已完成（达到最大检查次数）",
                "check_count": self.check_count
            }
            return task
        
        tool_result = self._get_last_tool_result(task)
        result = self._analyze_tool_result(tool_result)
        
        task.status = TaskStatus.COMPLETED
        task.output_data = {
            "result": result,
            "check_count": self.check_count,
            "tool_result": tool_result
        }
        return task
    
    def _get_last_tool_result(self, task: Task) -> dict:
        if task.execution_history:
            for step in reversed(task.execution_history):
                if step.get("step") == "tool_execution":
                    return step
        return {}
    
    def _analyze_tool_result(self, tool_result: dict) -> str:
        if not tool_result:
            return "未找到工具执行结果"
        
        status = tool_result.get("status", "")
        if status == "success":
            return "工具执行成功"
        elif status == "failed":
            return "工具执行失败"
        else:
            return "工具执行状态未知"
