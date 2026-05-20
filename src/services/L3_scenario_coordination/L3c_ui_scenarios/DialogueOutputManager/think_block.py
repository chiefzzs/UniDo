from typing import Dict, Any

class ThinkBlock:
    def __init__(self):
        pass
    
    def format_thinking(self, thinking_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "thinking",
            "content": thinking_data.get("content", ""),
            "tool_info": thinking_data.get("tool_info", {}),
            "is_visible": thinking_data.get("is_visible", True)
        }
