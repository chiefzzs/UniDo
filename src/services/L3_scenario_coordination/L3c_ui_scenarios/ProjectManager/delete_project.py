from typing import Dict, Any
from services.L2_domain.L2a_project_config.project_service import ProjectService

class DeleteProject:
    def __init__(self):
        self.project_service = ProjectService()
    
    def execute(self, project_id: str) -> Dict[str, Any]:
        success = self.project_service.delete_project(project_id)
        return {"success": success, "project_id": project_id}
