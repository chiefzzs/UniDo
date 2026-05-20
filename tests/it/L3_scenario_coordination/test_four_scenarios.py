"""
L3 四大场景测试用例

测试场景：
- SC04: 简单单次文本对话
- SC05: 简单单次工具对话
- SC16: 任务组对话
- SC17: 嵌套任务组对话
"""

import pytest
import os
import sys
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['STORAGE_ENV'] = 'test'

from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.session_manager import SessionManager
from services.L3_scenario_coordination.L3c_ui_scenarios.DialogManager.dialog_manager import DialogManager
from services.L3_scenario_coordination.L3c_ui_scenarios.MessageManager.message_manager import MessageManager
from services.L3_scenario_coordination.L3a_task_coordination.dialogue_based_llm_service import DialogueBasedLLMService
from services.L3_scenario_coordination.L3a_task_coordination.intent_service import IntentService
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory


class TestFourScenarios:
    """四大场景测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试前的清理和初始化"""
        # 清理测试数据
        self._cleanup_test_data()
        
        # 初始化组件
        self.session_manager = SessionManager()
        self.dialog_manager = DialogManager()
        self.message_manager = MessageManager()
        self.dialogue_llm_service = DialogueBasedLLMService()
        self.intent_service = IntentService()
        self.persistence = StorageFactory.create()
        
        yield
        
        # 测试后清理（可选）
        # self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """清理测试数据"""
        persistence = StorageFactory.create()
        try:
            # 清空测试数据
            persistence._write_all('sessions', [])
            persistence._write_all('dialogs', [])
            persistence._write_all('messages', [])
            persistence._write_all('events', [])
        except Exception as e:
            print(f"清理测试数据失败: {e}")
    
    def _create_test_session(self):
        """创建测试会话"""
        result = self.session_manager.create_session(
            project_id="test-project",
            name="测试会话"
        )
        return result
    
    def test_sc04_simple_text_dialogue(self):
        """
        SC04: 简单单次文本对话
        
        特征：无工具调用，直接LLM返回文本
        执行路径：DIRECT_COMPLETION
        数据流：用户输入 → IntentService → DialogueBasedLLMService → L2d LLM执行服务 → 助手回复
        """
        # 1. 创建会话
        session_result = self._create_test_session()
        session_id = session_result['session']['session_id']
        dialog_id = session_result['dialog']['dialog_id']
        
        # 2. 用户输入简单问候
        user_input = "你好，很高兴认识你"
        
        # 3. 意图分析
        intent_result = self.intent_service.analyze_intent(
            task_input={
                'session_id': session_id,
                'user_input': user_input
            }
        )
        
        # 验证意图分析结果
        assert intent_result.execution_path.value == 'direct_completion'
        
        # 4. 调用DialogueBasedLLMService
        llm_response = self.dialogue_llm_service.call_llm(
            session_id=session_id,
            user_input=user_input
        )
        
        # 验证LLM响应
        assert llm_response.success is True
        assert llm_response.content is not None
        assert len(llm_response.content) > 0
        assert llm_response.tool_calls is None or len(llm_response.tool_calls) == 0
        
        # 5. 保存消息
        user_message = self.message_manager.create_user_message(
            dialog_id=dialog_id,
            content=user_input
        )
        
        assistant_message = self.message_manager.create_assistant_message(
            dialog_id=dialog_id,
            content=llm_response.content
        )
        
        # 验证消息保存
        assert user_message['role'] == 'user'
        assert assistant_message['role'] == 'assistant'
        
        # 6. 验证持久化数据
        sessions = self.persistence.list('sessions')
        dialogs = self.persistence.list('dialogs')
        messages = self.persistence.list('messages')
        
        assert len(sessions) == 1
        assert len(dialogs) == 1
        assert len(messages) == 3  # system + user + assistant
        
        print(f"✓ SC04测试通过: {llm_response.content[:50]}...")
    
    def test_sc05_single_tool_dialogue(self):
        """
        SC05: 简单单次工具对话
        
        特征：LLM选择并调用单个工具，返回结果
        执行路径：SINGLE_TOOL
        数据流：用户输入 → IntentService → ToolTaskExecutor → L2c工具执行服务 → 工具结果 → 助手回复
        """
        # 1. 创建会话
        session_result = self._create_test_session()
        session_id = session_result['session']['session_id']
        dialog_id = session_result['dialog']['dialog_id']
        
        # 2. 用户输入需要工具调用的请求
        user_input = "帮我读取README.md文件"
        
        # 3. 意图分析
        intent_result = self.intent_service.analyze_intent(
            task_input={
                'session_id': session_id,
                'user_input': user_input
            }
        )
        
        # 验证意图分析结果
        assert intent_result.execution_path.value in ['single_tool', 'task_group']
        
        # 4. 调用DialogueBasedLLMService（包含工具）
        llm_response = self.dialogue_llm_service.call_llm(
            session_id=session_id,
            user_input=user_input,
            include_tools=True
        )
        
        # 验证LLM响应
        assert llm_response.success is True
        
        # 5. 保存消息
        user_message = self.message_manager.create_user_message(
            dialog_id=dialog_id,
            content=user_input
        )
        
        # 如果有工具调用，保存工具消息
        if llm_response.tool_calls and len(llm_response.tool_calls) > 0:
            for tool_call in llm_response.tool_calls:
                assistant_message = self.message_manager.create_assistant_message(
                    dialog_id=dialog_id,
                    content="",
                    tool_calls=[tool_call]
                )
                
                # 模拟工具执行结果
                tool_result = self.message_manager.create_tool_message(
                    dialog_id=dialog_id,
                    content='{"result": "README.md内容"}',
                    call_id=tool_call.get('id', ''),
                    tool_name=tool_call.get('function', {}).get('name', ''),
                    success=True
                )
        
        # 6. 验证持久化数据
        messages = self.persistence.list('messages')
        assert len(messages) >= 2  # 至少有system和user消息
        
        print(f"✓ SC05测试通过: 工具调用流程验证成功")
    
    def test_sc16_task_group_dialogue(self):
        """
        SC16: 任务组对话
        
        特征：拆解为多个任务，顺序/并行执行
        执行路径：TASK_GROUP
        数据流：用户输入 → IntentService → TaskGroupExecutor → TaskExecutionService → 子任务执行 → 结果聚合
        """
        # 1. 创建会话
        session_result = self._create_test_session()
        session_id = session_result['session']['session_id']
        dialog_id = session_result['dialog']['dialog_id']
        
        # 2. 用户输入需要多个任务协作的请求
        user_input = "分析项目结构并生成文档"
        
        # 3. 意图分析
        intent_result = self.intent_service.analyze_intent(
            task_input={
                'session_id': session_id,
                'user_input': user_input
            }
        )
        
        # 验证意图分析结果
        assert intent_result.execution_path.value == 'task_group'
        
        # 4. 生成任务规划
        task_plan = self.dialogue_llm_service.generate_task_plan(
            session_id=session_id,
            user_input=user_input
        )
        
        # 验证任务规划
        assert 'tasks' in task_plan
        assert len(task_plan['tasks']) >= 2  # 至少有两个子任务
        assert 'execution_mode' in task_plan
        
        # 5. 保存消息
        user_message = self.message_manager.create_user_message(
            dialog_id=dialog_id,
            content=user_input
        )
        
        # 6. 验证持久化数据
        messages = self.persistence.list('messages')
        assert len(messages) >= 2  # 至少有system和user消息
        
        print(f"✓ SC16测试通过: 任务组规划验证成功，包含{len(task_plan['tasks'])}个子任务")
    
    def test_sc17_nested_task_group_dialogue(self):
        """
        SC17: 嵌套任务组对话
        
        特征：任务组中嵌套子任务组，递归执行
        执行路径：TASK_GROUP（嵌套）
        数据流：用户输入 → IntentService → TaskGroupExecutor → 递归TaskGroupExecutor → 自底向上聚合
        """
        # 1. 创建会话
        session_result = self._create_test_session()
        session_id = session_result['session']['session_id']
        dialog_id = session_result['dialog']['dialog_id']
        
        # 2. 用户输入需要嵌套任务组的复杂请求
        user_input = "分析整个项目，包括代码结构、依赖关系、测试覆盖率，并生成完整的分析报告"
        
        # 3. 意图分析
        intent_result = self.intent_service.analyze_intent(
            task_input={
                'session_id': session_id,
                'user_input': user_input
            }
        )
        
        # 验证意图分析结果
        assert intent_result.execution_path.value == 'task_group'
        
        # 4. 生成任务规划
        task_plan = self.dialogue_llm_service.generate_task_plan(
            session_id=session_id,
            user_input=user_input
        )
        
        # 验证任务规划
        assert 'tasks' in task_plan
        assert len(task_plan['tasks']) >= 3  # 至少有三个子任务
        
        # 检查是否有嵌套任务（通过dependencies判断）
        has_nested = any(
            len(task.get('dependencies', [])) > 0 
            for task in task_plan['tasks']
        )
        assert has_nested, "应该有嵌套任务关系"
        
        # 5. 保存消息
        user_message = self.message_manager.create_user_message(
            dialog_id=dialog_id,
            content=user_input
        )
        
        # 6. 验证持久化数据
        messages = self.persistence.list('messages')
        assert len(messages) >= 2  # 至少有system和user消息
        
        print(f"✓ SC17测试通过: 嵌套任务组验证成功，包含{len(task_plan['tasks'])}个子任务")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])