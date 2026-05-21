"""
测试工具 - 用于单元测试的工具实现
"""
from src.tools.implement.base_tool import BaseTool
from typing import Dict, Any


class TestTool(BaseTool):
    """基础测试工具"""
    
    def __init__(self):
        super().__init__()
        self.tool_id = "tool-test"
        self.name = "test_tool"
        self.category = "test"
        self.description = "基础测试工具"
        self.parameters = {"required": ["input"]}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行测试工具"""
        return {
            "success": True,
            "result": f"Executed with input: {params.get('input', '')}"
        }


class StatusTestTool(BaseTool):
    """状态测试工具"""
    
    def __init__(self):
        super().__init__()
        self.tool_id = "tool-status-test"
        self.name = "status_test_tool"
        self.category = "test"
        self.description = "状态测试工具"
        self.parameters = {"required": ["input"]}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行状态测试工具"""
        return {
            "success": True,
            "result": f"Status test executed: {params.get('input', '')}"
        }


class AsyncTestTool(BaseTool):
    """异步测试工具"""
    
    def __init__(self):
        super().__init__()
        self.tool_id = "tool-async-test"
        self.name = "async_tool"
        self.category = "test"
        self.description = "异步测试工具"
        self.parameters = {"required": ["input"]}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行异步测试工具"""
        import time
        time.sleep(2)  # 模拟长时间运行
        return {
            "success": True,
            "result": f"Async executed: {params.get('input', '')}"
        }


class FailingTool(BaseTool):
    """失败测试工具"""
    
    def __init__(self):
        super().__init__()
        self.tool_id = "tool-failing"
        self.name = "failing_tool"
        self.category = "test"
        self.description = "失败测试工具"
        self.parameters = {"required": ["input"]}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行失败测试工具 - 故意抛出异常"""
        raise Exception("Intentional failure")


class ListTestTool(BaseTool):
    """列表测试工具"""
    
    def __init__(self):
        super().__init__()
        self.tool_id = "tool-list-test"
        self.name = "list_test_tool"
        self.category = "test"
        self.description = "列表测试工具"
        self.parameters = {"required": ["input"]}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行列表测试工具"""
        return {
            "success": True,
            "result": f"List test executed: {params.get('input', '')}"
        }


class TestToolWithRequired(BaseTool):
    """带必填参数的测试工具"""
    
    def __init__(self):
        super().__init__()
        self.tool_id = "tool-test-required"
        self.name = "test_tool_with_required"
        self.category = "test"
        self.description = "带必填参数的测试工具"
        self.parameters = {"required": ["input", "required_param"]}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行带必填参数的测试工具"""
        return {
            "success": True,
            "result": f"Executed with input: {params.get('input', '')}, required_param: {params.get('required_param', '')}"
        }
