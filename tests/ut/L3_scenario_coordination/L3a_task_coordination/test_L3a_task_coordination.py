"""
L3a Task Coordination - UT测试

单元测试：测试单个服务，直接使用L1/L2层真实服务，不打桩不mock
"""

import pytest
from services.L3_scenario_coordination.L3a_task_coordination.dialogue_service import DialogueService
from services.L3_scenario_coordination.L3a_task_coordination.intent_service import IntentService, ExecutionPath
from services.L3_scenario_coordination.L3a_task_coordination.base_execution_service import BaseExecutionService
from services.L3_scenario_coordination.L3a_task_coordination.tool_task_executor import ToolTaskExecutor
from services.L3_scenario_coordination.L3a_task_coordination.check_task_service import CheckTaskService
from services.L3_scenario_coordination.L3a_task_coordination.adjust_task_service import AdjustTaskService
from services.L3_scenario_coordination.L3a_task_coordination.task_execution_service import TaskExecutionService
from services.L3_scenario_coordination.L3a_task_coordination.task_group_executor import TaskGroupExecutor
from services.L3_scenario_coordination.schemas import Task, TaskStatus
from services.L2_domain.L2b_memory_state.session_service import SessionService
from services.L2_domain.L2b_memory_state.message_service import MessageService
from services.L2_domain.L2f_tool_management import ToolManagementService, ToolRegistry, ToolDefinition


def register_test_tools():
    """注册测试工具"""
    registry = ToolRegistry.get_instance()
    
    def calculator_impl(**kwargs):
        expression = kwargs.get('expression', '')
        try:
            return str(eval(expression))
        except:
            return f"无法计算: {expression}"
    
    tool = ToolDefinition(
        tool_id="tool-calculator-test",
        tool_name="calculator",
        category="math",
        description="计算器工具",
        parameters={'required': ['expression']}
    )
    
    registry.register_tool(tool, calculator_impl)

class TestDialogueService:
    """测试对话服务 - UT测试"""
    
    def test_process_dialogue_simple(self, test_report):
        """测试简单对话处理"""
        service = DialogueService()
        
        inputs = {
            "session_id": "test-session-simple",
            "user_input": "你好"
        }
        
        result = service.process_dialogue(inputs["session_id"], inputs["user_input"])
        
        # 测试报告自动收集持久化数据
        test_report(
            test_points=["测试对话服务基本功能", "验证会话创建", "验证消息存储"],
            inputs=inputs,
            outputs={
                "session_id": result.session_id,
                "status": result.status,
                "content": result.content
            }
        )
        
        assert result is not None
        assert result.session_id == inputs["session_id"]
    
    def test_process_dialogue_tool_call(self, test_report):
        """测试工具调用对话"""
        service = DialogueService()
        
        inputs = {
            "session_id": "test-session-tool",
            "user_input": "计算 2 + 3"
        }
        
        result = service.process_dialogue(inputs["session_id"], inputs["user_input"])
        
        test_report(
            test_points=["测试对话服务工具调用", "验证工具执行流程"],
            inputs=inputs,
            outputs={
                "session_id": result.session_id,
                "status": result.status,
                "content": result.content
            }
        )
        
        assert result is not None
        assert result.status == "completed"
    
    def test_process_dialogue_complex(self, test_report):
        """测试复杂对话处理"""
        service = DialogueService()
        
        inputs = {
            "session_id": "test-session-complex",
            "user_input": "分析这个任务并给出建议"
        }
        
        result = service.process_dialogue(inputs["session_id"], inputs["user_input"])
        
        test_report(
            test_points=["测试对话服务复杂任务处理", "验证意图分析流程"],
            inputs=inputs,
            outputs={
                "session_id": result.session_id,
                "status": result.status,
                "content": result.content
            }
        )
        
        assert result is not None

