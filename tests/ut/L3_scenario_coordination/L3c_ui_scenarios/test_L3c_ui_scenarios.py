"""
L3c UI Scenarios - UT测试

单元测试：测试UI操作场景组件，直接使用L1/L2层真实服务，不打桩不mock
"""

import pytest
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.create_project import CreateProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.update_project import UpdateProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.delete_project import DeleteProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.list_projects import ListProjects
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.create_session import CreateSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.update_session import UpdateSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.delete_session import DeleteSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.archive_session import ArchiveSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.list_sessions import ListSessions
from services.L3_scenario_coordination.L3c_ui_scenarios.DialogueOutputManager.stream_output import StreamOutput
from services.L3_scenario_coordination.L3c_ui_scenarios.DialogueOutputManager.think_block import ThinkBlock
from services.L3_scenario_coordination.L3c_ui_scenarios.DialogueOutputManager.tool_call import ToolCall
from services.L3_scenario_coordination.L3c_ui_scenarios.DialogueOutputManager.message_display import MessageDisplay
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.workspace_config import WorkspaceConfig
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.model_config import ModelConfig
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.tool_config import ToolConfig
from services.L2_domain.L2a_project_config.project_service import ProjectService

class TestProjectManager:
    """测试项目管理组件 - UT测试"""
    
    def test_create_project_basic(self, test_report):
        """测试创建基础项目"""
        manager = CreateProject()
        
        inputs = {
            "name": "Basic Project",
            "workspace_config_id": "ws-test-001",
            "model_config_id": "mc-test-001"
        }
        
        result = manager.execute(inputs)
        
        # 获取持久化数据
        project_service = ProjectService()
        project = project_service.get_project(result["project_id"])
        
        test_report(
            test_points=["测试创建项目", "验证项目持久化"],
            inputs=inputs,
            outputs={
                "project_id": result["project_id"],
                "name": result["name"]
            },
            persistent_data={
                "project_exists": project is not None,
                "project_name": project.name if project else None
            }
        )
        
        assert "project_id" in result
        assert result["name"] == "Basic Project"
    
    def test_create_project_with_configs(self, test_report):
        """测试创建带配置的项目"""
        manager = CreateProject()
        
        inputs = {
            "name": "Project with Configs",
            "workspace_config_id": "ws-test-002",
            "model_config_id": "mc-test-002",
            "description": "Test project"
        }
        
        result = manager.execute(inputs)
        
        test_report(
            test_points=["测试创建项目带配置", "验证配置关联"],
            inputs=inputs,
            outputs={
                "project_id": result["project_id"],
                "name": result["name"]
            }
        )
        
        assert "project_id" in result
    
    def test_update_project_description(self, test_report):
        """测试更新项目描述"""
        create_manager = CreateProject()
        project = create_manager.execute({
            "name": "Update Test Project",
            "workspace_config_id": "ws-test",
            "model_config_id": "mc-test"
        })
        
        update_manager = UpdateProject()
        
        inputs = {
            "project_id": project["project_id"],
            "description": "Updated description"
        }
        
        result = update_manager.execute(project["project_id"], inputs)
        
        test_report(
            test_points=["测试更新项目描述", "验证描述修改"],
            inputs=inputs,
            outputs={
                "project_id": result["project_id"],
                "description": result["description"]
            }
        )
        
        assert result["description"] == "Updated description"
    
    def test_update_project_name(self, test_report):
        """测试更新项目名称"""
        create_manager = CreateProject()
        project = create_manager.execute({
            "name": "Old Name Project",
            "workspace_config_id": "ws-test",
            "model_config_id": "mc-test"
        })
        
        update_manager = UpdateProject()
        
        inputs = {
            "project_id": project["project_id"],
            "name": "New Name Project"
        }
        
        result = update_manager.execute(project["project_id"], inputs)
        
        test_report(
            test_points=["测试更新项目名称", "验证名称修改"],
            inputs=inputs,
            outputs={
                "project_id": result["project_id"],
                "name": result["name"]
            }
        )
        
        assert result["name"] == "New Name Project"
    
    def test_delete_project(self, test_report):
        """测试删除项目"""
        create_manager = CreateProject()
        project = create_manager.execute({
            "name": "Project to Delete",
            "workspace_config_id": "ws-test",
            "model_config_id": "mc-test"
        })
        
        delete_manager = DeleteProject()
        
        inputs = {"project_id": project["project_id"]}
        result = delete_manager.execute(project["project_id"])
        
        # 验证项目已删除
        project_service = ProjectService()
        deleted_project = project_service.get_project(project["project_id"])
        
        test_report(
            test_points=["测试删除项目", "验证项目删除"],
            inputs=inputs,
            outputs={"success": result["success"]},
            persistent_data={"project_exists": deleted_project is not None}
        )
        
        assert result["success"] is True
    
    def test_list_projects_empty(self, test_report):
        """测试列出空项目列表"""
        list_manager = ListProjects()
        result = list_manager.execute()
        
        test_report(
            test_points=["测试列出项目-空列表", "验证空列表处理"],
            inputs={},
            outputs={"project_count": len(result)}
        )
        
        assert isinstance(result, list)
    
    def test_list_projects_multiple(self, test_report):
        """测试列出多个项目"""
        create_manager = CreateProject()
        create_manager.execute({
            "name": "Project Alpha",
            "workspace_config_id": "ws-test-001",
            "model_config_id": "mc-test-001"
        })
        create_manager.execute({
            "name": "Project Beta",
            "workspace_config_id": "ws-test-001",
            "model_config_id": "mc-test-001"
        })
        create_manager.execute({
            "name": "Project Gamma",
            "workspace_config_id": "ws-test-001",
            "model_config_id": "mc-test-001"
        })
        
        list_manager = ListProjects()
        result = list_manager.execute()
        
        test_report(
            test_points=["测试列出项目-多个", "验证多项目查询"],
            inputs={},
            outputs={"project_count": len(result)}
        )
        
        assert len(result) >= 3

