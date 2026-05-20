"""
Windows平台RunCommand工具实现
使用PowerShell执行命令
"""
import subprocess
import sys
from typing import Dict, Any
from .base_tool import BaseTool


class WindowsRunCommandTool(BaseTool):
    """
    Windows平台执行命令工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T12"
        self.name = "RunCommand"
        self.category = "System"
        self.load_description()
        self.commands = {}
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行命令 - Windows版本
        
        Args:
            params: 工具参数，包含 command, requires_approval, workspace 字段
            
        Returns:
            命令执行结果
        """
        command = params.get("command", "")
        requires_approval = params.get("requires_approval", False)
        workspace = params.get("workspace")  # 获取workspace路径
        
        if not command:
            return {"error": "命令不能为空"}
        
        # 如果需要批准，返回待批准状态
        if requires_approval:
            command_id = f"cmd_{id(command)}"
            self.commands[command_id] = {
                "command": command,
                "status": "pending_approval",
                "requires_approval": True,
                "workspace": workspace
            }
            return {
                "command_id": command_id,
                "command": command,
                "status": "pending_approval",
                "message": "命令等待用户批准",
                "workspace": workspace
            }
        
        try:
            # Windows使用PowerShell执行
            full_command = ["powershell", "-Command", command]
            
            result = subprocess.run(
                full_command,
                shell=False,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=120,
                cwd=workspace if workspace else None  # 在workspace目录中执行命令
            )
            
            command_id = f"cmd_{id(command)}"
            self.commands[command_id] = {
                "command": command,
                "status": "completed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "workspace": workspace
            }
            
            return {
                "command_id": command_id,
                "command": command,
                "status": "completed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "workspace": workspace
            }
        except subprocess.TimeoutExpired:
            return {"error": "命令执行超时"}
        except Exception as e:
            return {"error": str(e)}
