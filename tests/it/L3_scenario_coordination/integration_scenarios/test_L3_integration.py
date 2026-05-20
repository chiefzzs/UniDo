"""
L3层集成测试（IT测试）

测试场景：
1. 对话服务与任务执行服务的集成
2. 会话管理与项目管理的集成
3. 配置管理与工具管理的集成
4. 任务编排服务与意图分析服务的集成

所有测试直接使用L1/L2层真实服务，不打桩不mock
"""

import pytest

# L3层服务
from services.L3_scenario_coordination.L3a_task_coordination.dialogue_service import DialogueService
from services.L3_scenario_coordination.L3a_task_coordination.intent_service import IntentService
from services.L3_scenario_coordination.L3a_task_coordination.base_execution_service import BaseExecutionService
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.create_project import CreateProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.list_projects import ListProjects
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.create_session import CreateSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.list_sessions import ListSessions
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.workspace_config import WorkspaceConfig
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.tool_config import ToolConfig

class TestDialogueIntegration:
    """测试对话服务集成 - IT测试"""
    
    def test_dialogue_with_intent_and_execution(self, test_report):
        """测试对话服务与意图分析、任务执行的完整集成"""
        dialogue_service = DialogueService()
        intent_service = IntentService()
        execution_service = BaseExecutionService()
        
        inputs = {"user_input": "你好"}
        
        # 分析意图
        intent_result = intent_service.analyze_intent(inputs)
        
        # 处理对话
        response = dialogue_service.process_dialogue("test-session-1", inputs["user_input"])
        
        test_report(
            test_points=[
                "测试对话服务与意图分析集成",
                "验证对话服务与任务执行集成",
                "验证完整对话流程"
            ],
            inputs=inputs,
            outputs={
                "session_id": response.session_id,
                "status": response.status,
                "content": response.content,
                "execution_path": intent_result.execution_path.value
            }
        )
        
        assert response is not None
        assert response.session_id == "test-session-1"
        assert response.status == "completed"
    
    def test_dialogue_tool_execution_flow(self, test_report):
        """测试对话中工具执行的完整流程"""
        dialogue_service = DialogueService()
        
        inputs = {"user_input": "计算 2 + 3"}
        response = dialogue_service.process_dialogue("test-session-tool", inputs["user_input"])
        
        test_report(
            test_points=[
                "测试对话工具执行流程",
                "验证工具调用集成"
            ],
            inputs=inputs,
            outputs={
                "session_id": response.session_id,
                "status": response.status
            }
        )
        
        assert response is not None
        assert response.status == "completed"

class TestProjectSessionIntegration:
    """测试项目与会话的集成 - IT测试"""
    
    def test_create_project_and_session(self, test_report):
        """测试创建项目后创建会话的集成流程"""
        # 创建项目
        create_project = CreateProject()
        project_input = {
            "name": "Integration Test Project",
            "workspace_config_id": "ws-test-it",
            "model_config_id": "mc-test-it"
        }
        project = create_project.execute(project_input)
        
        # 创建会话关联到项目
        create_session = CreateSession()
        session_input = {
            "name": "Integration Test Session",
            "project_id": project["project_id"]
        }
        session = create_session.execute(session_input)
        
        test_report(
            test_points=[
                "测试项目与会话集成",
                "验证项目创建后会话关联"
            ],
            inputs={
                "project": project_input,
                "session": session_input
            },
            outputs={
                "project_id": project["project_id"],
                "session_id": session["session_id"],
                "session_project_id": session["project_id"]
            }
        )
        
        assert "project_id" in project
        assert "session_id" in session
        assert session["project_id"] == project["project_id"]
    
    def test_list_projects_and_sessions(self, test_report):
        """测试列出项目和会话的集成"""
        # 创建多个项目
        create_project = CreateProject()
        create_project.execute({"name": "Project A", "workspace_config_id": "ws-a", "model_config_id": "mc-a"})
        create_project.execute({"name": "Project B", "workspace_config_id": "ws-b", "model_config_id": "mc-b"})
        
        # 创建多个会话
        create_session = CreateSession()
        create_session.execute({"name": "Session 1"})
        create_session.execute({"name": "Session 2"})
        
        # 列出项目和会话
        list_projects = ListProjects()
        projects = list_projects.execute()
        
        list_sessions = ListSessions()
        sessions = list_sessions.execute()
        
        test_report(
            test_points=[
                "测试列出项目和会话",
                "验证多项目多会话查询"
            ],
            inputs={},
            outputs={
                "project_count": len(projects),
                "session_count": len(sessions)
            }
        )
        
        assert len(projects) >= 2
        assert len(sessions) >= 2

