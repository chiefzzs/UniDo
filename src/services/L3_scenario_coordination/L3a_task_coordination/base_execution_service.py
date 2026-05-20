from typing import Any
from datetime import datetime
from ..schemas import Task, TaskStatus
from .intent_service import IntentService, ExecutionPath

class BaseExecutionService:
    def __init__(self):
        self.intent_service = IntentService()
        self.tool_task_executor = None
        self.task_group_executor = None
    
    def _get_tool_task_executor(self):
        if self.tool_task_executor is None:
            from .tool_task_executor import ToolTaskExecutor
            self.tool_task_executor = ToolTaskExecutor()
        return self.tool_task_executor
    
    def _get_task_group_executor(self):
        if self.task_group_executor is None:
            from .task_group_executor import TaskGroupExecutor
            self.task_group_executor = TaskGroupExecutor()
        return self.task_group_executor
    
    def execute_task(self, task: Task) -> Task:
        task.status = TaskStatus.ANALYZING
        task.updated_at = datetime.now()
        
        intent_result = self.intent_service.analyze_intent(task.input_data)
        
        if intent_result.execution_path == ExecutionPath.DIRECT_COMPLETION:
            return self.execute_direct_completion(task, intent_result)
        elif intent_result.execution_path == ExecutionPath.SINGLE_TOOL:
            return self._get_tool_task_executor().execute(task, intent_result)
        elif intent_result.execution_path == ExecutionPath.TASK_GROUP:
            return self._get_task_group_executor().execute(task, intent_result)
        
        return task
    
    def execute_direct_completion(self, task: Task, intent_result: Any) -> Task:
        task.status = TaskStatus.COMPLETED
        task.output_data = {
            "result": "任务已直接完成",
            "reasoning": intent_result.reasoning
        }
        task.completed_at = datetime.now()
        return task
