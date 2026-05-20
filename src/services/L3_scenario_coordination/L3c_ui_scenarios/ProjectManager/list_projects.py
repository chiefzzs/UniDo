from typing import List, Dict, Any
from services.L2_domain.L2a_project_config.project_service import ProjectService

class ListProjects:
    def __init__(self):
        self.project_service = ProjectService()
    
    def execute(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        projects = self.project_service.list_projects(filters or {})
        return [project.to_dict() for project in projects]