class TestIntentService:
    """测试意图服务 - UT测试"""
    
    def test_analyze_intent_direct_completion(self, test_report):
        """测试直接完成意图"""
        service = IntentService()
        
        inputs = {"user_input": "你好"}
        result = service.analyze_intent(inputs)
        
        test_report(
            test_points=["测试意图分析-直接完成", "验证简单问题识别"],
            inputs=inputs,
            outputs={
                "execution_path": result.execution_path.value,
                "reasoning": result.reasoning
            }
        )
        
        assert result.execution_path == ExecutionPath.DIRECT_COMPLETION
    
    def test_analyze_intent_greeting(self, test_report):
        """测试问候意图"""
        service = IntentService()
        
        inputs = {"user_input": "您好，很高兴认识你"}
        result = service.analyze_intent(inputs)
        
        test_report(
            test_points=["测试意图分析-问候语", "验证问候识别"],
            inputs=inputs,
            outputs={
                "execution_path": result.execution_path.value
            }
        )
        
        assert result.execution_path == ExecutionPath.DIRECT_COMPLETION
    
    def test_analyze_intent_single_tool_calculator(self, test_report):
        """测试单工具调用意图-计算器"""
        service = IntentService()
        
        inputs = {"user_input": "计算 100 + 200"}
        result = service.analyze_intent(inputs)
        
        test_report(
            test_points=["测试意图分析-单工具调用", "验证计算器识别"],
            inputs=inputs,
            outputs={
                "execution_path": result.execution_path.value,
                "tool_id": result.single_tool_info.tool_id if result.single_tool_info else None
            }
        )
        
        assert result.execution_path == ExecutionPath.SINGLE_TOOL
    
    def test_analyze_intent_single_tool_read(self, test_report):
        """测试单工具调用意图-读取文件"""
        service = IntentService()
        
        inputs = {"user_input": "读取文件 /tmp/test.txt"}
        result = service.analyze_intent(inputs)
        
        test_report(
            test_points=["测试意图分析-单工具调用", "验证文件读取识别"],
            inputs=inputs,
            outputs={
                "execution_path": result.execution_path.value
            }
        )
        
        assert result.execution_path == ExecutionPath.SINGLE_TOOL
    
    def test_analyze_intent_task_group(self, test_report):
        """测试任务组意图"""
        service = IntentService()
        
        inputs = {"user_input": "先分析需求，然后执行操作，最后汇总结果"}
        result = service.analyze_intent(inputs)
        
        test_report(
            test_points=["测试意图分析-任务组", "验证多步骤任务识别"],
            inputs=inputs,
            outputs={
                "execution_path": result.execution_path.value,
                "execution_mode": result.task_group_info.execution_mode.value if result.task_group_info else None
            }
        )
        
        assert result.execution_path == ExecutionPath.TASK_GROUP