class TestSessionManager:
    """测试会话管理组件 - UT测试"""
    
    def test_create_session_basic(self, test_report):
        """测试创建基础会话"""
        manager = CreateSession()
        
        inputs = {
            "name": "Basic Session",
            "project_id": "proj-001"
        }
        
        result = manager.execute(inputs)
        
        test_report(
            test_points=["测试创建会话", "验证会话持久化"],
            inputs=inputs,
            outputs={
                "session_id": result["session_id"],
                "name": result["name"],
                "project_id": result["project_id"]
            }
        )
        
        assert "session_id" in result
        assert result["name"] == "Basic Session"
    
    def test_create_session_default_name(self, test_report):
        """测试创建默认名称的会话"""
        manager = CreateSession()
        
        inputs = {}
        result = manager.execute(inputs)
        
        test_report(
            test_points=["测试创建会话-默认名称", "验证默认值"],
            inputs=inputs,
            outputs={
                "session_id": result["session_id"],
                "name": result["name"]
            }
        )
        
        assert "session_id" in result
        assert result["name"] == "New Session"
    
    def test_update_session_name(self, test_report):
        """测试更新会话名称"""
        create_manager = CreateSession()
        session = create_manager.execute({"name": "Old Session"})
        
        update_manager = UpdateSession()
        
        inputs = {
            "session_id": session["session_id"],
            "name": "Updated Session"
        }
        
        result = update_manager.execute(session["session_id"], {"name": "Updated Session"})
        
        test_report(
            test_points=["测试更新会话名称", "验证名称修改"],
            inputs=inputs,
            outputs={"name": result["name"]}
        )
        
        assert result["name"] == "Updated Session"
    
    def test_delete_session(self, test_report):
        """测试删除会话"""
        create_manager = CreateSession()
        session = create_manager.execute({"name": "Session to Delete"})
        
        delete_manager = DeleteSession()
        
        inputs = {"session_id": session["session_id"]}
        result = delete_manager.execute(session["session_id"])
        
        test_report(
            test_points=["测试删除会话", "验证会话删除"],
            inputs=inputs,
            outputs={"success": result["success"]}
        )
        
        assert result["success"] is True
    
    def test_archive_session(self, test_report):
        """测试归档会话"""
        create_manager = CreateSession()
        session = create_manager.execute({"name": "Session to Archive"})
        
        archive_manager = ArchiveSession()
        
        inputs = {"session_id": session["session_id"]}
        result = archive_manager.execute(session["session_id"])
        
        test_report(
            test_points=["测试归档会话", "验证归档状态"],
            inputs=inputs,
            outputs={
                "is_archived": result["is_archived"],
                "is_active": result["is_active"]
            }
        )
        
        assert result["is_archived"] is True
        assert result["is_active"] is False
    
    def test_list_sessions(self, test_report):
        """测试列出会话"""
        create_manager = CreateSession()
        create_manager.execute({"name": "Session 1"})
        create_manager.execute({"name": "Session 2"})
        
        list_manager = ListSessions()
        result = list_manager.execute()
        
        test_report(
            test_points=["测试列出会话", "验证会话查询"],
            inputs={},
            outputs={"session_count": len(result)}
        )
        
        assert len(result) >= 2

