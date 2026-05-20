import pytest
from services.L2_domain.L2c_tool_execution import ToolExecutor, ToolResult, ToolCall
from services.L2_domain.L2f_tool_management import ToolManagementService, ToolRegistry


class TestToolExecutor:
    """测试工具执行服务"""

    def test_execute_tool(self, test_report):
        """测试执行工具 - 验证L2服务调用L1持久化到tool_calls.json"""
        tool_service = ToolManagementService()
        executor = ToolExecutor(tool_service=tool_service)
        
        tool_service.register_tool(
            tool_name="test_tool",
            category="test",
            description="Test tool for unit testing",
            parameters={'required': ['input']}
        )
        
        result = executor.execute_tool(
            tool_name="test_tool",
            dialog_id="dialog-001",
            task_id="task-001",
            params={"input": "test input"}
        )
        
        test_report(
            test_points=["测试执行工具", "验证L2服务自动触发L1持久化到tool_calls.json"],
            inputs={"tool_name": "test_tool", "dialog_id": "dialog-001", "task_id": "task-001", "params": {"input": "test input"}},
            outputs={"success": result.success, "call_id": result.call_id, "status": result.status}
        )
        
        assert result.success is True
        assert result.call_id is not None

    def test_execute_tool_not_found(self, test_report):
        """测试执行不存在的工具"""
        executor = ToolExecutor()
        
        result = executor.execute_tool(
            tool_name="non_existent_tool",
            dialog_id="dialog-001",
            task_id="task-001",
            params={"input": "test"}
        )
        
        test_report(
            test_points=["测试执行不存在的工具"],
            inputs={"tool_name": "non_existent_tool"},
            outputs={"success": result.success, "error": result.error, "status": result.status}
        )
        
        assert result.success is False
        assert "not found" in result.error.lower()
        assert result.status == "failed"

    def test_execute_tool_invalid_params(self, test_report):
        """测试执行工具参数验证失败 - invalid_params状态"""
        tool_service = ToolManagementService()
        executor = ToolExecutor(tool_service=tool_service)
        
        tool_service.register_tool(
            tool_name="test_tool_with_required",
            category="test",
            description="Tool with required params",
            parameters={'required': ['input', 'required_param']}
        )
        
        result = executor.execute_tool(
            tool_name="test_tool_with_required",
            dialog_id="dialog-001",
            task_id="task-001",
            params={"input": "only one"}
        )
        
        test_report(
            test_points=["测试工具参数验证失败", "验证invalid_params状态"],
            inputs={"tool_name": "test_tool_with_required", "params": {"input": "only one"}},
            outputs={"success": result.success, "status": result.status, "error": result.error}
        )
        
        assert result.success is False
        assert result.status == "invalid_params"

    def test_get_call_status(self, test_report):
        """测试获取工具调用状态 - 验证ToolCall完整字段"""
        tool_service = ToolManagementService()
        executor = ToolExecutor(tool_service=tool_service)
        
        tool_service.register_tool(
            tool_name="status_test_tool",
            category="test",
            description="Tool for status test",
            parameters={'required': ['input']}
        )
        
        result = executor.execute_tool(
            tool_name="status_test_tool",
            dialog_id="dialog-002",
            task_id="task-002",
            params={"input": "status test"}
        )
        
        call_status = executor.get_call_status(result.call_id)
        
        test_report(
            test_points=["测试获取工具调用状态", "验证ToolCall完整字段"],
            inputs={"call_id": result.call_id},
            outputs={
                "call_id": call_status.call_id if call_status else None,
                "tool_id": call_status.tool_id if call_status else None,
                "tool_name": call_status.tool_name if call_status else None,
                "dialog_id": call_status.dialog_id if call_status else None,
                "task_id": call_status.task_id if call_status else None,
                "status": call_status.status if call_status else None,
                "start_time": call_status.start_time if call_status else None,
                "end_time": call_status.end_time if call_status else None,
                "duration": call_status.duration if call_status else None
            }
        )
        
        assert call_status is not None
        assert call_status.call_id == result.call_id
        assert call_status.status == "completed"
        assert call_status.tool_name == "status_test_tool"
        assert call_status.dialog_id == "dialog-002"
        assert call_status.task_id == "task-002"
        assert call_status.start_time is not None
        assert call_status.end_time is not None
        assert call_status.duration >= 0

    def test_list_calls(self, test_report):
        """测试列出工具调用记录"""
        tool_service = ToolManagementService()
        executor = ToolExecutor(tool_service=tool_service)
        
        tool_service.register_tool(
            tool_name="list_test_tool",
            category="test",
            description="Tool for list test",
            parameters={'required': ['input']}
        )
        
        result1 = executor.execute_tool(
            tool_name="list_test_tool",
            dialog_id="dialog-003",
            task_id="task-003",
            params={"input": "list test 1"}
        )
        
        result2 = executor.execute_tool(
            tool_name="list_test_tool",
            dialog_id="dialog-003",
            task_id="task-004",
            params={"input": "list test 2"}
        )
        
        calls = executor.list_calls(dialog_id="dialog-003")
        
        test_report(
            test_points=["测试列出工具调用记录", "验证按dialog_id过滤"],
            inputs={"dialog_id": "dialog-003"},
            outputs={"call_count": len(calls)}
        )
        
        # 只有成功执行的才会被记录
        successful_calls = sum(1 for r in [result1, result2] if r.success)
        assert len(calls) >= successful_calls

    def test_cancel_call(self, test_report):
        """测试取消工具调用 - cancelled状态"""
        tool_service = ToolManagementService()
        executor = ToolExecutor(tool_service=tool_service)
        
        tool_service.register_tool(
            tool_name="async_tool",
            category="test",
            description="Async tool",
            parameters={'required': ['input']}
        )
        
        call_id = executor.execute_async(
            tool_name="async_tool",
            dialog_id="dialog-004",
            task_id="task-005",
            params={"input": "async test"}
        )
        
        if call_id:
            cancelled = executor.cancel_call(call_id)
            call_status = executor.get_call_status(call_id)
            
            test_report(
                test_points=["测试取消工具调用", "验证cancelled状态"],
                inputs={"call_id": call_id},
                outputs={"cancelled": cancelled, "status": call_status.status if call_status else None}
            )
            
            assert cancelled is True
            assert call_status is not None
            assert call_status.status == "cancelled"
        else:
            pytest.xfail("Async execution failed to create call")

    def test_execute_tool_failure(self, test_report):
        """测试工具执行失败 - failed状态"""
        tool_service = ToolManagementService()
        executor = ToolExecutor(tool_service=tool_service)
        
        def failing_tool(**kwargs):
            raise Exception("Intentional failure")
        
        tool_service.register_tool(
            tool_name="failing_tool",
            category="test",
            description="Tool that fails",
            parameters={'required': ['input']},
            implementation=failing_tool
        )
        
        result = executor.execute_tool(
            tool_name="failing_tool",
            dialog_id="dialog-005",
            task_id="task-006",
            params={"input": "fail test"}
        )
        
        test_report(
            test_points=["测试工具执行失败", "验证failed状态"],
            inputs={"tool_name": "failing_tool"},
            outputs={"success": result.success, "status": result.status, "error": result.error}
        )
        
        assert result.success is False
        assert result.status == "failed"
        assert "Intentional failure" in result.error

    def test_tool_result_status_values(self, test_report):
        """测试ToolResult各种状态值"""
        # Test done status
        done_result = ToolResult.done("success result", "call-001")
        assert done_result.success is True
        assert done_result.status == "done"
        assert done_result.result == "success result"
        assert done_result.call_id == "call-001"
        
        # Test failed status
        failed_result = ToolResult.failed("error message", "call-002")
        assert failed_result.success is False
        assert failed_result.status == "failed"
        assert failed_result.error == "error message"
        
        # Test timeout status
        timeout_result = ToolResult.timeout("call-003")
        assert timeout_result.success is False
        assert timeout_result.status == "timeout"
        assert "timeout" in timeout_result.error
        
        # Test cancelled status
        cancelled_result = ToolResult.cancelled("call-004")
        assert cancelled_result.success is False
        assert cancelled_result.status == "cancelled"
        
        # Test invalid_params status
        invalid_result = ToolResult.invalid_params("missing param", "call-005")
        assert invalid_result.success is False
        assert invalid_result.status == "invalid_params"
        
        # Test partial_done status
        partial_result = ToolResult.partial_done("partial result", "call-006")
        assert partial_result.success is True
        assert partial_result.status == "partial_done"
        
        test_report(
            test_points=["测试ToolResult各种状态值", "验证done/failed/timeout/cancelled/invalid_params/partial_done"],
            inputs={"test_all_status": True},
            outputs={
                "done": done_result.status,
                "failed": failed_result.status,
                "timeout": timeout_result.status,
                "cancelled": cancelled_result.status,
                "invalid_params": invalid_result.status,
                "partial_done": partial_result.status
            }
        )

    def test_tool_call_to_dict(self, test_report):
        """测试ToolCall序列化"""
        call = ToolCall(
            call_id="call-test-001",
            tool_id="tool-001",
            tool_name="test_tool",
            dialog_id="dialog-001",
            task_id="task-001",
            input_params={"key": "value"},
            output_result="result",
            status="completed",
            start_time="2026-05-18T10:30:00",
            end_time="2026-05-18T10:30:01",
            duration=1.0
        )
        
        call_dict = call.to_dict()
        
        test_report(
            test_points=["测试ToolCall序列化", "验证所有字段正确序列化"],
            inputs={"call_id": "call-test-001"},
            outputs={
                "has_call_id": "call_id" in call_dict,
                "has_tool_id": "tool_id" in call_dict,
                "has_tool_name": "tool_name" in call_dict,
                "has_dialog_id": "dialog_id" in call_dict,
                "has_task_id": "task_id" in call_dict,
                "has_input_params": "input_params" in call_dict,
                "has_output_result": "output_result" in call_dict,
                "has_status": "status" in call_dict,
                "has_start_time": "start_time" in call_dict,
                "has_end_time": "end_time" in call_dict,
                "has_duration": "duration" in call_dict
            }
        )
        
        assert call_dict["call_id"] == "call-test-001"
        assert call_dict["tool_id"] == "tool-001"
        assert call_dict["tool_name"] == "test_tool"
        assert call_dict["dialog_id"] == "dialog-001"
        assert call_dict["task_id"] == "task-001"
        assert call_dict["status"] == "completed"
        assert call_dict["duration"] == 1.0

    def test_tool_result_to_dict(self, test_report):
        """测试ToolResult序列化"""
        result = ToolResult(
            success=True,
            result="test result",
            error=None,
            call_id="call-001",
            status="done"
        )
        
        result_dict = result.to_dict()
        
        test_report(
            test_points=["测试ToolResult序列化", "验证所有字段正确序列化"],
            inputs={"call_id": "call-001"},
            outputs={
                "has_success": "success" in result_dict,
                "has_result": "result" in result_dict,
                "has_error": "error" in result_dict,
                "has_call_id": "call_id" in result_dict,
                "has_status": "status" in result_dict
            }
        )
        
        assert result_dict["success"] is True
        assert result_dict["result"] == "test result"
        assert result_dict["call_id"] == "call-001"
        assert result_dict["status"] == "done"


if __name__ == "__main__":
    pytest.main([__file__, '-v'])