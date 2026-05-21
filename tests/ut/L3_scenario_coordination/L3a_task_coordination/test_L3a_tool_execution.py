"""
L3a Tool Execution Service - UT测试

单元测试：测试工具执行服务，直接使用L2/L1层真实服务，不打桩不mock
验证工具调用结果正确存储到 src/data/test 目录
"""

import os
import pytest
from pathlib import Path

# 设置测试环境
os.environ['STORAGE_ENV'] = 'test'

from services.L3_scenario_coordination.L3a_task_coordination.tool_task_executor import ToolTaskExecutor
from services.L3_scenario_coordination.schemas import Task, TaskStatus
from services.L2_domain.L2c_tool_execution import get_tool_executor, ToolExecutor
from services.L1_infrastructure.L1b_persistence.persistence_service import get_persistence_service


class TestToolExecutionService:
    """测试工具执行服务 - UT测试"""
    
    def test_execute_tool_run_command(self, test_report):
        """测试执行RunCommand工具 - 真实执行命令"""
        # 使用真实的工具执行器
        executor = get_tool_executor()
        
        # 创建测试目录 - 使用workspace目录
        test_dir = "d:\\learnning\\260521\\workspace\\tool_test_dir"
        
        inputs = {
            "tool_name": "RunCommand",
            "command": f"mkdir {test_dir}"
        }
        
        result = executor.execute_tool(
            tool_name=inputs["tool_name"],
            dialog_id="test-tool-exec-1",
            task_id="test-tool-exec-1",
            params={"command": inputs["command"], "workspace": "d:\\learnning\\260521\\workspace"}
        )
        
        # 验证工具调用结果
        assert result.success, f"工具执行失败: {result.error}"
        assert result.result is not None
        
        # 验证目录确实被创建
        assert os.path.exists(test_dir), f"目录未被创建: {test_dir}"
        
        # 收集工具调用记录
        persistence = get_persistence_service()
        tool_calls = persistence.list('tool_calls')
        
        test_report(
            test_points=[
                "测试工具执行-RunCommand",
                "验证真实命令执行",
                "验证工具调用结果正确",
                "验证工具调用记录持久化"
            ],
            inputs=inputs,
            outputs={
                "success": result.success,
                "result": result.result,
                "call_id": result.call_id,
                "tool_call_count": len(tool_calls)
            },
            tool_calls=tool_calls
        )
    
    def test_execute_tool_write_read_file(self, test_report):
        """测试执行Write和Read工具 - 真实文件操作"""
        executor = get_tool_executor()
        
        # 使用workspace目录
        test_file = "d:\\learnning\\260521\\workspace\\tool_test_file.txt"
        test_content = "测试工具执行内容"
        
        # 第一步：写入文件
        write_result = executor.execute_tool(
            tool_name="Write",
            dialog_id="test-tool-exec-2",
            task_id="test-tool-exec-2",
            params={"file_path": test_file, "content": test_content, "workspace": "d:\\learnning\\260521\\workspace"}
        )
        
        assert write_result.success, f"写入文件失败: {write_result.error}"
        
        # 第二步：读取文件
        read_result = executor.execute_tool(
            tool_name="Read",
            dialog_id="test-tool-exec-2",
            task_id="test-tool-exec-2",
            params={"file_path": test_file, "workspace": "d:\\learnning\\260521\\workspace"}
        )
        
        # 验证读取结果
        assert read_result.success, f"读取文件失败: {read_result.error}"
        # 解析字符串结果为字典
        import ast
        read_result_dict = ast.literal_eval(read_result.result)
        assert 'content' in read_result_dict, "Read结果缺少content字段"
        assert read_result_dict['content'] == test_content, f"内容不匹配: {read_result_dict['content']}"
        
        # 验证文件确实被创建
        assert os.path.exists(test_file), f"文件未被创建: {test_file}"
        
        # 收集工具调用记录
        persistence = get_persistence_service()
        tool_calls = persistence.list('tool_calls')
        
        test_report(
            test_points=[
                "测试工具执行-Write/Read",
                "验证文件写入",
                "验证文件读取",
                "验证读写内容一致性"
            ],
            inputs={
                "write_file": test_file,
                "write_content": test_content
            },
            outputs={
                "write_success": write_result.success,
                "read_success": read_result.success,
                "read_content": read_result.result,
                "tool_call_count": len(tool_calls)
            },
            tool_calls=tool_calls
        )
    
    def test_execute_tool_ls(self, test_report):
        """测试执行LS工具 - 真实目录列表"""
        executor = get_tool_executor()
        
        # 使用workspace目录
        test_path = "d:\\learnning\\260521\\workspace"
        
        result = executor.execute_tool(
            tool_name="LS",
            dialog_id="test-tool-exec-3",
            task_id="test-tool-exec-3",
            params={"path": test_path, "workspace": "d:\\learnning\\260521\\workspace"}
        )
        
        # 验证工具调用结果
        assert result.success, f"LS工具执行失败: {result.error}"
        assert result.result is not None
        # 解析字符串结果为字典
        import ast
        result_dict = ast.literal_eval(result.result)
        assert isinstance(result_dict, dict), "LS结果应该是字典"
        assert 'entries' in result_dict, "LS结果缺少entries字段"
        
        # 收集工具调用记录
        persistence = get_persistence_service()
        tool_calls = persistence.list('tool_calls')
        
        test_report(
            test_points=[
                "测试工具执行-LS",
                "验证目录列表功能",
                "验证返回结果格式正确"
            ],
            inputs={"path": test_path},
            outputs={
                "success": result.success,
                "result_type": type(result.result).__name__,
                "item_count": len(result.result) if isinstance(result.result, list) else 0,
                "tool_call_count": len(tool_calls)
            },
            tool_calls=tool_calls
        )
    
    def test_tool_task_executor_integration(self, test_report):
        """测试工具任务执行器集成 - 完整流程"""
        from services.L3_scenario_coordination.L3a_task_coordination.intent_service import IntentService, IntentAnalysisResult, SingleToolInfo, ExecutionPath
        
        # 创建工具任务执行器
        tool_task_executor = ToolTaskExecutor()
        
        # 创建测试任务
        task = Task(
            task_id="test-tool-task-1",
            input_data={"user_input": "列出测试目录"}
        )
        
        # 创建意图分析结果（模拟单工具调用）
        intent_result = IntentAnalysisResult(
            execution_path=ExecutionPath.SINGLE_TOOL,
            single_tool_info=SingleToolInfo(
                tool_id="T04",
                tool_name="LS",
                parameters={"path": "d:\\learnning\\260521\\workspace"}
            )
        )
        
        inputs = {
            "task_id": task.task_id,
            "user_input": "列出测试目录",
            "tool_name": "LS"
        }
        
        # 执行任务
        result = tool_task_executor.execute(task, intent_result)
        
        # 验证任务状态
        assert result.status == TaskStatus.COMPLETED, f"任务执行失败: {result.error_message}"
        assert "result" in result.output_data, "缺少执行结果"
        assert len(result.execution_history) > 0, "缺少执行历史"
        # 验证执行历史包含工具执行记录
        tool_execution_steps = [h for h in result.execution_history if h.get('step') == 'tool_execution']
        assert len(tool_execution_steps) > 0, "执行历史中缺少工具执行记录"
        
        # 收集工具调用记录
        persistence = get_persistence_service()
        tool_calls = persistence.list('tool_calls')
        messages = persistence.list('messages')
        
        test_report(
            test_points=[
                "测试工具任务执行器集成",
                "验证完整工具调用流程",
                "验证任务状态转换",
                "验证执行历史记录"
            ],
            inputs=inputs,
            outputs={
                "task_id": result.task_id,
                "status": result.status.value,
                "execution_history_length": len(result.execution_history),
                "tool_call_count": len(tool_calls),
                "message_count": len(messages)
            },
            tool_calls=tool_calls,
            persistent_data={
                'tool_calls': tool_calls,
                'messages': messages
            }
        )
    
    def test_tool_executor_result_structure(self, test_report):
        """测试工具执行结果结构 - 验证ToolResult属性"""
        executor = get_tool_executor()
        
        # 使用workspace目录
        result = executor.execute_tool(
            tool_name="LS",
            dialog_id="test-tool-exec-4",
            task_id="test-tool-exec-4",
            params={"path": "d:\\learnning\\260521\\workspace", "workspace": "d:\\learnning\\260521\\workspace"}
        )
        
        # 验证ToolResult结构（修复之前的bug: result.content -> result.result）
        assert hasattr(result, 'success'), "ToolResult缺少success属性"
        assert hasattr(result, 'result'), "ToolResult缺少result属性"
        assert hasattr(result, 'error'), "ToolResult缺少error属性"
        assert hasattr(result, 'call_id'), "ToolResult缺少call_id属性"
        assert hasattr(result, 'to_dict'), "ToolResult缺少to_dict方法"
        
        # 验证to_dict返回正确的结构
        result_dict = result.to_dict()
        assert 'success' in result_dict
        assert 'result' in result_dict
        assert 'error' in result_dict
        assert 'call_id' in result_dict
        
        test_report(
            test_points=[
                "测试ToolResult结构",
                "验证属性存在性",
                "验证to_dict方法返回正确结构"
            ],
            inputs={"tool_name": "LS"},
            outputs={
                "success": result.success,
                "has_success_attr": hasattr(result, 'success'),
                "has_result_attr": hasattr(result, 'result'),
                "has_error_attr": hasattr(result, 'error'),
                "has_call_id_attr": hasattr(result, 'call_id'),
                "to_dict_keys": list(result_dict.keys())
            }
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])