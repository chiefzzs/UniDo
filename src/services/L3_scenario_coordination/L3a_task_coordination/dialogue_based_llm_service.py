"""
L3a Dialogue-Based LLM Service

基于对话的LLM调用服务，负责：
1. 通过历史记录构造messages
2. 通过工具管理获取工具定义
3. 调用L2d LLM执行服务
4. 为意图分析层提供LLM调用能力

依赖：
- L2d LLM执行服务：执行实际的LLM调用
- L2b 记忆服务：获取对话历史
- L2f 工具管理服务：获取工具定义
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from services.L2_domain.L2d_llm_execution import LLMExecutionService
from services.L2_domain.L2b_memory_state import MemoryService
from services.L2_domain.L2f_tool_management import ToolManagementService, ToolDefinition


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class DialogueMessage:
    """对话消息结构"""
    role: str
    content: str
    tool_call: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"role": self.role, "content": self.content}
        if self.tool_call:
            result["tool_calls"] = [self.tool_call]
        if self.tool_result:
            result["tool_result"] = self.tool_result
        return result


@dataclass
class LLMRequest:
    """LLM请求结构"""
    session_id: str
    messages: List[Dict[str, Any]]
    model_config_id: str = "default"
    max_tokens: int = 4096
    temperature: float = 0.7
    tools: Optional[List[Dict[str, Any]]] = None
    stream: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "model_config_id": self.model_config_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "tools": self.tools,
            "stream": self.stream
        }


@dataclass
class LLMResponse:
    """LLM响应结构"""
    success: bool
    content: str = ""
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "content": self.content,
            "tool_calls": self.tool_calls,
            "usage": self.usage,
            "error": self.error
        }


class DialogueBasedLLMService:
    """
    基于对话的LLM调用服务
    
    核心职责：
    1. 从记忆服务获取对话历史
    2. 构造标准格式的messages
    3. 获取工具定义并转换为LLM所需格式
    4. 调用L2d LLM执行服务
    5. 处理响应并返回结构化结果
    """

    def __init__(self):
        self.llm_executor = LLMExecutionService()
        self.memory_service = MemoryService()
        self.tool_management = ToolManagementService()
        # 自动加载工具描述文件
        self._load_tool_descriptions()
    
    def _load_tool_descriptions(self):
        """
        自动加载工具描述文件
        """
        try:
            loaded_count = self.tool_management.load_tools_from_descriptions('en')
            if loaded_count > 0:
                print(f"[DialogueBasedLLMService] 已加载 {loaded_count} 个工具描述")
            else:
                print(f"[DialogueBasedLLMService] 未加载到工具描述")
        except Exception as e:
            print(f"[DialogueBasedLLMService] 加载工具描述失败: {e}")

    def build_messages_from_history(self, session_id: str, user_input: str, 
                                     tools: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        从历史记录构造messages
        
        Args:
            session_id: 会话ID
            user_input: 当前用户输入
            tools: 工具定义列表
            
        Returns:
            构造好的messages列表
        """
        messages = []
        
        # 添加系统消息（包含工具信息）
        system_prompt = self._get_system_prompt(tools)
        messages.append({"role": MessageRole.SYSTEM.value, "content": system_prompt})
        
        # 获取历史消息
        history = self.memory_service.get_short_term_memory(session_id)
        
        if history:
            for item in history:
                role = item.get("role", "user")
                content = item.get("content", "")
                
                # 处理工具调用消息
                if item.get("tool_call"):
                    messages.append({
                        "role": role,
                        "content": content,
                        "tool_calls": [item["tool_call"]]
                    })
                # 处理工具结果消息
                elif item.get("tool_result"):
                    messages.append({
                        "role": MessageRole.TOOL.value,
                        "content": item["tool_result"]
                    })
                else:
                    messages.append({"role": role, "content": content})
        
        # 添加当前用户输入（包含环境信息）
        user_message = self._build_user_message_with_context(user_input)
        messages.append(user_message)
        
        return messages
    
    def _build_user_message_with_context(self, user_input: str) -> Dict[str, Any]:
        """
        构建包含环境信息的用户消息
        
        Args:
            user_input: 用户原始输入
            
        Returns:
            包含环境信息的用户消息对象
        """
        from services.L1_infrastructure import get_prompt_manager
        
        try:
            prompt_manager = get_prompt_manager()
            
            # 获取环境信息
            import os
            workspace_path = self._get_workspace_path()
            
            env_info = {
                "Operating system": os.name,
                "Working directories": workspace_path,
                "Today's date": self._get_current_date()
            }
            
            print(f"[DialogueBasedLLMService] 环境信息: {env_info}")
            
            # 使用 PromptManager 构建用户消息
            user_message = prompt_manager.build_user_message_for_llm(user_input, env_info)
            print(f"[DialogueBasedLLMService] 构建的用户消息长度: {len(str(user_message))}")
            
            return user_message
        except Exception as e:
            import traceback
            print(f"[DialogueBasedLLMService] 构建用户消息上下文失败: {e}")
            traceback.print_exc()
            # 降级：返回简单的用户消息
            return {"role": MessageRole.USER.value, "content": user_input}
    
    def _get_workspace_path(self) -> str:
        """
        获取当前workspace路径
        
        优先从workspace配置中获取，如果没有配置则使用应用当前目录
        
        Returns:
            workspace绝对路径
        """
        import os
        try:
            # 尝试从workspace配置服务获取
            from services.L2_domain.L2a_project_config.workspace_config_service import WorkspaceConfigService
            
            workspace_service = WorkspaceConfigService()
            configs = workspace_service.list_workspace_configs()
            
            if configs:
                # 返回第一个配置的路径（可以优化为根据session获取对应的workspace）
                return configs[0].root_path
        except Exception as e:
            print(f"[DialogueBasedLLMService] 获取workspace配置失败: {e}")
        
        # 降级：使用应用当前目录
        return os.path.abspath(os.getcwd())
    
    def _get_current_date(self) -> str:
        """获取当前日期字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    def _get_system_prompt(self, tools: List[Dict[str, Any]] = None) -> str:
        """获取系统提示词"""
        # 将工具列表转换为可读格式
        tools_description = self._format_tools_for_prompt(tools or [])
        
        return f"""你是一个智能助手，能够理解用户意图并调用合适的工具来完成任务。

