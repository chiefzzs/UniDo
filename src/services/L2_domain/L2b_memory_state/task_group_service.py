"""
L2b Memory and State Management - Task Group Service

任务组管理服务：负责任务组的创建、查询、状态更新
"""

import uuid
from typing import List, Optional

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory

from .models import TaskGroup


class TaskGroupService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus

    def _generate_id(self) -> str:
        return f"group-{uuid.uuid4().hex[:12]}"

    def create_task_group(self, session_id: str, name: str) -> TaskGroup:
        group = TaskGroup(
            group_id=self._generate_id(),
            session_id=session_id,
            name=name
        )
        self.persistence.save('task_groups', group.to_dict())
        return group

    def get_task_group(self, group_id: str) -> Optional[TaskGroup]:
        all_groups = self.persistence.list('task_groups')
        for g in all_groups:
            if g.get('group_id') == group_id:
                return TaskGroup.from_dict(g)
        return None

    def update_task_group_status(self, group_id: str, status: str) -> Optional[TaskGroup]:
        all_groups = self.persistence.list('task_groups')
        for i, g in enumerate(all_groups):
            if g.get('group_id') == group_id:
                g['status'] = status
                all_groups[i] = g
                self.persistence.save('task_groups', g)
                return TaskGroup.from_dict(g)
        return None

    def list_task_groups(self, session_id: str = None) -> List[TaskGroup]:
        all_groups = self.persistence.list('task_groups')
        result = [TaskGroup.from_dict(g) for g in all_groups]

        if session_id:
            result = [g for g in result if g.session_id == session_id]

        return result
