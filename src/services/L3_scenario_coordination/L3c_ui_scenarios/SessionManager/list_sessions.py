from typing import List, Dict, Any
from services.L2_domain.L2b_memory_state.session_service import SessionService

class ListSessions:
    def __init__(self):
        self.session_service = SessionService()
    
    def execute(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        filters = filters or {}
        sessions = self.session_service.list_sessions(
            project_id=filters.get("project_id"),
            status=filters.get("status")
        )
        return [session.to_dict() for session in sessions]