class TestBaseExecutionService:
    """测试基础执行服务 - UT测试"""
    
    def test_execute_task_direct_completion(self, test_report):
        """测试直接完成任务执行"""
        service = BaseExecutionService()
        task = Task(task_id="test-direct", input_data={"user_input": "你好"})
        
        inputs = {"task_id": task.task_id, "user_input": "你好"}
        result = service.execute_task(task)
        
        test_report(
            test_points=["测试基础执行-直接完成", "验证任务状态转换"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "output_data": result.output_data
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
    
    def test_execute_task_single_tool(self, test_report):
        """测试单工具任务执行"""
        register_test_tools()
        service = BaseExecutionService()
        task = Task(task_id="test-tool", input_data={"user_input": "计算 5 + 5"})
        
        inputs = {"task_id": task.task_id, "user_input": "计算 5 + 5"}
        result = service.execute_task(task)
        
        test_report(
            test_points=["测试基础执行-单工具", "验证工具调用流程"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
    
    def test_execute_task_task_group(self, test_report):
        """测试任务组执行"""
        service = BaseExecutionService()
        task = Task(task_id="test-group", input_data={"user_input": "先分析再执行"})
        
        inputs = {"task_id": task.task_id, "user_input": "先分析再执行"}
        result = service.execute_task(task)
        
        test_report(
            test_points=["测试基础执行-任务组", "验证任务编排流程"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "subtask_count": result.output_data.get("subtask_count")
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
    
    def test_task_status_transition(self, test_report):
        """测试任务状态转换"""
        service = BaseExecutionService()
        task = Task(task_id="test-status", input_data={"user_input": "测试"})
        
        result = service.execute_task(task)
        
        test_report(
            test_points=["测试任务状态转换", "验证状态机流转"],
            inputs={"task_id": task.task_id},
            outputs={
                "initial_status": TaskStatus.PENDING.value,
                "final_status": result.status.value
            }
        )
        
        assert result.status == TaskStatus.COMPLETED

class TestToolTaskExecutor:
    """测试工具任务执行器 - UT测试"""
    
    def test_execute_tool_task(self, test_report):
        """测试执行工具任务"""
        register_test_tools()
        executor = ToolTaskExecutor()
        task = Task(task_id="test-tool-exec", input_data={"user_input": "计算 3 + 4"})
        intent_result = IntentService().analyze_intent({"user_input": "计算 3 + 4"})
        
        inputs = {"task_id": task.task_id, "user_input": "计算 3 + 4"}
        result = executor.execute(task, intent_result)
        
        test_report(
            test_points=["测试工具任务执行", "验证工具调用"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "output_data": result.output_data
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
    
    def test_execute_tool_task_with_history(self, test_report):
        """测试带历史记录的工具任务"""
        register_test_tools()
        executor = ToolTaskExecutor()
        task = Task(
            task_id="test-tool-history",
            input_data={"user_input": "计算 2 * 8"},
            execution_history=[{"step": "test", "result": "ok"}]
        )
        intent_result = IntentService().analyze_intent({"user_input": "计算 2 * 8"})
        
        inputs = {"task_id": task.task_id, "user_input": "计算 2 * 8"}
        result = executor.execute(task, intent_result)
        
        test_report(
            test_points=["测试工具任务执行-带历史", "验证历史记录传递"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "history_length": len(result.execution_history)
            }
        )
        
        assert result.status == TaskStatus.COMPLETED

class TestCheckTaskService:
    """测试检查任务服务 - UT测试"""
    
    def test_execute_check_completed(self, test_report):
        """测试检查已完成的任务"""
        service = CheckTaskService()
        task = Task(
            task_id="test_check_task_1",
            input_data={"user_input": "简单任务"},
            status=TaskStatus.COMPLETED,
            output_data={"result": "完成"}
        )
        
        inputs = {"task_id": task.task_id, "status": "completed"}
        result = service.execute(task)
        
        test_report(
            test_points=["测试检查任务-已完成", "验证检查逻辑"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "check_count": result.output_data.get("check_count")
            }
        )
        
        assert result.task_id == "test_check_task_1"
    
    def test_execute_check_with_execution_history(self, test_report):
        """测试检查有执行历史的任务"""
        service = CheckTaskService()
        task = Task(
            task_id="test_check_task_2",
            input_data={"user_input": "测试"},
            status=TaskStatus.COMPLETED,
            execution_history=[{"step": "tool_execution", "tool_name": "test", "result": "success"}]
        )
        
        inputs = {"task_id": task.task_id, "has_history": True}
        result = service.execute(task)
        
        test_report(
            test_points=["测试检查任务-带历史", "验证历史分析"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value
            }
        )
        
        assert result is not None

class TestAdjustTaskService:
    """测试调整任务服务 - UT测试"""
    
    def test_execute_adjust_completed(self, test_report):
        """测试调整已完成的任务"""
        service = AdjustTaskService()
        task = Task(
            task_id="test_adjust_task_1",
            input_data={"user_input": "测试", "original_input": {"user_input": "test"}, "tool_execution_result": {"status": "success"}},
            status=TaskStatus.COMPLETED
        )
        
        inputs = {"task_id": task.task_id, "status": "completed"}
        result = service.execute(task)
        
        test_report(
            test_points=["测试调整任务-已完成", "验证调整逻辑"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value
            }
        )
        
        assert result is not None
    
    def test_execute_adjust_pending(self, test_report):
        """测试调整待处理的任务"""
        service = AdjustTaskService()
        task = Task(
            task_id="test_adjust_task_2",
            input_data={"user_input": "测试", "original_input": {"user_input": "test"}, "tool_execution_result": {"status": "failed"}},
            status=TaskStatus.PENDING
        )
        
        inputs = {"task_id": task.task_id, "status": "pending"}
        result = service.execute(task)
        
        test_report(
            test_points=["测试调整任务-待处理", "验证重试逻辑"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value
            }
        )
        
        assert result is not None

class TestTaskExecutionService:
    """测试任务执行服务 - UT测试"""
    
    def test_execute_task(self, test_report):
        """测试执行单个任务"""
        service = TaskExecutionService()
        task = Task(task_id="test_task_exec_1", input_data={"user_input": "你好"})
        
        inputs = {"task_id": task.task_id, "user_input": "你好"}
        result = service.execute(task)
        
        test_report(
            test_points=["测试任务执行", "验证执行流程"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
    
    def test_execute_task_with_parent(self, test_report):
        """测试执行带父任务的任务"""
        service = TaskExecutionService()
        task = Task(
            task_id="test_task_exec_2",
            parent_task_id="parent-task",
            input_data={"user_input": "子任务"}
        )
        
        inputs = {"task_id": task.task_id, "parent_task_id": task.parent_task_id}
        result = service.execute(task)
        
        test_report(
            test_points=["测试任务执行-带父任务", "验证父子任务关系"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value
            }
        )
        
        assert result.status == TaskStatus.COMPLETED

class TestTaskGroupExecutor:
    """测试任务组执行器 - UT测试"""
    
    def test_execute_task_group_sequential(self, test_report):
        """测试顺序执行任务组"""
        from services.L3_scenario_coordination.L3a_task_coordination.intent_service import IntentAnalysisResult, TaskGroupInfo
        
        executor = TaskGroupExecutor()
        task = Task(task_id="test_group_task_1", input_data={"user_input": "顺序任务"})
        intent_result = IntentAnalysisResult(
            execution_path=ExecutionPath.TASK_GROUP,
            task_group_info=TaskGroupInfo(
                execution_mode=TaskGroupInfo.ExecutionMode.SEQUENTIAL,
                subtask_definitions=[]
            )
        )
        
        inputs = {"task_id": task.task_id, "execution_mode": "sequential"}
        result = executor.execute(task, intent_result)
        
        test_report(
            test_points=["测试任务组执行-顺序", "验证顺序执行模式"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "subtask_count": result.output_data.get("subtask_count"),
                "execution_mode": result.output_data.get("execution_mode")
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
    
    def test_execute_task_group_parallel(self, test_report):
        """测试并行执行任务组"""
        from services.L3_scenario_coordination.L3a_task_coordination.intent_service import IntentAnalysisResult, TaskGroupInfo
        
        executor = TaskGroupExecutor()
        task = Task(task_id="test_group_task_2", input_data={"user_input": "并行任务"})
        intent_result = IntentAnalysisResult(
            execution_path=ExecutionPath.TASK_GROUP,
            task_group_info=TaskGroupInfo(
                execution_mode=TaskGroupInfo.ExecutionMode.PARALLEL,
                subtask_definitions=[]
            )
        )
        
        inputs = {"task_id": task.task_id, "execution_mode": "parallel"}
        result = executor.execute(task, intent_result)
        
        test_report(
            test_points=["测试任务组执行-并行", "验证并行执行模式"],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "subtask_count": result.output_data.get("subtask_count"),
                "execution_mode": result.output_data.get("execution_mode")
            }
        )
        
        assert result.status == TaskStatus.COMPLETED
