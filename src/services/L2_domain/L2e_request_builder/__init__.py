"""
L2e Request Builder Service

L2e 请求构造服务负责构建和格式化 LLM 请求，包括 prompt 构建、上下文管理和参数配置。

职责：
- Prompt构建：构建LLM请求的prompt
- 上下文格式化：格式化上下文信息
- 工具描述集成：从L2f获取工具和技能的描述信息
- 参数配置：配置LLM请求参数

依赖 L1 层：
- L1b 持久化服务：用于存储 prompt 模板和请求配置

依赖 L2 层：
- L2b 记忆与状态管理：获取会话上下文和消息
- L2a 项目与配置管理：获取项目和模型配置
- L2f 工具管理服务：获取工具和技能描述
"""

from .request_builder import (
    PromptBuilder,
    ContextBuilder,
    RequestBuilder,
    PromptTemplate,
    RequestConfiguration,
    LLMRequest
)


def get_prompt_builder() -> PromptBuilder:
    """获取 Prompt 构建器实例"""
    return PromptBuilder()


def get_context_builder() -> ContextBuilder:
    """获取上下文构建器实例"""
    return ContextBuilder()


def get_request_builder() -> RequestBuilder:
    """获取请求构建器实例"""
    return RequestBuilder()
