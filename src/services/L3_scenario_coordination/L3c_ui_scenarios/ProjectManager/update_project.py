from typing import Dict, Any
from services.L2_domain.L2a_project_config.project_service import ProjectService

class UpdateProject:
    def __init__(self):
        self.project_service = ProjectService()
    
    def execute(self, project_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        # 移除可能存在的 project_id，避免重复传入
        update_data = {k: v for k, v in update_data.items() if k != 'project_id'}
        project = self.project_service.update_project(
            project_id=project_id,
            **update_data
        )
        return project.to_dict() if project else {}
