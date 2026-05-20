from typing import Dict, Any
from services.L2_domain.L2b_memory_state.session_service import SessionService

class DeleteSession:
    def __init__(self):
        self.session_service = SessionService()
    
    def execute(self, session_id: str) -> Dict[str, Any]:
        success = self.session_service.delete_session(session_id)
        return {"success": success, "session_id": session_id}
