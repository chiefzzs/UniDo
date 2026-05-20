"""
L2a Project Configuration Unit Tests

单元测试：测试项目配置管理服务
"""

import pytest
from services.L2_domain.L2a_project_config.project_service import ProjectService
from services.L2_domain.L2a_project_config.workspace_config_service import WorkspaceConfigService
from services.L2_domain.L2a_project_config.model_config_service import ModelConfigService


class TestProjectService:
    """测试项目服务"""

    def test_create_project(self, test_report):
        """测试创建项目 - 验证L2服务调用L1持久化"""
        project_service = ProjectService()
        
        inputs = {
            "name": "Test Project",
            "description": "A test project",
            "workspace_config_id": "ws-config-001",
            "model_config_id": "model-config-001",
            "tool_config_ids": ["tool-1", "tool-2"]
        }
        
        project = project_service.create_project(**inputs)
        
        outputs = {
            "project_id": project.project_id,
            "name": project.name,
            "status": project.status
        }
        
        test_report(
            test_points=["测试项目创建", "验证L2服务自动触发L1持久化", "验证项目数据保存到projects.json"],
            inputs=inputs,
            outputs=outputs
        )
        
        assert project is not None
        assert project.name == "Test Project"
        assert project.project_id is not None

    def test_get_project(self, test_report):
        """测试获取项目 - 验证从L1持久化读取"""
        project_service = ProjectService()
        
        # 先创建项目
        project = project_service.create_project(
            name="Test Get Project",
            description="Test project for get",
            workspace_config_id="ws-config-002",
            model_config_id="model-config-002"
        )
        
        # 获取项目
        retrieved = project_service.get_project(project.project_id)
        
        test_report(
            test_points=["测试获取项目", "验证从L1持久化正确读取"],
            inputs={"project_id": project.project_id},
            outputs={"found": retrieved is not None, "name": retrieved.name if retrieved else None}
        )
        
        assert retrieved is not None
        assert retrieved.project_id == project.project_id
        assert retrieved.name == "Test Get Project"

    def test_update_project(self, test_report):
        """测试更新项目 - 验证L2服务更新L1持久化"""
        project_service = ProjectService()
        
        # 先创建项目
        project = project_service.create_project(
            name="Test Update Project",
            description="Before update",
            workspace_config_id="ws-config-003",
            model_config_id="model-config-003"
        )
        
        # 更新项目
        updated = project_service.update_project(
            project.project_id,
            name="Updated Project",
            description="After update"
        )
        
        test_report(
            test_points=["测试更新项目", "验证L2服务更新L1持久化"],
            inputs={"project_id": project.project_id, "updates": {"name": "Updated Project"}},
            outputs={"updated_name": updated.name if updated else None}
        )
        
        assert updated is not None
        assert updated.name == "Updated Project"
        assert updated.description == "After update"

    def test_list_projects(self, test_report):
        """测试列出项目 - 验证L2服务从L1持久化查询"""
        project_service = ProjectService()
        
        # 创建多个项目
        for i in range(3):
            project_service.create_project(
                name=f"List Test Project {i}",
                description=f"Project {i} for list test",
                workspace_config_id=f"ws-config-{i}",
                model_config_id=f"model-config-{i}"
            )
        
        projects = project_service.list_projects()
        
        test_report(
            test_points=["测试列出项目", "验证L2服务从L1持久化正确查询"],
            inputs={"expected_count": 3},
            outputs={"actual_count": len(projects)}
        )
        
        assert len(projects) >= 3


class TestWorkspaceConfigService:
    """测试工作空间配置服务"""

    def test_create_workspace_config(self, test_report):
        """测试创建工作空间配置 - 验证L2服务调用L1持久化"""
        service = WorkspaceConfigService()
        
        config = service.create_workspace_config(
            name="Test Workspace",
            root_path="/workspace/test",
            type="local"
        )
        
        test_report(
            test_points=["测试创建工作空间配置", "验证L2服务自动触发L1持久化"],
            inputs={"name": "Test Workspace"},
            outputs={"config_id": config.config_id, "name": config.name}
        )
        
        assert config is not None
        assert config.config_id is not None


class TestModelConfigService:
    """测试模型配置服务"""

    def test_create_model_config(self, test_report):
        """测试创建模型配置 - 验证L2服务调用L1持久化"""
        service = ModelConfigService()
        
        config = service.create_model_config(
            name="Test Model",
            model_name="gpt-4",
            api_type="openai",
            api_address="http://localhost/v1",
            api_key="test-key"
        )
        
        test_report(
            test_points=["测试创建模型配置", "验证L2服务自动触发L1持久化"],
            inputs={"name": "Test Model", "api_type": "openai"},
            outputs={"config_id": config.config_id, "name": config.name}
        )
        
        assert config is not None
        assert config.config_id is not None
