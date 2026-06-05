from datetime import datetime
from ..schemas import Task, TaskStatus
from .intent_service import IntentAnalysisResult
from services.L2_domain.L2c_tool_execution import ToolExecutor

class ToolTaskExecutor:
    def __init__(self):
        self.tool_executor = ToolExecutor()
        self.check_task_service = None
        self.adjust_task_service = None
    
    def _get_check_task_service(self):
        if self.check_task_service is None:
            from .check_task_service import CheckTaskService
            self.check_task_service = CheckTaskService()
        return self.check_task_service
    
    def _get_adjust_task_service(self):
        if self.adjust_task_service is None:
            from .adjust_task_service import AdjustTaskService
            self.adjust_task_service = AdjustTaskService()
        return self.adjust_task_service
    
    def execute(self, task: Task, intent_result: IntentAnalysisResult) -> Task:
        max_iterations = 3
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            task = self.execute_l2_tool(task, intent_result.single_tool_info)
            
            if task.status == TaskStatus.FAILED:
                break
            
            check_result = self._get_check_task_service().execute(task)
            
            adjust_result = self._get_adjust_task_service().execute(task, check_result)
            
            if adjust_result.output_data.get("action") == "complete":
                task.output_data = {"result": "成功", "iterations": iteration}
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                break
        
        return task
    
    def execute_l2_tool(self, task: Task, tool_info, tool_call_id: str = "", dialog_id: str = "", session_id: str = "") -> Task:
        """
        执行L2层工具
        
        Args:
            task: 任务对象
            tool_info: 工具信息
            tool_call_id: LLM返回的工具调用ID（符合OpenAI API标准，可选）
            dialog_id: 对话ID（可选，用于正确关联工具调用事件）
            session_id: 会话ID（可选，用于正确关联工具调用事件）
        
        Returns:
            更新后的任务对象
        """
        if tool_info:
            try:
                # 必须显式传入 dialog_id 和 session_id，不允许使用降级方案
                if dialog_id is None:
                    raise ValueError("execute_tool_step: dialog_id 参数缺失，必须显式传入")
                if session_id is None:
                    raise ValueError("execute_tool_step: session_id 参数缺失，必须显式传入")
                
                result = self.tool_executor.execute_tool(
                    tool_name=tool_info.tool_name,
                    dialog_id=dialog_id,
                    task_id=task.task_id,
                    params=tool_info.parameters,
                    session_id=session_id,  # 传递session_id，确保工具调用事件能正确关联会话
                    tool_call_id=tool_call_id  # 传递LLM原始调用ID（符合OpenAI API标准）
                )
                task.execution_history.append({
                    "step": "tool_execution",
                    "tool_name": tool_info.tool_name,
                    "result": str(result),
                    "timestamp": datetime.now().isoformat()
                })
                task.output_data["tool_result"] = result.to_dict() if hasattr(result, 'to_dict') else str(result)
                if result.success:
                    task.status = TaskStatus.COMPLETED
                else:
                    task.status = TaskStatus.FAILED
                    task.error_message = result.error
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
        
        return task
