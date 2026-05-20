from typing import Dict, Any, List, Optional
from services.L2_domain.L2f_tool_management import ToolManagementService

class ToolConfig:
    def __init__(self):
        self.tool_management_service = ToolManagementService()
    
    def register(self, tool_data: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.tool_management_service.register_tool(
            tool_name=tool_data.get("name"),
            description=tool_data.get("description", ""),
            category=tool_data.get("category", "")
        )
        result = tool.to_dict() if tool else {}
        result["tool_name"] = tool_data.get("name")
        return result
    
    def get(self, tool_id: str) -> Optional[Dict[str, Any]]:
        tool = self.tool_management_service.get_tool(tool_id)
        return tool.to_dict() if tool else None
    
    def query(self, tool_id: str) -> Optional[Dict[str, Any]]:
        return self.get(tool_id)
    
    def update(self, tool_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        tool = self.tool_management_service.update_tool(
            tool_id=tool_id,
            **update_data
        )
        return tool.to_dict() if tool else None
    
    def list(self) -> List[Dict[str, Any]]:
        tools = self.tool_management_service.list_tools()
        return [t.to_dict() for t in tools]
    
    def unregister(self, tool_id: str) -> Dict[str, bool]:
        success = self.tool_management_service.unregister_tool(tool_id)
        return {"success": success}