class TestDialogueOutputManager:
    """测试对话输出管理组件 - UT测试"""
    
    def test_stream_output_basic(self, test_report):
        """测试流式输出基本功能"""
        streamer = StreamOutput()
        
        def generate_stream():
            yield "Hello"
            yield " "
            yield "World"
        
        inputs = {"stream_data": ["Hello", " ", "World"]}
        results = list(streamer.process_stream(generate_stream()))
        
        test_report(
            test_points=["测试流式输出", "验证流式处理"],
            inputs=inputs,
            outputs={
                "chunk_count": len(results),
                "first_chunk": results[0]["content"],
                "is_complete": results[-1]["is_complete"]
            }
        )
        
        assert len(results) == 4
        assert results[0]["content"] == "Hello"
    
    def test_stream_output_empty(self, test_report):
        """测试空流输出"""
        streamer = StreamOutput()
        
        def generate_empty_stream():
            yield from []
        
        inputs = {"stream_data": []}
        results = list(streamer.process_stream(generate_empty_stream()))
        
        test_report(
            test_points=["测试流式输出-空流", "验证空流处理"],
            inputs=inputs,
            outputs={"chunk_count": len(results)}
        )
        
        assert len(results) == 1
        assert results[0]["is_complete"] is True
    
    def test_think_block_format(self, test_report):
        """测试思考块格式化"""
        formatter = ThinkBlock()
        
        inputs = {"content": "正在分析用户意图"}
        result = formatter.format_thinking(inputs)
        
        test_report(
            test_points=["测试思考块格式化", "验证格式处理"],
            inputs=inputs,
            outputs={"formatted": result}
        )
        
        assert result["type"] == "thinking"
    
    def test_tool_call_format(self, test_report):
        """测试工具调用格式化"""
        formatter = ToolCall()
        
        inputs = {
            "tool_name": "calculator",
            "parameters": {"expression": "2 + 3"}
        }
        result = formatter.format_tool_call(inputs)
        
        test_report(
            test_points=["测试工具调用格式化", "验证工具信息展示"],
            inputs=inputs,
            outputs={"formatted": result}
        )
        
        assert result["tool_name"] == "calculator"
    
    def test_message_display_format(self, test_report):
        """测试消息显示格式化"""
        formatter = MessageDisplay()
        
        inputs = {
            "role": "assistant",
            "content": "这是助手回复"
        }
        result = formatter.format_message(inputs)
        
        test_report(
            test_points=["测试消息显示格式化", "验证消息格式"],
            inputs=inputs,
            outputs={"formatted": result}
        )
        
        assert result["role"] == "assistant"

class TestConfigManager:
    """测试配置管理组件 - UT测试"""
    
    def test_workspace_config_full_crud(self, test_report):
        """测试工作区配置完整CRUD"""
        config = WorkspaceConfig()
        
        # 创建
        create_input = {
            "name": "Test Workspace",
            "root_path": "/workspace/test",
            "type": "local"
        }
        create_result = config.create(create_input)
        config_id = create_result["config_id"]
        
        # 读取
        read_result = config.get(config_id)
        
        # 更新
        update_input = {"name": "Updated Workspace"}
        update_result = config.update(config_id, update_input)
        
        # 列出
        list_result = config.list()
        
        # 删除
        delete_result = config.delete(config_id)
        
        test_report(
            test_points=[
                "测试工作区配置CRUD",
                "验证创建、读取、更新、删除"
            ],
            inputs={
                "create": create_input,
                "update": update_input,
                "delete": {"config_id": config_id}
            },
            outputs={
                "created": create_result,
                "read": read_result,
                "updated": update_result,
                "list_count": len(list_result),
                "deleted": delete_result
            }
        )
        
        assert create_result["name"] == "Test Workspace"
        assert delete_result["success"] is True
    
    def test_model_config_full_crud(self, test_report):
        """测试模型配置完整CRUD"""
        config = ModelConfig()
        
        # 创建
        create_input = {
            "name": "Test Model",
            "model_name": "qwen-7b",
            "api_type": "cloud",
            "api_address": "https://api.example.com"
        }
        create_result = config.create(create_input)
        config_id = create_result["config_id"]
        
        # 读取
        read_result = config.get(config_id)
        
        # 更新
        update_input = {"name": "Updated Model"}
        update_result = config.update(config_id, update_input)
        
        # 列出
        list_result = config.list()
        
        # 删除
        delete_result = config.delete(config_id)
        
        test_report(
            test_points=[
                "测试模型配置CRUD",
                "验证创建、读取、更新、删除"
            ],
            inputs={
                "create": create_input,
                "update": update_input,
                "delete": {"config_id": config_id}
            },
            outputs={
                "created": create_result,
                "read": read_result,
                "updated": update_result,
                "list_count": len(list_result),
                "deleted": delete_result
            }
        )
        
        assert create_result["name"] == "Test Model"
        assert delete_result["success"] is True
    
    def test_tool_config_full_crud(self, test_report):
        """测试工具配置完整CRUD"""
        config = ToolConfig()
        
        # 注册
        register_input = {
            "name": "Test Tool",
            "description": "Test description",
            "category": "test"
        }
        register_result = config.register(register_input)
        
        # 查询
        query_result = config.query(register_input["name"])
        
        # 更新
        update_input = {"description": "Updated description"}
        update_result = config.update(register_input["name"], update_input)
        
        # 列出
        list_result = config.list()
        
        # 注销
        unregister_result = config.unregister(register_input["name"])
        
        test_report(
            test_points=[
                "测试工具配置CRUD",
                "验证注册、查询、更新、注销"
            ],
            inputs={
                "register": register_input,
                "update": update_input,
                "unregister": {"tool_name": register_input["name"]}
            },
            outputs={
                "registered": register_result,
                "queried": query_result,
                "updated": update_result,
                "list_count": len(list_result),
                "unregistered": unregister_result
            }
        )
        
        assert register_result["tool_name"] == "Test Tool"
        assert unregister_result["success"] is True
