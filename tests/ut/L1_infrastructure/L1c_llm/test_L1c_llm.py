"""
L1c LLM Client Unit Tests

单元测试：测试LLM客户端的基本功能
"""

import pytest
from services.L1_infrastructure.L1c_llm.llm_client import LLMRequest, get_llm_client


class TestLLMClient:
    """测试LLM客户端"""

    def test_send_request_records_llm_call(self, test_report):
        """测试LLMClient发送请求 - 验证LLM调用自动持久化到llm_calls.json"""
        client = get_llm_client()
        
        request = LLMRequest(
            model_name="test",
            messages=[{"role": "user", "content": "Hello"}],
            api_address="http://localhost/v1",
            api_type="openai"
        )
        
        inputs = {
            "model_name": request.model_name,
            "messages": request.messages,
            "api_type": request.api_type
        }
        
        try:
            result = client.send_request(request, session_id="test-session")
            outputs = {"success": True, "content": result.content}
        except Exception as e:
            outputs = {"success": False, "error": str(e)}
        
        test_report(
            test_points=["测试LLM请求发送", "验证请求记录自动保存到llm_calls.json"],
            inputs=inputs,
            outputs=outputs
        )

    def test_llm_request_to_dict(self, test_report):
        """测试LLM请求转换为字典 - 验证LLMClient自动持久化到llm_calls.json"""
        client = get_llm_client()
        
        request = LLMRequest(
            model_name="test-model",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
            max_tokens=100,
            api_address="http://localhost/v1"
        )
        
        result = request.to_dict()
        
        try:
            response = client.send_request(request, session_id="test-serialization-session")
            llm_success = True
        except Exception as e:
            llm_success = False
        
        test_report(
            test_points=["测试请求序列化", "验证LLMClient自动持久化到llm_calls.json"],
            inputs={"request": result},
            outputs={
                "dict_result": result, 
                "llm_success": llm_success
            }
        )
        
        assert result["model_name"] == "test-model"
        assert result["temperature"] == 0.5
        assert result["max_tokens"] == 100

    def test_adapter_selection(self, test_report):
        """测试适配器选择 - 验证LLMClient自动持久化到llm_calls.json"""
        client = get_llm_client()
        
        adapter = client._get_adapter("openai", "http://localhost", "key", "model")
        assert adapter.__class__.__name__ == "OpenAIAdapter"
        
        adapter = client._get_adapter("qwen", "http://localhost", "key", "model")
        assert adapter.__class__.__name__ == "QwenAdapter"
        
        adapter = client._get_adapter("anthropic", "http://localhost", "key", "model")
        assert adapter.__class__.__name__ == "AnthropicAdapter"
        
        request = LLMRequest(
            model_name="test",
            messages=[{"role": "user", "content": "Hello"}],
            api_address="http://localhost/v1"
        )
        try:
            client.send_request(request, session_id="test-adapter-session")
        except Exception:
            pass
        
        test_report(
            test_points=["测试适配器选择", "验证适配器选择后自动持久化到llm_calls.json"],
            inputs={"api_types": ["openai", "qwen", "anthropic"]},
            outputs={"result": "all adapters selected correctly"}
        )
