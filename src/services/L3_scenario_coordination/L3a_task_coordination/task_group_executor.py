from typing import List, Dict, Any, Optional
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
    
    def execute(self, task: Task, intent_result: IntentAnalysisResult, 
                messages: Optional[List[Dict[str, Any]]] = None) -> Task:
        """
        执行任务组，支持messages数组累积
        
        Args:
            task: 父任务
            intent_result: 意图分析结果
            messages: 当前上下文messages数组
        """
        # 初始化messages数组
        if messages is None:
            messages = []
        
        group_info = intent_result.task_group_info
        
        task_group = TaskGroup(
            task_group_id=f"group_{task.task_id}",
            parent_task_id=task.task_id,
            subtasks=[],
            execution_mode=group_info.execution_mode.value
        )
        
        # 执行子任务，传递messages数组
        task_group.subtasks = self._execute_subtasks(task_group, group_info.execution_mode, messages)
        
        aggregated_result = self._aggregate_results(task_group.subtasks)
        
        task.output_data = {
            "result": aggregated_result,
            "subtask_count": len(task_group.subtasks),
            "execution_mode": group_info.execution_mode.value,
            "messages_count": len(messages)
        }
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        
        return task
    
    def _execute_subtasks(self, task_group: TaskGroup, execution_mode, 
                          messages: List[Dict[str, Any]]) -> List[Task]:
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
            
            # 执行子任务，传递messages数组
            completed_subtask = self._get_task_executor().execute(subtask, messages)
            completed_subtasks.append(completed_subtask)
            
            # 更新messages数组（子任务可能会添加工具结果等）
            if completed_subtask.output_data and completed_subtask.output_data.get('messages'):
                messages.extend(completed_subtask.output_data['messages'])
        
        return completed_subtasks
    
    def _aggregate_results(self, subtasks: List[Task]) -> str:
        results = []
        for subtask in subtasks:
            result = subtask.output_data.get("result", "未完成")
            results.append(f"- {subtask.input_data.get('description', '')}: {result}")
        return "\n".join(results)
