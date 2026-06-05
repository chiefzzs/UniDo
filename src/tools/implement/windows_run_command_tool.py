"""
Windows平台RunCommand工具实现
使用PowerShell执行命令
"""
import subprocess
import sys
import threading
from typing import Dict, Any, Callable, Optional
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
    
    def _read_output_stream(self, process: subprocess.Popen, stream_name: str, output_callback: Optional[Callable] = None):
        """
        实时读取进程输出流并通过回调发送
        
        Args:
            process: 子进程对象
            stream_name: 流名称 (stdout/stderr)
            output_callback: 输出回调函数
        """
        try:
            stream = process.stdout if stream_name == 'stdout' else process.stderr
            for line in iter(stream.readline, ''):
                if not line:
                    break
                # 使用基类的智能解码方法，确保不乱码
                decoded_line = self._decode_output(line)
                # 通过回调发送实时输出
                if output_callback:
                    output_callback(decoded_line)
        except Exception as e:
            print(f"[WindowsRunCommandTool] Error reading {stream_name}: {e}")
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行命令 - Windows版本
        
        Args:
            params: 工具参数，包含 command, requires_approval, workspace, output_callback 字段
            
        Returns:
            命令执行结果
        """
        command = params.get("command", "")
        requires_approval = params.get("requires_approval", False)
        workspace = params.get("workspace")  # 获取workspace路径
        output_callback = params.get("output_callback")  # 实时输出回调
        
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
            # 先切换到UTF-8代码页，避免GBK编码导致乱码
            full_command = ["powershell", "-Command", f"chcp 65001 > $null; {command}"]
            
            # 使用 Popen 进行实时输出捕获
            process = subprocess.Popen(
                full_command,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=workspace if workspace else None  # 在workspace目录中执行命令
            )
            
            # 收集完整输出
            full_stdout = []
            full_stderr = []
            
            # 启动 stdout 读取线程
            stdout_thread = None
            if output_callback:
                stdout_thread = threading.Thread(
                    target=self._read_output_stream,
                    args=(process, 'stdout', output_callback),
                    daemon=True
                )
                stdout_thread.start()
                
                # stderr 也通过回调发送
                stderr_thread = threading.Thread(
                    target=self._read_output_stream,
                    args=(process, 'stderr', output_callback),
                    daemon=True
                )
                stderr_thread.start()
            
            # 等待进程完成
            try:
                process.wait(timeout=120)
            except subprocess.TimeoutExpired:
                process.kill()
                return {"error": "命令执行超时"}
            
            # 如果没有实时回调，手动收集输出
            if not output_callback:
                for line in process.stdout:
                    if line:
                        full_stdout.append(line)
                for line in process.stderr:
                    if line:
                        full_stderr.append(line)
            else:
                # 等待读取线程完成
                if stdout_thread:
                    stdout_thread.join(timeout=1)
                # 收集剩余输出
                remaining_stdout, remaining_stderr = process.communicate()
                if remaining_stdout:
                    full_stdout.append(remaining_stdout)
                if remaining_stderr:
                    full_stderr.append(remaining_stderr)
            
            stdout_text = ''.join(full_stdout)
            stderr_text = ''.join(full_stderr)
            
            command_id = f"cmd_{id(command)}"
            self.commands[command_id] = {
                "command": command,
                "status": "completed",
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "workspace": workspace
            }
            
            return {
                "command_id": command_id,
                "command": command,
                "status": "completed",
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "success": process.returncode == 0,
                "workspace": workspace
            }
        except subprocess.TimeoutExpired:
            return {"error": "命令执行超时"}
        except Exception as e:
            return {"error": str(e)}
