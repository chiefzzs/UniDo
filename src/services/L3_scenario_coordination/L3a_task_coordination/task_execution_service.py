from ..schemas import Task, TaskStatus
from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service


class TaskExecutionService:
    def __init__(self):
        self.persistence = get_persistence_service()
    
    def execute(self, task: Task) -> Task:
        # 保存任务到持久化存储
        task_data = {
            "task_id": task.task_id,
            "parent_task_id": task.parent_task_id,
            "status": task.status.value,
            "input_data": task.input_data,
            "output_data": {}
        }
        self.persistence.save("tasks", task_data)
        
        task.status = TaskStatus.COMPLETED
        task.output_data = {
            "result": "任务执行完成",
            "input": task.input_data
        }
        
        # 更新任务持久化记录
        task_data["status"] = task.status.value
        task_data["output_data"] = task.output_data
        self.persistence.save("tasks", task_data)
        
        return task
