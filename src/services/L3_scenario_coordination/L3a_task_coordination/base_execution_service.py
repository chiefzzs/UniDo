from typing import Any, Dict, List, Optional
from datetime import datetime
from ..schemas import Task, TaskStatus
from .intent_service import IntentService, IntentAnalysisResult, ExecutionPath, SingleToolInfo
from services.L2_domain.L2c_tool_execution import ToolExecutor

class BaseExecutionService:
    def __init__(self):
        self.intent_service = IntentService()
        self.tool_task_executor = None
        self.task_group_executor = None
        self.tool_executor = None
    
    def _get_tool_task_executor(self):
        if self.tool_task_executor is None:
            from .tool_task_executor import ToolTaskExecutor
            self.tool_task_executor = ToolTaskExecutor()
        return self.tool_task_executor
    
    def _get_task_group_executor(self):
        if self.task_group_executor is None:
            from .task_group_executor import TaskGroupExecutor
            self.task_group_executor = TaskGroupExecutor()
        return self.task_group_executor
    
    def execute_task(self, task: Task) -> Task:
        task.status = TaskStatus.ANALYZING
        task.updated_at = datetime.now()
        
        intent_result = self.intent_service.analyze_intent(task.input_data)
        
        if intent_result.execution_path == ExecutionPath.DIRECT_COMPLETION:
            return self.execute_direct_completion(task, intent_result)
        elif intent_result.execution_path == ExecutionPath.SINGLE_TOOL:
            return self._get_tool_task_executor().execute(task, intent_result)
        elif intent_result.execution_path == ExecutionPath.TASK_GROUP:
            return self._get_task_group_executor().execute(task, intent_result)
        
        return task
    
    def execute_direct_completion(self, task: Task, intent_result: Any) -> Task:
        task.status = TaskStatus.COMPLETED
        task.output_data = {
            "result": "任务已直接完成",
            "reasoning": intent_result.reasoning
        }
        task.completed_at = datetime.now()
        return task

    def _get_tool_executor(self) -> ToolExecutor:
        """获取工具执行器（懒加载）"""
        if self.tool_executor is None:
            self.tool_executor = ToolExecutor()
        return self.tool_executor

    def execute_with_recursive_llm(self, task: Task, session_id: str, user_input: str) -> Task:
        """
        使用递归 LLM 调用执行任务

        流程：
        1. 调用 DialogueBasedLLMService.call_llm() 获取 LLM 响应
        2. 如果返回 tool_calls：
           a. 解析工具调用信息
           b. 执行工具
           c. 将结果转换为 role=tool 消息，添加到 messages
           d. 再次调用 LLM（带新的 messages）
           e. 重复直到 finish_reason=stop
        3. 返回最终回复

        职责边界：
        - BaseExecutionService：协调 LLM 调用和工具执行的循环
        - DialogueBasedLLMService：负责 LLM 调用和消息构造（不变）
        - ToolExecutor：负责执行单个工具（不变）

        Args:
            task: 任务对象
            session_id: 会话ID
            user_input: 用户输入

        Returns:
            更新后的任务对象
        """
        from .dialogue_based_llm_service import DialogueBasedLLMService
        from services.L2_domain.L2b_memory_state.message_service import MessageService
        from services.L2_domain.L2b_memory_state.dialog_service import DialogService

        max_iterations = 10
        iteration = 0
        messages = []  # 累积的对话历史

        # 获取 LLM 服务实例
        llm_service = DialogueBasedLLMService()
        
        # 获取消息服务用于保存历史
        message_service = MessageService()
        dialog_service = DialogService()
        
        # 获取或创建 dialog_id
        dialogs = dialog_service.list_dialogs(session_id)
        if dialogs:
            dialog_id = dialogs[0].dialog_id
        else:
            dialog = dialog_service.create_dialog(session_id=session_id, dialog_type="text")
            dialog_id = dialog.dialog_id

        # 构建初始 messages
        messages = llm_service.build_messages_from_history(session_id, user_input, llm_service.get_tools_for_llm())

        print(f"[BaseExecutionService] 初始 messages 数量: {len(messages)}")

        while iteration < max_iterations:
            iteration += 1
            print(f"[BaseExecutionService] LLM 调用迭代 {iteration}")

            # 调用 LLM（传递累积的 messages）
            llm_response = llm_service.call_llm(
                session_id=session_id,
                user_input=user_input,
                messages=messages
            )

            if not llm_response.success:
                task.status = TaskStatus.FAILED
                task.error_message = llm_response.error or "LLM 调用失败"
                break

            # 检查是否有工具调用
            tool_calls = llm_response.tool_calls

            if tool_calls and len(tool_calls) > 0:
                print(f"[BaseExecutionService] LLM 返回 {len(tool_calls)} 个工具调用")

                # 记录 assistant 消息（包含 tool_calls）
                assistant_msg = {
                    "role": "assistant",
                    "content": llm_response.content or "",
                    "tool_calls": tool_calls
                }
                messages.append(assistant_msg)
                
                # 保存 assistant 消息到 MessageService（包含 tool_calls）
                message_service.create_message(
                    dialog_id=dialog_id,
                    role="assistant",
                    content=llm_response.content or "",
                    metadata={"tool_calls": tool_calls}
                )

                # 执行每个工具调用
                tool_results = []
                for tool_call in tool_calls:
                    tool_result = self._execute_single_tool_call(tool_call, session_id)
                    tool_results.append(tool_result)
                    
                    tool_call_id = tool_call.get('id', '')
                    tool_content = str(tool_result.get('result', ''))

                    # 将工具结果转换为 role=tool 消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": tool_content
                    })
                    
                    # 保存 tool 消息到 MessageService
                    message_service.create_message(
                        dialog_id=dialog_id,
                        role="tool",
                        content=tool_content,
                        metadata={"tool_call_id": tool_call_id, "tool_result": tool_result}
                    )

                # 继续循环，再次调用 LLM
                continue

            # 如果没有工具调用，检查是否是最终回复
            if llm_response.content:
                print(f"[BaseExecutionService] 收到最终回复，长度: {len(llm_response.content)}")

                # 记录最后的 assistant 消息
                messages.append({
                    "role": "assistant",
                    "content": llm_response.content
                })

                # 任务完成
                task.status = TaskStatus.COMPLETED
                task.output_data = {
                    "result": llm_response.content,
                    "iterations": iteration,
                    "tool_calls": self._collect_tool_calls_from_messages(messages)
                }
                task.completed_at = datetime.now()
                break
            else:
                # 无内容且无工具调用，可能是异常
                task.status = TaskStatus.FAILED
                task.error_message = "LLM 返回空响应"
                break

        if iteration >= max_iterations:
            print(f"[BaseExecutionService] 达到最大迭代次数 {max_iterations}")
            task.status = TaskStatus.COMPLETED
            task.output_data = {
                "result": "任务执行达到最大迭代次数",
                "iterations": iteration
            }

        return task

    def _execute_single_tool_call(self, tool_call: Dict, session_id: str) -> Dict:
        """
        执行单个工具调用

        Args:
            tool_call: 工具调用信息
            session_id: 会话ID

        Returns:
            工具执行结果
        """
        tool_executor = self._get_tool_executor()

        # 解析工具调用信息
        if 'function' in tool_call:
            tool_name = tool_call['function'].get('name', '')
            arguments = tool_call['function'].get('arguments', {})
        else:
            tool_name = tool_call.get('name', '')
            arguments = tool_call.get('arguments', {})

        # 解析 arguments（可能是字符串）
        if isinstance(arguments, str):
            import json
            try:
                arguments = json.loads(arguments)
            except:
                arguments = {}

        print(f"[BaseExecutionService] 执行工具: {tool_name}, 参数: {arguments}")

        try:
            result = tool_executor.execute_tool(
                tool_name=tool_name,
                dialog_id=session_id,
                task_id=session_id,
                params=arguments
            )

            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "call_id": result.call_id
            }
        except Exception as e:
            print(f"[BaseExecutionService] 工具执行异常: {e}")
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }

    def _collect_tool_calls_from_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        从 messages 中收集所有工具调用和结果

        Args:
            messages: 消息列表

        Returns:
            工具调用历史列表
        """
        tool_calls_history = []

        for msg in messages:
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                for tc in msg.get('tool_calls', []):
                    tool_calls_history.append({
                        "type": "assistant_tool_call",
                        "tool_name": tc.get('function', {}).get('name', ''),
                        "call_id": tc.get('id', ''),
                        "arguments": tc.get('function', {}).get('arguments', '')
                    })
            elif msg.get('role') == 'tool':
                tool_calls_history.append({
                    "type": "tool_result",
                    "call_id": msg.get('tool_call_id', ''),
                    "content": msg.get('content', '')
                })

        return tool_calls_history
