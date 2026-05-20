from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from .dialogue_based_llm_service import DialogueBasedLLMService

class ExecutionPath(Enum):
    DIRECT_COMPLETION = "direct_completion"
    SINGLE_TOOL = "single_tool"
    TASK_GROUP = "task_group"

@dataclass
class SingleToolInfo:
    tool_id: str
    tool_name: str
    parameters: Dict[str, Any]

@dataclass
class TaskGroupInfo:
    class ExecutionMode(Enum):
        SEQUENTIAL = "sequential"
        PARALLEL = "parallel"
        DEPENDENCY_BASED = "dependency_based"
    
    execution_mode: ExecutionMode
    subtask_definitions: list

@dataclass
class IntentAnalysisResult:
    execution_path: ExecutionPath
    single_tool_info: Optional[SingleToolInfo] = None
    task_group_info: Optional[TaskGroupInfo] = None
    reasoning: str = ""

class IntentService:
    def __init__(self):
        # 使用基于对话的LLM服务，而非直接调用L2d
        self.dialogue_llm_service = DialogueBasedLLMService()
    
    def analyze_intent(self, task_input: Dict[str, Any]) -> IntentAnalysisResult:
        user_input = task_input.get("user_input", "")
        session_id = task_input.get("session_id", "default-session")
        
        # 简单问题快速判断
        if self._is_simple_question(user_input):
            return IntentAnalysisResult(
                execution_path=ExecutionPath.DIRECT_COMPLETION,
                reasoning="简单问题，无需工具调用"
            )
        
        # 需要单工具的场景
        if self._requires_single_tool(user_input):
            tool_info = self._extract_tool_info(user_input)
            return IntentAnalysisResult(
                execution_path=ExecutionPath.SINGLE_TOOL,
                single_tool_info=tool_info,
                reasoning="需要调用单个工具"
            )
        
        # 复杂任务需要调用 LLM 来分析
        return self._analyze_with_llm(session_id, user_input)
    
    def _analyze_with_llm(self, session_id: str, user_input: str) -> IntentAnalysisResult:
        """使用基于对话的LLM服务分析用户意图"""
        try:
            # 调用DialogueBasedLLMService进行意图分析
            # 该服务会自动从记忆服务获取历史记录并构造messages
            llm_result = self.dialogue_llm_service.analyze_intent(session_id, user_input)
            
            intent_type = llm_result.get("intent_type", "task_group")
            confidence = llm_result.get("confidence", 0.7)
            
            # 根据LLM分析结果判断意图
            if intent_type == "direct_completion":
                return IntentAnalysisResult(
                    execution_path=ExecutionPath.DIRECT_COMPLETION,
                    reasoning=f"LLM分析结果（置信度{confidence}）：{llm_result.get('reasoning', '')}"
                )
            elif intent_type == "single_tool":
                tool_info = llm_result.get("tool_info", {})
                return IntentAnalysisResult(
                    execution_path=ExecutionPath.SINGLE_TOOL,
                    single_tool_info=SingleToolInfo(
                        tool_id=tool_info.get("tool_id", tool_info.get("tool_name", "default")),
                        tool_name=tool_info.get("tool_name", "default"),
                        parameters=tool_info.get("parameters", {})
                    ),
                    reasoning=f"LLM分析结果（置信度{confidence}）：{llm_result.get('reasoning', '')}"
                )
            else:
                task_info = llm_result.get("task_info", {})
                execution_mode = task_info.get("execution_mode", "sequential")
                return IntentAnalysisResult(
                    execution_path=ExecutionPath.TASK_GROUP,
                    task_group_info=TaskGroupInfo(
                        execution_mode=TaskGroupInfo.ExecutionMode(execution_mode),
                        subtask_definitions=task_info.get("subtasks", self._generate_subtasks(user_input))
                    ),
                    reasoning=f"LLM分析结果（置信度{confidence}）：{llm_result.get('reasoning', '')}"
                )
                
        except Exception as e:
            # LLM 调用失败时使用默认行为
            return IntentAnalysisResult(
                execution_path=ExecutionPath.TASK_GROUP,
                task_group_info=TaskGroupInfo(
                    execution_mode=TaskGroupInfo.ExecutionMode.SEQUENTIAL,
                    subtask_definitions=self._generate_subtasks(user_input)
                ),
                reasoning=f"LLM分析失败，使用默认分析：{str(e)}"
            )
    
    def _is_simple_question(self, user_input: str) -> bool:
        simple_patterns = ["你好", "您好", "谢谢", "再见", "你是谁", "介绍自己", "很高兴认识你", "认识你", "打招呼"]
        return any(pattern in user_input for pattern in simple_patterns)
    
    def _requires_single_tool(self, user_input: str) -> bool:
        tool_keywords = ["计算", "打开", "读取", "写入", "删除", "查询"]
        return any(keyword in user_input for keyword in tool_keywords)
    
    def _extract_tool_info(self, user_input: str) -> SingleToolInfo:
        if "计算" in user_input:
            return SingleToolInfo(
                tool_id="calculator",
                tool_name="calculator",
                parameters={"expression": user_input.replace("计算", "").strip()}
            )
        return SingleToolInfo(
            tool_id="default",
            tool_name="default",
            parameters={"input": user_input}
        )
    
    def _generate_subtasks(self, user_input: str) -> list:
        return [
            {"step": 1, "description": "分析用户需求", "task_type": "analysis"},
            {"step": 2, "description": "执行必要操作", "task_type": "execution"},
            {"step": 3, "description": "汇总结果", "task_type": "summary"}
        ]
