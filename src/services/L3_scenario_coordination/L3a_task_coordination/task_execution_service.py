from typing import List, Dict, Any, Optional
from ..schemas import Task, TaskStatus
from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service


class TaskExecutionService:
    def __init__(self):
        self.persistence = get_persistence_service()
    
    def execute(self, task: Task, messages: Optional[List[Dict[str, Any]]] = None) -> Task:
        """
        执行任务，支持messages数组累积
        
        Args:
            task: 任务对象
            messages: 当前上下文messages数组（可选）
            
        Returns:
            执行完成的任务
        """
        # 初始化messages数组
        if messages is None:
            messages = []
        
        # 保存任务到持久化存储
        task_data = {
            "task_id": task.task_id,
            "parent_task_id": task.parent_task_id,
            "status": task.status.value,
            "input_data": task.input_data,
            "output_data": {}
        }
        self.persistence.save("tasks", task_data)
        
        # 执行任务逻辑
        task_type = task.input_data.get("task_type", "direct")
        
        if task_type == "analysis":
            result = self._execute_analysis(task, messages)
        elif task_type == "execution":
            result = self._execute_operation(task, messages)
        elif task_type == "summary":
            result = self._execute_summary(task, messages)
        else:
            result = "任务执行完成"
        
        task.status = TaskStatus.COMPLETED
        task.output_data = {
            "result": result,
            "input": task.input_data,
            "messages_count": len(messages)
        }
        
        # 更新任务持久化记录
        task_data["status"] = task.status.value
        task_data["output_data"] = task.output_data
        self.persistence.save("tasks", task_data)
        
        return task
    
    def _execute_analysis(self, task: Task, messages: List[Dict[str, Any]]) -> str:
        """执行分析任务"""
        description = task.input_data.get("description", "")
        return f"分析完成: {description}"
    
    def _execute_operation(self, task: Task, messages: List[Dict[str, Any]]) -> str:
        """执行操作任务"""
        description = task.input_data.get("description", "")
        return f"操作执行完成: {description}"
    
    def _execute_summary(self, task: Task, messages: List[Dict[str, Any]]) -> str:
        """执行汇总任务"""
        description = task.input_data.get("description", "")
        return f"汇总完成: {description}"
