"""
Linux平台RunCommand工具实现
使用bash执行命令
"""
import subprocess
from typing import Dict, Any
from .base_tool import BaseTool


class LinuxRunCommandTool(BaseTool):
    """
    Linux平台执行命令工具
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
        执行命令 - Linux版本
        
        Args:
            params: 工具参数，包含 command, requires_approval 字段
            
        Returns:
            命令执行结果
        """
        command = params.get("command", "")
        requires_approval = params.get("requires_approval", False)
        
        if not command:
            return {"error": "命令不能为空"}
        
        # 如果需要批准，返回待批准状态
        if requires_approval:
            command_id = f"cmd_{id(command)}"
            self.commands[command_id] = {
                "command": command,
                "status": "pending_approval",
                "requires_approval": True
            }
            return {
                "command_id": command_id,
                "command": command,
                "status": "pending_approval",
                "message": "命令等待用户批准"
            }
        
        try:
            # Linux/macOS使用bash执行
            full_command = ["bash", "-c", command]
            
            result = subprocess.run(
                full_command,
                shell=False,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            command_id = f"cmd_{id(command)}"
            self.commands[command_id] = {
                "command": command,
                "status": "completed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return {
                "command_id": command_id,
                "command": command,
                "status": "completed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "命令执行超时"}
        except Exception as e:
            return {"error": str(e)}


class MacOsRunCommandTool(LinuxRunCommandTool):
    """
    macOS平台执行命令工具
    继承自Linux实现
    """
    pass
