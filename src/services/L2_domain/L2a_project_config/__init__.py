"""
L2a Project and Configuration Management Service

L2a 项目与配置管理服务负责管理项目及其相关配置数据。
包括 Project、WorkspaceConfig、ModelConfig 的 CRUD 操作。

职责：
- Project管理：项目的创建、查询、更新、删除、归档
- WorkspaceConfig管理：工作区配置的创建、查询、更新、删除
- ModelConfig管理：模型配置的创建、查询、更新、删除
- 配置验证：验证配置ID的有效性

依赖 L1 层：
- L1b 持久化服务：用于存储和读取配置数据
- L1d 事件系统：发布配置变更事件
"""

from .models import Project, WorkspaceConfig, ModelConfig
from .project_service import ProjectService
from .workspace_config_service import WorkspaceConfigService
from .model_config_service import ModelConfigService
from .config_validation_service import ConfigValidationService


def get_project_service() -> ProjectService:
    return ProjectService()


def get_workspace_config_service() -> WorkspaceConfigService:
    return WorkspaceConfigService()


def get_model_config_service() -> ModelConfigService:
    return ModelConfigService()


def get_config_validation_service() -> ConfigValidationService:
    return ConfigValidationService()


__all__ = [
    'Project', 'WorkspaceConfig', 'ModelConfig',
    'ProjectService', 'WorkspaceConfigService', 'ModelConfigService',
    'ConfigValidationService',
    'get_project_service', 'get_workspace_config_service', 
    'get_model_config_service', 'get_config_validation_service'
]
