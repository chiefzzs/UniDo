from typing import Dict, Any, List, Optional
from services.L2_domain.L2a_project_config.workspace_config_service import WorkspaceConfigService

class WorkspaceConfig:
    def __init__(self):
        self.workspace_config_service = WorkspaceConfigService()
    
    def create(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        workspace = self.workspace_config_service.create_workspace_config(
            name=config_data.get("name"),
            root_path=config_data.get("root_path", "/workspace/default"),
            type=config_data.get("type", "local"),
            encoding=config_data.get("encoding", "utf-8"),
            excluded_patterns=config_data.get("excluded_patterns", [])
        )
        return workspace.to_dict()
    
    def get(self, config_id: str) -> Optional[Dict[str, Any]]:
        workspace = self.workspace_config_service.get_workspace_config(config_id)
        return workspace.to_dict() if workspace else None
    
    def update(self, config_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        workspace = self.workspace_config_service.update_workspace_config(
            config_id=config_id,
            **update_data
        )
        return workspace.to_dict() if workspace else None
    
    def list(self) -> List[Dict[str, Any]]:
        from services.L2_domain.L2a_project_config.models import WorkspaceConfig as WorkspaceConfigModel
        all_configs = self.workspace_config_service.persistence.list('workspace_configs')
        return [WorkspaceConfigModel.from_dict(c).to_dict() for c in all_configs]
    
    def delete(self, config_id: str) -> Dict[str, bool]:
        all_configs = self.workspace_config_service.persistence.list('workspace_configs')
        new_configs = [c for c in all_configs if c.get('config_id') != config_id]
        if len(new_configs) != len(all_configs):
            self.workspace_config_service.persistence._write_all('workspace_configs', new_configs)
            return {"success": True}
        return {"success": False}
