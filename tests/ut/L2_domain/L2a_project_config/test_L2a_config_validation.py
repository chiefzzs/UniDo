"""
L2a Config Validation Unit Tests

单元测试：测试配置验证服务
"""

import pytest
from services.L2_domain.L2a_project_config.config_validation_service import ConfigValidationService
from services.L2_domain.L2a_project_config.workspace_config_service import WorkspaceConfigService
from services.L2_domain.L2a_project_config.model_config_service import ModelConfigService


class TestConfigValidationService:
    """测试配置验证服务"""

    def test_validate_configs_with_valid_configs(self, test_report):
        """测试验证有效配置"""
        # 先创建一些配置
        workspace_service = WorkspaceConfigService()
        model_service = ModelConfigService()
        
        workspace = workspace_service.create_workspace_config(
            name="Test Workspace",
            root_path="/workspace/test",
            type="local"
        )
        
        model = model_service.create_model_config(
            name="Test Model",
            model_name="gpt-4",
            api_type="openai",
            api_address="http://localhost/v1",
            api_key="test-key"
        )
        
        # 验证配置
        service = ConfigValidationService(workspace_service, model_service)
        result = service.validate_configs(workspace.config_id, model.config_id)
        
        test_report(
            test_points=["测试验证有效配置", "验证存在的配置ID通过验证"],
            inputs={"workspace_id": workspace.config_id, "model_config_id": model.config_id},
            outputs={"valid": result}
        )
        
        assert result is True

    def test_validate_configs_with_invalid_workspace(self, test_report):
        """测试验证无效工作空间配置"""
        model_service = ModelConfigService()
        model = model_service.create_model_config(
            name="Test Model",
            model_name="gpt-4",
            api_type="openai",
            api_address="http://localhost/v1",
            api_key="test-key"
        )
        
        service = ConfigValidationService()
        result = service.validate_configs("invalid-workspace-id", model.config_id)
        
        test_report(
            test_points=["测试验证无效工作空间", "验证不存在的工作空间ID被拒绝"],
            inputs={"workspace_id": "invalid-workspace-id", "model_config_id": model.config_id},
            outputs={"valid": result}
        )
        
        assert result is False

    def test_validate_configs_with_invalid_model(self, test_report):
        """测试验证无效模型配置"""
        workspace_service = WorkspaceConfigService()
        workspace = workspace_service.create_workspace_config(
            name="Test Workspace",
            root_path="/workspace/test",
            type="local"
        )
        
        service = ConfigValidationService(workspace_service)
        result = service.validate_configs(workspace.config_id, "invalid-model-id")
        
        test_report(
            test_points=["测试验证无效模型配置", "验证不存在的模型ID被拒绝"],
            inputs={"workspace_id": workspace.config_id, "model_config_id": "invalid-model-id"},
            outputs={"valid": result}
        )
        
        assert result is False

    def test_validate_configs_with_none_values(self, test_report):
        """测试验证None值配置"""
        service = ConfigValidationService()
        result = service.validate_configs(None, None)
        
        test_report(
            test_points=["测试验证None值配置", "验证None值被正确处理"],
            inputs={"workspace_id": None, "model_config_id": None},
            outputs={"valid": result}
        )
        
        assert result is False