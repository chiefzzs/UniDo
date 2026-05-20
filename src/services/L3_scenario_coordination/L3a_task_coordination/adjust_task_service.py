from datetime import datetime
from ..schemas import Task, TaskStatus

class AdjustTaskService:
    def __init__(self):
        self.max_adjustments = 3
        self.adjust_count = 0
    
    def execute(self, task: Task, check_result=None) -> Task:
        self.adjust_count += 1
        
        if self.adjust_count >= self.max_adjustments:
            task.status = TaskStatus.COMPLETED
            task.output_data = {
                "result": "调整任务已完成（达到最大调整次数）",
                "adjust_count": self.adjust_count,
                "action": "complete"
            }
            return task
        
        original_input = task.input_data.get("original_input", {})
        tool_result = task.input_data.get("tool_execution_result", {})
        
        adjustment = self._generate_adjustment(original_input, tool_result)
        
        task.status = TaskStatus.COMPLETED
        task.output_data = {
            "result": adjustment,
            "adjust_count": self.adjust_count,
            "original_input": original_input,
            "action": "complete"
        }
        return task
    
    def _generate_adjustment(self, original_input: dict, tool_result: dict) -> str:
        if not tool_result:
            return "根据原始输入进行调整"
        
        status = tool_result.get("status", "")
        if status == "failed":
            return "检测到工具执行失败，已调整参数"
        else:
            return "工具执行成功，无需调整"
