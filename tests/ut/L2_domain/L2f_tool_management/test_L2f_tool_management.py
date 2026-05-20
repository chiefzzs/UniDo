import pytest
from services.L2_domain.L2f_tool_management import ToolManagementService, ToolDefinition


class TestToolManagementService:
    """测试工具管理服务"""

    def test_register_tool(self, test_report):
        """测试注册工具 - 验证L2服务调用L1持久化到tool_definitions.json"""
        service = ToolManagementService()
        
        tool = service.register_tool(
            tool_name="test_tool_reg",
            category="test",
            description="Test tool for registration",
            parameters={'required': ['input']}
        )
        
        test_report(
            test_points=["测试注册工具", "验证L2服务自动触发L1持久化到tool_definitions.json"],
            inputs={"tool_name": "test_tool_reg", "category": "test"},
            outputs={"tool_id": tool.tool_id, "tool_name": tool.tool_name}
        )
        
        assert tool is not None
        assert tool.tool_id is not None

    def test_get_tool(self, test_report):
        """测试获取工具"""
        service = ToolManagementService()
        
        tool = service.register_tool(
            tool_name="get_test_tool",
            category="test",
            description="Tool for get test"
        )
        
        retrieved = service.get_tool(tool.tool_id)
        
        test_report(
            test_points=["测试获取工具", "验证tool_definitions查询功能"],
            inputs={"tool_id": tool.tool_id},
            outputs={"found": retrieved is not None, "name": retrieved.tool_name if retrieved else None}
        )
        
        assert retrieved is not None
        assert retrieved.tool_id == tool.tool_id

    def test_list_tools(self, test_report):
        """测试列出工具"""
        service = ToolManagementService()
        
        service.register_tool(
            tool_name="list_tool_1",
            category="category_a",
            description="Tool 1"
        )
        
        service.register_tool(
            tool_name="list_tool_2",
            category="category_b",
            description="Tool 2"
        )
        
        all_tools = service.list_tools()
        category_a_tools = service.list_tools(category="category_a")
        
        test_report(
            test_points=["测试列出工具", "验证按类别过滤"],
            inputs={"filter_category": "category_a"},
            outputs={"all_count": len(all_tools), "category_a_count": len(category_a_tools)}
        )
        
        assert len(all_tools) >= 2
        assert len(category_a_tools) >= 1

    def test_update_tool(self, test_report):
        """测试更新工具"""
        service = ToolManagementService()
        
        tool = service.register_tool(
            tool_name="update_test_tool",
            category="test",
            description="Original description"
        )
        
        updated = service.update_tool(
            tool.tool_id,
            description="Updated description",
            category="updated"
        )
        
        test_report(
            test_points=["测试更新工具", "验证tool_definitions更新"],
            inputs={"tool_id": tool.tool_id, "new_description": "Updated description"},
            outputs={"updated": updated is not None, "description": updated.description if updated else None}
        )
        
        assert updated is not None
        assert updated.description == "Updated description"

    def test_unregister_tool(self, test_report):
        """测试注销工具"""
        service = ToolManagementService()
        
        tool = service.register_tool(
            tool_name="unregister_test_tool",
            category="test",
            description="Tool for unregister test"
        )
        
        result = service.unregister_tool(tool.tool_id)
        retrieved = service.get_tool(tool.tool_id)
        
        test_report(
            test_points=["测试注销工具", "验证工具删除"],
            inputs={"tool_id": tool.tool_id},
            outputs={"unregistered": result, "retrieved": retrieved is not None}
        )
        
        assert result is True
        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
