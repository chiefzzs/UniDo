from typing import Dict, Any
from services.L2_domain.L2a_project_config.project_service import ProjectService

class CreateProject:
    def __init__(self):
        self.project_service = ProjectService()
    
    def execute(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        project = self.project_service.create_project(
            name=project_data.get("name"),
            description=project_data.get("description", ""),
            workspace_config_id=project_data.get("workspace_config_id", ""),
            model_config_id=project_data.get("model_config_id", "")
        )
        return project.to_dict()
