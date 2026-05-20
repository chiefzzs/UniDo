"""
L2b Memory and State Management - Task Service

任务管理服务：负责任务的创建、查询、更新
"""

import uuid
from datetime import datetime
from typing import List, Optional

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes

from .models import Task


class TaskService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()

    def _generate_id(self) -> str:
        return f"task-{uuid.uuid4().hex[:12]}"

    def create_task(self, group_id: str, name: str) -> Task:
        task = Task(
            task_id=self._generate_id(),
            group_id=group_id,
            name=name
        )
        self.persistence.save('tasks', task.to_dict())
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        all_tasks = self.persistence.list('tasks')
        for t in all_tasks:
            if t.get('task_id') == task_id:
                return Task.from_dict(t)
        return None

    def update_task(self, task_id: str, **kwargs) -> Optional[Task]:
        all_tasks = self.persistence.list('tasks')
        for i, t in enumerate(all_tasks):
            if t.get('task_id') == task_id:
                t.update(kwargs)
                t['updated_at'] = datetime.now().isoformat()
                all_tasks[i] = t
                self.persistence.save('tasks', t)

                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type=EventTypes.TASK_UPDATED,
                        payload={'task_id': task_id, 'status': kwargs.get('status')}
                    ))

                return Task.from_dict(t)
        return None

    def list_tasks(self, group_id: str = None, status: str = None) -> List[Task]:
        all_tasks = self.persistence.list('tasks')
        result = [Task.from_dict(t) for t in all_tasks]

        if group_id:
            result = [t for t in result if t.group_id == group_id]
        if status:
            result = [t for t in result if t.status == status]

        return result