class TestConfigIntegration:
    """测试配置管理集成 - IT测试"""
    
    def test_workspace_and_tool_config(self, test_report):
        """测试工作区配置与工具配置的集成"""
        # 创建工作区配置
        workspace_config = WorkspaceConfig()
        workspace_input = {
            "name": "IT Test Workspace",
            "root_path": "/workspace/it-test",
            "type": "local"
        }
        workspace = workspace_config.create(workspace_input)
        
        # 创建工具配置
        tool_config = ToolConfig()
        tool_input = {
            "name": "IT Test Tool",
            "description": "Integration test tool",
            "category": "test"
        }
        tool = tool_config.register(tool_input)
        
        test_report(
            test_points=[
                "测试工作区配置与工具配置集成",
                "验证配置创建流程"
            ],
            inputs={
                "workspace": workspace_input,
                "tool": tool_input
            },
            outputs={
                "workspace_config_id": workspace.get("config_id"),
                "tool_name": tool.get("tool_name")
            }
        )
        
        assert "config_id" in workspace
        assert "tool_name" in tool
        assert tool["tool_name"] == "IT Test Tool"

class TestTaskOrchestrationIntegration:
    """测试任务编排集成 - IT测试"""
    
    def test_intent_to_task_execution(self, test_report):
        """测试从意图分析到任务执行的完整流程"""
        intent_service = IntentService()
        execution_service = BaseExecutionService()
        
        # 分析意图
        intent_input = {"user_input": "分析这个任务并执行"}
        intent_result = intent_service.analyze_intent(intent_input)
        
        # 执行任务
        from services.L3_scenario_coordination.schemas import Task
        task = Task(task_id="it-test-task", input_data={"user_input": "分析任务"})
        result = execution_service.execute_task(task)
        
        test_report(
            test_points=[
                "测试意图分析到任务执行流程",
                "验证任务编排集成"
            ],
            inputs={
                "intent_input": intent_input,
                "task_input": {"task_id": task.task_id, "user_input": "分析任务"}
            },
            outputs={
                "execution_path": intent_result.execution_path.value,
                "task_status": result.status.value,
                "output_data": result.output_data
            }
        )
        
        assert result is not None
        assert result.status.value == "completed"
    
    def test_task_group_execution(self, test_report):
        """测试任务组执行流程"""
        intent_service = IntentService()
        execution_service = BaseExecutionService()
        
        # 分析意图（任务组模式）
        intent_input = {"user_input": "先分析需求，然后执行操作，最后汇总结果"}
        intent_result = intent_service.analyze_intent(intent_input)
        
        # 执行任务
        from services.L3_scenario_coordination.schemas import Task
        task = Task(task_id="it-group-task", input_data={"user_input": "任务组执行"})
        result = execution_service.execute_task(task)
        
        test_report(
            test_points=[
                "测试任务组执行流程",
                "验证多步骤任务编排"
            ],
            inputs={
                "intent_input": intent_input,
                "task_input": {"task_id": task.task_id, "user_input": "任务组执行"}
            },
            outputs={
                "execution_path": intent_result.execution_path.value,
                "task_status": result.status.value,
                "subtask_count": result.output_data.get("subtask_count"),
                "execution_mode": result.output_data.get("execution_mode")
            }
        )
        
        assert result is not None
        assert result.status.value == "completed"
        assert "subtask_count" in result.output_data
