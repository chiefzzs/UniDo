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

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory


@dataclass
class PromptTemplate:
    template_id: str
    name: str
    content: str
    type: str
    parameters: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        return cls(**data)


@dataclass
class RequestConfiguration:
    config_id: str
    name: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = True
    default_tools: List[str] = field(default_factory=list)
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestConfiguration':
        return cls(**data)


@dataclass
class LLMRequest:
    messages: List[Dict[str, str]]
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    tools: List[Dict] = field(default_factory=list)
    tool_choice: str = "auto"
    stream: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMRequest':
        return cls(**data)


class PromptBuilder:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def _generate_id(self) -> str:
        return f"template-{uuid.uuid4().hex[:12]}"

    def create_template(self, name: str, content: str, template_type: str,
                       parameters: List[str] = None) -> PromptTemplate:
        template = PromptTemplate(
            template_id=self._generate_id(),
            name=name,
            content=content,
            type=template_type,
            parameters=parameters or []
        )
        self.persistence.save('prompt_template', template.to_dict())
        return template

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        all_templates = self.persistence.list('prompt_template')
        for t in all_templates:
            if t.get('template_id') == template_id:
                return PromptTemplate.from_dict(t)
        return None

    def list_templates(self, template_type: str = None) -> List[PromptTemplate]:
        all_templates = self.persistence.list('prompt_template')
        result = [PromptTemplate.from_dict(t) for t in all_templates]

        if template_type:
            result = [t for t in result if t.type == template_type]

        return result

    def build_system_prompt(self, session_id: str = None, template_id: str = None,
                           **kwargs) -> str:
        if template_id:
            template = self.get_template(template_id)
            if template:
                content = template.content
                for param in template.parameters:
                    if param in kwargs:
                        content = content.replace(f'{{{param}}}', str(kwargs[param]))
                return content

        default_prompt = """你是一个专业的AI助手，擅长帮助用户完成各种任务。
请始终保持友好、专业和准确的态度。"""

        if kwargs:
            for key, value in kwargs.items():
                default_prompt = default_prompt.replace(f'{{{key}}}', str(value))

        return default_prompt

    def build_user_prompt(self, message: str) -> str:
        return message

    def build_agent_info(self) -> str:
        return "AI Assistant v1.0"


class ContextBuilder:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def build_context(self, session_id: str, max_tokens: int = None) -> List[Dict]:
        all_messages = self.persistence.list('messages')
        session_messages = [m for m in all_messages if m.get('session_id') == session_id]

        session_messages.sort(key=lambda x: x.get('created_at', ''))

        if max_tokens:
            session_messages = self.truncate_context(session_messages, max_tokens)

        return session_messages

    def truncate_context(self, messages: List[Dict], max_tokens: int) -> List[Dict]:
        total_tokens = sum(len(str(m.get('content', ''))) for m in messages)

        if total_tokens <= max_tokens:
            return messages

        truncated = []
        current_tokens = 0

        for msg in reversed(messages):
            msg_tokens = len(str(msg.get('content', '')))
            if current_tokens + msg_tokens <= max_tokens:
                truncated.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        return truncated

    def format_memory(self, memory_entries: List[Dict]) -> List[Dict]:
        formatted = []
        for entry in memory_entries:
            formatted.append({
                'role': 'system',
                'content': entry.get('content', '')
            })
        return formatted


class RequestBuilder:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def _generate_id(self) -> str:
        return f"req-config-{uuid.uuid4().hex[:12]}"

    def create_request_configuration(self, name: str, model: str, temperature: float = 0.7,
                                   max_tokens: int = 2000, stream: bool = True,
                                   default_tools: List[str] = None) -> RequestConfiguration:
        config = RequestConfiguration(
            config_id=self._generate_id(),
            name=name,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            default_tools=default_tools or []
        )
        self.persistence.save('request_configuration', config.to_dict())
        return config

    def get_request_configuration(self, config_id: str) -> Optional[RequestConfiguration]:
        all_configs = self.persistence.list('request_configuration')
        for c in all_configs:
            if c.get('config_id') == config_id:
                return RequestConfiguration.from_dict(c)
        return None

    def list_request_configurations(self) -> List[RequestConfiguration]:
        all_configs = self.persistence.list('request_configuration')
        return [RequestConfiguration.from_dict(c) for c in all_configs]

    def build_request(self, session_id: str, messages: List[Dict],
                      model: str = None, temperature: float = 0.7,
                      max_tokens: int = 2000, tools: List[Dict] = None,
                      stream: bool = True, **kwargs) -> LLMRequest:
        if not model:
            model = "default-model"

        request = LLMRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools or [],
            stream=stream
        )

        self.persistence.save('llm_request', request.to_dict())

        return request

    def build_stream_request(self, session_id: str, messages: List[Dict],
                            model: str = None, **kwargs) -> LLMRequest:
        return self.build_request(session_id, messages, model=model, stream=True, **kwargs)

    def validate_request(self, request: LLMRequest) -> bool:
        if not request.messages:
            return False
        if not request.model:
            return False
        if request.max_tokens <= 0:
            return False
        return True


def get_prompt_builder() -> PromptBuilder:
    return PromptBuilder()


def get_context_builder() -> ContextBuilder:
    return ContextBuilder()


def get_request_builder() -> RequestBuilder:
    return RequestBuilder()
