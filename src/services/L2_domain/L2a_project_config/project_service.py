"""
L2a Project and Configuration Management - Project Service

项目管理服务：负责项目的创建、查询、更新、删除、归档
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes

from .models import Project


class ProjectService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()

    def _generate_id(self) -> str:
        return f"proj-{uuid.uuid4().hex[:12]}"

    def _update_timestamp(self, entity: Dict) -> Dict:
        entity['updated_at'] = datetime.now().isoformat()
        return entity

    def create_project(self, name: str, description: str, workspace_config_id: str,
                      model_config_id: str, tool_config_ids: List[str] = None) -> Project:
        project = Project(
            project_id=self._generate_id(),
            name=name,
            description=description,
            workspace_config_id=workspace_config_id,
            model_config_id=model_config_id,
            tool_config_ids=tool_config_ids or []
        )
        self.persistence.save('projects', project.to_dict())

        if self.event_bus:
            self.event_bus.publish(Event(
                event_type=EventTypes.PROJECT_CREATED,
                payload={'project_id': project.project_id, 'name': project.name}
            ))

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        all_projects = self.persistence.list('projects')
        for p in all_projects:
            if p.get('project_id') == project_id:
                return Project.from_dict(p)
        return None

    def update_project(self, project_id: str, **kwargs) -> Optional[Project]:
        all_projects = self.persistence.list('projects')
        for i, p in enumerate(all_projects):
            if p.get('project_id') == project_id:
                p.update(kwargs)
                p['updated_at'] = datetime.now().isoformat()
                all_projects[i] = p
                self.persistence.save('projects', p)

                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type=EventTypes.PROJECT_UPDATED,
                        payload={'project_id': project_id}
                    ))

                return Project.from_dict(p)
        return None

    def delete_project(self, project_id: str) -> bool:
        all_projects = self.persistence.list('projects')
        new_projects = [p for p in all_projects if p.get('project_id') != project_id]
        if len(new_projects) == len(all_projects):
            return False

        for p in all_projects:
            if p.get('project_id') == project_id:
                self.persistence._write_all('projects', new_projects)

                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type=EventTypes.PROJECT_DELETED,
                        payload={'project_id': project_id}
                    ))
                return True
        return False

    def archive_project(self, project_id: str) -> bool:
        return self.update_project(project_id, status='archived') is not None

    def list_projects(self, status: str = None) -> List[Project]:
        all_projects = self.persistence.list('projects')
        if status:
            return [Project.from_dict(p) for p in all_projects if p.get('status') == status]
        return [Project.from_dict(p) for p in all_projects]

    def validate_project_config(self, project_id: str) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False

        if not project.workspace_config_id:
            return False
        if not project.model_config_id:
            return False

        return True
