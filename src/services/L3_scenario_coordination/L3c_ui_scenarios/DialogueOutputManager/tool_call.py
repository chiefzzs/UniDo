from typing import Dict, Any

class ToolCall:
    def __init__(self):
        pass
    
    def format_tool_call(self, tool_call_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "tool_call",
            "tool_name": tool_call_data.get("tool_name", ""),
            "parameters": tool_call_data.get("parameters", {}),
            "result": tool_call_data.get("result", ""),
            "status": tool_call_data.get("status", "pending")
        }
