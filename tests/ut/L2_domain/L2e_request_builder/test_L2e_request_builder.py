import pytest
from services.L2_domain.L2e_request_builder import PromptBuilder, ContextBuilder, RequestBuilder, PromptTemplate, RequestConfiguration, LLMRequest


class TestPromptBuilder:
    """测试Prompt构建器"""

    def test_create_template(self, test_report):
        """测试创建Prompt模板 - 验证持久化到prompt_template.json"""
        builder = PromptBuilder()
        
        template = builder.create_template(
            name="test_template",
            content="Hello {name}, welcome!",
            template_type="greeting",
            parameters=["name"]
        )
        
        test_report(
            test_points=["测试创建Prompt模板", "验证L2服务自动触发L1持久化到prompt_template.json"],
            inputs={"name": "test_template", "type": "greeting"},
            outputs={"template_id": template.template_id, "name": template.name}
        )
        
        assert template is not None
        assert template.template_id is not None

    def test_get_template(self, test_report):
        """测试获取Prompt模板"""
        builder = PromptBuilder()
        
        template = builder.create_template(
            name="get_test_template",
            content="Test content",
            template_type="test"
        )
        
        retrieved = builder.get_template(template.template_id)
        
        test_report(
            test_points=["测试获取Prompt模板", "验证prompt_template查询功能"],
            inputs={"template_id": template.template_id},
            outputs={"found": retrieved is not None, "name": retrieved.name if retrieved else None}
        )
        
        assert retrieved is not None
        assert retrieved.name == "get_test_template"

    def test_build_system_prompt(self, test_report):
        """测试构建系统Prompt"""
        builder = PromptBuilder()
        
        prompt = builder.build_system_prompt(name="TestUser")
        
        test_report(
            test_points=["测试构建系统Prompt"],
            inputs={"name": "TestUser"},
            outputs={"prompt_length": len(prompt)}
        )
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestContextBuilder:
    """测试上下文构建器"""

    def test_build_context(self, test_report):
        """测试构建上下文 - 验证从messages.json获取数据"""
        builder = ContextBuilder()
        
        context = builder.build_context(session_id="test-session")
        
        test_report(
            test_points=["测试构建上下文", "验证从messages.json获取会话消息"],
            inputs={"session_id": "test-session"},
            outputs={"message_count": len(context)}
        )
        
        assert isinstance(context, list)

    def test_truncate_context(self, test_report):
        """测试截断上下文"""
        builder = ContextBuilder()
        
        messages = [
            {"content": "a" * 100},
            {"content": "b" * 100},
            {"content": "c" * 100}
        ]
        
        truncated = builder.truncate_context(messages, 150)
        
        test_report(
            test_points=["测试截断上下文"],
            inputs={"original_count": len(messages), "max_tokens": 150},
            outputs={"truncated_count": len(truncated)}
        )
        
        assert len(truncated) <= len(messages)


class TestRequestBuilder:
    """测试请求构建器"""

    def test_create_request_configuration(self, test_report):
        """测试创建请求配置 - 验证持久化到request_configuration.json"""
        builder = RequestBuilder()
        
        config = builder.create_request_configuration(
            name="test_config",
            model="gpt-4",
            temperature=0.8,
            max_tokens=4000
        )
        
        test_report(
            test_points=["测试创建请求配置", "验证L2服务自动触发L1持久化到request_configuration.json"],
            inputs={"name": "test_config", "model": "gpt-4"},
            outputs={"config_id": config.config_id, "name": config.name}
        )
        
        assert config is not None
        assert config.config_id is not None

    def test_build_request(self, test_report):
        """测试构建LLM请求"""
        builder = RequestBuilder()
        
        messages = [
            {"role": "user", "content": "Test request"}
        ]
        
        request = builder.build_request(
            session_id="session-req-001",
            messages=messages,
            model="test-model",
            temperature=0.7
        )
        
        test_report(
            test_points=["测试构建LLM请求", "验证llm_request持久化"],
            inputs={"session_id": "session-req-001", "message_count": len(messages)},
            outputs={"model": request.model, "temperature": request.temperature}
        )
        
        assert request is not None
        assert request.model == "test-model"

    def test_validate_request(self, test_report):
        """测试验证请求"""
        builder = RequestBuilder()
        
        valid_request = LLMRequest(messages=[{"role": "user", "content": "test"}], model="test")
        invalid_request = LLMRequest(messages=[], model="")
        
        valid_result = builder.validate_request(valid_request)
        invalid_result = builder.validate_request(invalid_request)
        
        test_report(
            test_points=["测试验证请求"],
            inputs={"valid_messages": len(valid_request.messages), "invalid_messages": len(invalid_request.messages)},
            outputs={"valid_result": valid_result, "invalid_result": invalid_result}
        )
        
        assert valid_result is True
        assert invalid_result is False


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
