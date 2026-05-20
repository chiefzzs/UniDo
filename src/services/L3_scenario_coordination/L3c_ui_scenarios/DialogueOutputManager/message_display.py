from typing import Dict, Any

class MessageDisplay:
    def __init__(self):
        pass
    
    def format_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "message",
            "role": message_data.get("role", "user"),
            "content": message_data.get("content", ""),
            "timestamp": message_data.get("timestamp"),
            "message_id": message_data.get("message_id")
        }
