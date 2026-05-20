"""
L2a Project and Configuration Management - Config Validation Service

配置验证服务：负责验证配置ID的有效性
"""

from typing import List

from .workspace_config_service import WorkspaceConfigService
from .model_config_service import ModelConfigService


class ConfigValidationService:
    def __init__(self, workspace_service: WorkspaceConfigService = None,
                 model_service: ModelConfigService = None):
        self.workspace_service = workspace_service or WorkspaceConfigService()
        self.model_service = model_service or ModelConfigService()

    def validate_configs(self, workspace_id: str, model_config_id: str,
                        tool_config_ids: List[str] = None) -> bool:
        workspace = self.workspace_service.get_workspace_config(workspace_id)
        if not workspace:
            return False

        model = self.model_service.get_model_config(model_config_id)
        if not model:
            return False

        return True
