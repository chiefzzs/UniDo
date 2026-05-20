from typing import List
from datetime import datetime
from ..schemas import Task, TaskStatus, TaskGroup
from .intent_service import IntentAnalysisResult

class TaskGroupExecutor:
    def __init__(self):
        self.task_executor = None
    
    def _get_task_executor(self):
        if self.task_executor is None:
            from .task_execution_service import TaskExecutionService
            self.task_executor = TaskExecutionService()
        return self.task_executor
    
    def execute(self, task: Task, intent_result: IntentAnalysisResult) -> Task:
        group_info = intent_result.task_group_info
        
        task_group = TaskGroup(
            task_group_id=f"group_{task.task_id}",
            parent_task_id=task.task_id,
            subtasks=[],
            execution_mode=group_info.execution_mode.value
        )
        
        task_group.subtasks = self._execute_subtasks(task_group, group_info.execution_mode)
        
        aggregated_result = self._aggregate_results(task_group.subtasks)
        
        task.output_data = {
            "result": aggregated_result,
            "subtask_count": len(task_group.subtasks),
            "execution_mode": group_info.execution_mode.value
        }
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        return task
    
    def _execute_subtasks(self, task_group: TaskGroup, execution_mode) -> List[Task]:
        completed_subtasks = []
        
        subtask_definitions = [
            {"description": "分析任务", "task_type": "analysis"},
            {"description": "执行操作", "task_type": "execution"},
            {"description": "汇总结果", "task_type": "summary"}
        ]
        
        for i, subtask_def in enumerate(subtask_definitions):
            subtask = Task(
                task_id=f"{task_group.task_group_id}_sub{i+1}",
                parent_task_id=task_group.parent_task_id,
                input_data={"description": subtask_def["description"]},
                created_at=datetime.now()
            )
            
            completed_subtask = self._get_task_executor().execute(subtask)
            completed_subtasks.append(completed_subtask)
        
        return completed_subtasks
    
    def _aggregate_results(self, subtasks: List[Task]) -> str:
        results = []
        for subtask in subtasks:
            result = subtask.output_data.get("result", "未完成")
            results.append(f"- {subtask.input_data.get('description', '')}: {result}")
        return "\n".join(results)
