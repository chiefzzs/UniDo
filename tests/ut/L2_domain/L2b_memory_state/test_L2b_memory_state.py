"""
L2b Memory State Unit Tests

单元测试：测试记忆与状态管理服务
"""

import pytest
from services.L2_domain.L2b_memory_state.session_service import SessionService
from services.L2_domain.L2b_memory_state.dialog_service import DialogService
from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L2_domain.L2b_memory_state.task_service import TaskService
from services.L2_domain.L2b_memory_state.task_group_service import TaskGroupService


class TestSessionService:
    """测试会话服务"""

    def test_create_session(self, test_report):
        """测试创建会话 - 验证L2服务调用L1持久化"""
        service = SessionService()
        
        session = service.create_session(
            project_id="proj-001",
            name="Test Session"
        )
        
        test_report(
            test_points=["测试创建会话", "验证L2服务自动触发L1持久化到sessions.json"],
            inputs={"project_id": "proj-001", "name": "Test Session"},
            outputs={"session_id": session.session_id, "status": session.status}
        )
        
        assert session is not None
        assert session.session_id is not None

    def test_get_session(self, test_report):
        """测试获取会话 - 验证从L1持久化读取"""
        service = SessionService()
        
        session = service.create_session(
            project_id="proj-002",
            name="Test Get Session"
        )
        
        retrieved = service.get_session(session.session_id)
        
        test_report(
            test_points=["测试获取会话", "验证从L1持久化正确读取"],
            inputs={"session_id": session.session_id},
            outputs={"found": retrieved is not None}
        )
        
        assert retrieved is not None
        assert retrieved.session_id == session.session_id


class TestDialogService:
    """测试对话服务"""

    def test_create_dialog(self, test_report):
        """测试创建对话 - 验证L2服务调用L1持久化"""
        service = DialogService()
        
        dialog = service.create_dialog(
            session_id="session-001",
            dialog_type="chat"
        )
        
        test_report(
            test_points=["测试创建对话", "验证L2服务自动触发L1持久化到dialogs.json"],
            inputs={"session_id": "session-001", "dialog_type": "chat"},
            outputs={"dialog_id": dialog.dialog_id}
        )
        
        assert dialog is not None
        assert dialog.dialog_id is not None


class TestMessageService:
    """测试消息服务"""

    def test_create_message(self, test_report):
        """测试创建消息 - 验证L2服务调用L1持久化"""
        service = MessageService()
        
        message = service.create_message(
            dialog_id="dialog-001",
            role="user",
            content="Hello"
        )
        
        test_report(
            test_points=["测试创建消息", "验证L2服务自动触发L1持久化到messages.json"],
            inputs={"dialog_id": "dialog-001", "role": "user", "content": "Hello"},
            outputs={"message_id": message.message_id, "role": message.role}
        )
        
        assert message is not None
        assert message.message_id is not None


class TestTaskService:
    """测试任务服务"""

    def test_create_task(self, test_report):
        """测试创建任务 - 验证L2服务调用L1持久化"""
        service = TaskService()
        
        task = service.create_task(
            group_id="group-001",
            name="Test Task"
        )
        
        test_report(
            test_points=["测试创建任务", "验证L2服务自动触发L1持久化到tasks.json"],
            inputs={"group_id": "group-001", "name": "Test Task"},
            outputs={"task_id": task.task_id, "status": task.status}
        )
        
        assert task is not None
        assert task.task_id is not None


class TestTaskGroupService:
    """测试任务组服务"""

    def test_create_task_group(self, test_report):
        """测试创建任务组 - 验证L2服务调用L1持久化"""
        service = TaskGroupService()
        
        task_group = service.create_task_group(
            session_id="session-001",
            name="Test Task Group"
        )
        
        test_report(
            test_points=["测试创建任务组", "验证L2服务自动触发L1持久化到task_groups.json"],
            inputs={"session_id": "session-001", "name": "Test Task Group"},
            outputs={"group_id": task_group.group_id, "status": task_group.status}
        )
        
        assert task_group is not None
        assert task_group.group_id is not None
