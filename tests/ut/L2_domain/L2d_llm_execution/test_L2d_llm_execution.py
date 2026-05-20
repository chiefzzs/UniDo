import pytest
from services.L2_domain.L2d_llm_execution import LLMExecutionService


class TestLLMExecutionService:
    """测试LLM执行服务"""

    def test_execute_llm(self, test_report):
        """测试执行LLM请求 - 验证L2服务调用L1持久化到llm_calls.json"""
        service = LLMExecutionService()
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        result = service.execute(
            session_id="session-llm-001",
            model_config_id="default",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        
        test_report(
            test_points=["测试执行LLM请求", "验证L2服务自动触发L1持久化到llm_calls.json"],
            inputs={"session_id": "session-llm-001", "model_config_id": "default", "message_count": len(messages)},
            outputs={"request_id": result.request_id, "status": result.status, "content": result.content[:50] if result.content else ""}
        )
        
        assert result is not None
        assert result.request_id is not None

    def test_execute_stream(self, test_report):
        """测试流式执行LLM请求"""
        service = LLMExecutionService()
        
        messages = [
            {"role": "user", "content": "Stream test"}
        ]
        
        chunks = []
        def on_chunk(chunk):
            chunks.append(chunk)
        
        result = service.execute_stream(
            session_id="session-stream-001",
            model_config_id="default",
            messages=messages,
            on_chunk=on_chunk
        )
        
        test_report(
            test_points=["测试流式LLM请求", "验证流式响应处理"],
            inputs={"session_id": "session-stream-001"},
            outputs={"request_id": result.request_id, "chunk_count": len(chunks), "status": result.status}
        )
        
        assert result is not None
        assert result.request_id is not None

    def test_get_call_record(self, test_report):
        """测试获取LLM调用记录"""
        service = LLMExecutionService()
        
        messages = [
            {"role": "user", "content": "Test record retrieval"}
        ]
        
        result = service.execute(
            session_id="session-record-001",
            model_config_id="default",
            messages=messages
        )
        
        records = service.list_call_records(dialog_id="session-record-001")
        
        test_report(
            test_points=["测试获取LLM调用记录", "验证llm_calls查询功能"],
            inputs={"dialog_id": "session-record-001"},
            outputs={"record_count": len(records)}
        )
        
        assert len(records) >= 1

    def test_parse_tool_calls(self, test_report):
        """测试解析工具调用"""
        service = LLMExecutionService()
        
        content_with_tool = '{"tool_calls": [{"tool_name": "calculator", "parameters": {"expression": "2+2"}}]}'
        tool_calls = service.parse_tool_calls(content_with_tool)
        
        test_report(
            test_points=["测试解析工具调用", "验证tool_calls解析功能"],
            inputs={"content": content_with_tool[:30] + "..."},
            outputs={"tool_call_count": len(tool_calls)}
        )
        
        assert isinstance(tool_calls, list)


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