## 角色
- 你是一个有能力的AI助手
- 你可以使用工具来获取信息或执行操作
- 如果不需要工具，直接回答用户问题

## 可用工具
{tools_description}

## 输出格式
- 如果需要调用工具，输出JSON格式的工具调用
- 如果直接回答，输出自然语言文本

## 注意事项
- 仔细分析用户问题，确定是否需要调用工具
- 如果调用工具，确保参数正确
- 如果收到工具结果，用自然语言总结给用户
"""
    
    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        将工具列表格式化为系统提示词中的工具描述
        
        Args:
            tools: 工具定义列表
            
        Returns:
            格式化的工具描述字符串
        """
        if not tools:
            return "无可用工具"
        
        tool_descriptions = []
        for tool in tools:
            function_info = tool.get("function", {})
            tool_name = function_info.get("name", "未知工具")
            description = function_info.get("description", "无描述")
            parameters = function_info.get("parameters", {})
            
            # 格式化参数
            param_descriptions = []
            for param_name, param_info in parameters.items():
                param_type = param_info.get("type", "string")
                param_desc = param_info.get("description", "")
                param_required = param_info.get("required", False)
                required_mark = "*" if param_required else ""
                param_descriptions.append(f"  - {required_mark}{param_name} ({param_type}): {param_desc}")
            
            params_str = "\n".join(param_descriptions) if param_descriptions else "  无参数"
            
            tool_descriptions.append(f"- {tool_name}: {description}\n  参数:\n{params_str}")
        
        return "\n\n".join(tool_descriptions)

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取工具定义并转换为LLM所需格式
        
        Returns:
            工具定义列表（LLM格式）
        """
        tools = []
        
        try:
            # 获取所有已注册的工具
            all_tools = self.tool_management.list_tools()
            
            for tool_def in all_tools:
                tool_dict = self._convert_tool_def_to_llm_format(tool_def)
                if tool_dict:
                    tools.append(tool_dict)
                    
        except Exception as e:
            print(f"获取工具定义失败: {e}")
        
        return tools

    def _convert_tool_def_to_llm_format(self, tool_def: ToolDefinition) -> Optional[Dict[str, Any]]:
        """
        将ToolDefinition转换为LLM工具调用格式
        
        Args:
            tool_def: 工具定义
            
        Returns:
            LLM格式的工具定义
        """
        try:
            return {
                "type": "function",
                "function": {
                    "name": tool_def.tool_name,
                    "description": tool_def.description,
                    "parameters": tool_def.parameters
                }
            }
        except Exception as e:
            print(f"转换工具定义失败: {e}")
            return None

    def construct_llm_request(self, session_id: str, user_input: str, 
                              include_tools: bool = True, **kwargs) -> LLMRequest:
        """
        构造完整的LLM请求
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            include_tools: 是否包含工具定义
            **kwargs: 其他参数（max_tokens, temperature等）
            
        Returns:
            LLMRequest对象
        """
        # 获取工具定义
        tools = self.get_tools_for_llm() if include_tools else None
        
        # 构建messages（包含工具信息）
        messages = self.build_messages_from_history(session_id, user_input, tools)
        
        # 构造请求
        llm_request = LLMRequest(
            session_id=session_id,
            messages=messages,
            model_config_id=kwargs.get("model_config_id", "default"),
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            tools=tools,
            stream=kwargs.get("stream", False)
        )
        
        # 发布LLM请求构造完毕消息
        self._publish_request_constructed_event(llm_request)
        
        return llm_request
    
    def _publish_request_constructed_event(self, llm_request: LLMRequest):
        """
        发布LLM请求构造完毕事件
        
        Args:
            llm_request: 构造好的LLM请求
        """
        try:
            from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
            from services.L1_infrastructure.L1d_events.event_types import EventTypes
            
            event_bus = EventBus.get_instance()
            event_bus.publish(Event(
                event_type=EventTypes.LLM_REQUEST_SENT,
                payload={
                    'session_id': llm_request.session_id,
                    'model_config_id': llm_request.model_config_id,
                    'num_messages': len(llm_request.messages),
                    'num_tools': len(llm_request.tools) if llm_request.tools else 0,
                    'stream': llm_request.stream
                }
            ))
            print(f"✅ 已发布LLM请求构造完毕事件: session_id={llm_request.session_id}")
        except Exception as e:
            print(f"❌ 发布LLM请求构造完毕事件失败: {e}")

    def call_llm(self, session_id: str, user_input: str, **kwargs) -> LLMResponse:
        """
        调用LLM执行服务
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            **kwargs: 额外参数
            
        Returns:
            LLMResponse对象
        """
        try:
            # 构造请求
            llm_request = self.construct_llm_request(session_id, user_input, **kwargs)
            
            # 调用L2d LLM执行服务
            response = self.llm_executor.execute(
                session_id=llm_request.session_id,
                model_config_id=llm_request.model_config_id,
                messages=llm_request.messages,
                max_tokens=llm_request.max_tokens,
                temperature=llm_request.temperature,
                stream=llm_request.stream,
                tools=llm_request.tools
            )
            
            # 解析响应
            return self._parse_llm_response(response)
            
        except Exception as e:
            return LLMResponse(
                success=False,
                error=f"LLM调用失败: {str(e)}"
            )

    def _parse_llm_response(self, response) -> LLMResponse:
        """
        解析LLM执行服务的响应
        
        Args:
            response: L2d LLM执行服务返回的响应
            
        Returns:
            结构化的LLMResponse
        """
        try:
            # 检查响应是否成功
            if hasattr(response, 'success') and not response.success:
                # 发布响应分类事件 - 失败类型
                self._publish_response_classified_event(
                    response_type='error',
                    content='',
                    tool_calls=[],
                    finish_reason='error',
                    error=getattr(response, 'error', '未知错误')
                )
                return LLMResponse(
                    success=False,
                    error=getattr(response, 'error', '未知错误')
                )
            
            # 提取内容
            content = getattr(response, 'content', '')
            tool_calls = getattr(response, 'tool_calls', None) or []
            usage = getattr(response, 'usage', None)
            finish_reason = getattr(response, 'finish_reason', '')
            
            # 检查内容是否为空，如果为空则视为失败
            # 但如果有工具调用或finish_reason是tool_calls，则不视为失败
            if not content and not tool_calls:
                self._publish_response_classified_event(
                    response_type='empty',
                    content='',
                    tool_calls=[],
                    finish_reason=finish_reason,
                    error='LLM返回空内容'
                )
                return LLMResponse(
                    success=False,
                    error='LLM返回空内容'
                )
            
            # 如果finish_reason是tool_calls但tool_calls为空或None，设置默认空列表
            if finish_reason == 'tool_calls' and (tool_calls is None or tool_calls == []):
                # 这可能是解析问题，检查原始响应
                if hasattr(response, '_original_response'):
                    original_tool_calls = getattr(response._original_response, 'tool_calls', None)
                    if original_tool_calls:
                        tool_calls = original_tool_calls
            
            # 判断响应类型并发布事件
            response_type = self._classify_response(content, tool_calls, finish_reason)
            self._publish_response_classified_event(
                response_type=response_type,
                content=content,
                tool_calls=tool_calls,
                finish_reason=finish_reason,
                usage=usage
            )
            
            return LLMResponse(
                success=True,
                content=content,
                tool_calls=tool_calls,
                usage=usage
            )
            
        except Exception as e:
            return LLMResponse(
                success=False,
                error=f"解析响应失败: {str(e)}"
            )

    def analyze_intent(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        基于LLM进行意图分析（为意图服务提供能力）
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            
        Returns:
            意图分析结果
        """
        # 构造意图分析的系统提示词
        intent_prompt = """你是一个意图分析助手。请分析用户输入并返回JSON格式的结果：
        
{
    "intent_type": "direct_completion|single_tool|task_group",
    "confidence": 0.0-1.0,
    "reasoning": "分析理由",
    "tool_info": {
        "tool_name": "工具名称",
        "parameters": {"参数名": "参数值"}
    },
    "task_info": {
        "execution_mode": "sequential|parallel|dependency_based",
        "subtasks": [{"description": "子任务描述"}]
    }
}

## 意图类型说明：
1. direct_completion：简单问答（问候、介绍自己、闲聊等），无需工具
2. single_tool：需要调用单个工具完成任务
3. task_group：需要多个任务协作完成

## 示例：
- 用户："你好" → intent_type: "direct_completion"
- 用户："帮我读取README.md" → intent_type: "single_tool", tool_name: "Read"
- 用户："分析项目结构并生成文档" → intent_type: "task_group"
"""
        
        messages = [
            {"role": "system", "content": intent_prompt},
            {"role": "user", "content": user_input}
        ]
        
        try:
            # 调用LLM执行意图分析
            response = self.llm_executor.execute(
                session_id=f"intent-analysis-{session_id}",
                model_config_id="default",
                messages=messages,
                max_tokens=1024,
                temperature=0.1  # 意图分析使用较低温度，提高确定性
            )
            
            if response and hasattr(response, 'content'):
                import json
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    # 如果不是有效JSON，返回默认分析
                    return self._default_intent_analysis(user_input)
            
            return self._default_intent_analysis(user_input)
            
        except Exception as e:
            print(f"意图分析失败: {e}")
            return self._default_intent_analysis(user_input)

    def _default_intent_analysis(self, user_input: str) -> Dict[str, Any]:
        """
        默认意图分析（当LLM调用失败时使用）
        
        Args:
            user_input: 用户输入
            
        Returns:
            默认意图分析结果
        """
        simple_patterns = ["你好", "您好", "谢谢", "再见", "你是谁", "介绍自己", "很高兴认识你"]
        
        if any(pattern in user_input for pattern in simple_patterns):
            return {
                "intent_type": "direct_completion",
                "confidence": 0.95,
                "reasoning": "简单问候或自我介绍"
            }
        
        return {
            "intent_type": "task_group",
            "confidence": 0.7,
            "reasoning": "复杂任务，需要进一步分析",
            "task_info": {
                "execution_mode": "sequential",
                "subtasks": [
                    {"description": "分析用户需求"},
                    {"description": "执行必要操作"},
                    {"description": "汇总结果"}
                ]
            }
        }

    def generate_task_plan(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        生成任务规划（为任务组执行提供能力）
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            
        Returns:
            任务规划
        """
        plan_prompt = """你是一个任务规划助手。请根据用户需求生成详细的任务规划：
        
{
    "plan_name": "任务名称",
    "execution_mode": "sequential|parallel|dependency_based",
    "tasks": [
        {
            "task_id": "任务ID",
            "name": "任务名称",
            "description": "任务描述",
            "task_type": "direct|single_tool|task_group",
            "tool_name": "工具名称（如果是工具调用）",
            "parameters": {"参数": "值"},
            "dependencies": ["依赖的任务ID列表"]
        }
    ],
    "summary": "任务规划摘要"
}
"""
        
        messages = [
            {"role": "system", "content": plan_prompt},
            {"role": "user", "content": f"根据以下需求生成任务规划：{user_input}"}
        ]
        
        try:
            response = self.llm_executor.execute(
                session_id=f"task-plan-{session_id}",
                model_config_id="default",
                messages=messages,
                max_tokens=2048,
                temperature=0.3
            )
            
            if response and hasattr(response, 'content'):
                import json
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return self._default_task_plan(user_input)
            
            return self._default_task_plan(user_input)
            
        except Exception as e:
            print(f"任务规划失败: {e}")
            return self._default_task_plan(user_input)

    def _default_task_plan(self, user_input: str) -> Dict[str, Any]:
        """
        默认任务规划
        
        Args:
            user_input: 用户输入
            
        Returns:
            默认任务规划
        """
        return {
            "plan_name": "任务规划",
            "execution_mode": "sequential",
            "tasks": [
                {
                    "task_id": "task-1",
                    "name": "分析需求",
                    "description": "分析用户需求",
                    "task_type": "direct",
                    "dependencies": []
                },
                {
                    "task_id": "task-2",
                    "name": "执行操作",
                    "description": "执行必要的操作",
                    "task_type": "single_tool",
                    "tool_name": "default",
                    "parameters": {"input": user_input},
                    "dependencies": ["task-1"]
                },
                {
                    "task_id": "task-3",
                    "name": "汇总结果",
                    "description": "汇总执行结果",
                    "task_type": "direct",
                    "dependencies": ["task-2"]
                }
            ],
            "summary": "基于用户输入生成的默认任务规划"
        }
    
    def _classify_response(self, content: str, tool_calls: list, finish_reason: str) -> str:
        """
        分类LLM响应类型
        
        Args:
            content: LLM返回的内容
            tool_calls: 工具调用列表
            finish_reason: 结束原因
            
        Returns:
            响应类型字符串
        """
        # 判断优先级：工具调用 > 直接回答 > 混合响应
        
        # 工具调用类型
        if tool_calls and len(tool_calls) > 0:
            if content and len(content.strip()) > 0:
                return 'tool_call_with_explanation'
            return 'tool_call_only'
        
        # 直接回答类型
        if content and len(content.strip()) > 0:
            return 'direct_answer'
        
        # 混合响应（内容+工具调用）
        if content and tool_calls:
            return 'mixed_response'
        
        # 其他情况
        return 'unknown'
    
    def _publish_response_classified_event(self, **kwargs):
        """
        发布LLM响应分类事件（L3层）
        
        Args:
            response_type: 响应类型
            content: 响应内容
            tool_calls: 工具调用列表
            finish_reason: 结束原因
            usage: 使用统计
            error: 错误信息（可选）
        """
        try:
            from services.L1_infrastructure.L1d_events.event_record import Event
            from services.L1_infrastructure.L1d_events.event_types import EventTypes
            
            event_bus = self._get_event_bus()
            
            # 构建事件payload
            payload = {
                'response_type': kwargs.get('response_type', 'unknown'),
                'has_content': bool(kwargs.get('content')),
                'content_length': len(kwargs.get('content', '')) if kwargs.get('content') else 0,
                'has_tool_calls': bool(kwargs.get('tool_calls') and len(kwargs.get('tool_calls')) > 0),
                'tool_call_count': len(kwargs.get('tool_calls', [])),
                'tool_names': [tc.get('function', {}).get('name', tc.get('name', '')) 
                             for tc in kwargs.get('tool_calls', [])],
                'finish_reason': kwargs.get('finish_reason', ''),
                'source_component': 'L3_task_coordination',
                'source_service': 'DialogueBasedLLMService'
            }
            
            # 添加usage信息
            if kwargs.get('usage'):
                payload['usage'] = {
                    'prompt_tokens': kwargs['usage'].get('prompt_tokens', 0),
                    'completion_tokens': kwargs['usage'].get('completion_tokens', 0),
                    'total_tokens': kwargs['usage'].get('total_tokens', 0)
                }
            
            # 添加错误信息（如果有）
            if kwargs.get('error'):
                payload['error'] = kwargs['error']
                payload['success'] = False
            else:
                payload['success'] = True
            
            # 发布事件
            event_bus.publish(Event(
                event_type=EventTypes.LLM_RESPONSE_CLASSIFIED,
                payload=payload
            ))
            
        except Exception as e:
            print(f"❌ 发布LLM响应分类事件失败: {e}")
    
    def _get_event_bus(self):
        """获取事件总线实例"""
        from services.L1_infrastructure.L1d_events.event_bus import EventBus
        return EventBus.get_instance()
