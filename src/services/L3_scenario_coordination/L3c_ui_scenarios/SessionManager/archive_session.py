from typing import Dict, Any
from services.L2_domain.L2b_memory_state.session_service import SessionService

class ArchiveSession:
    def __init__(self):
        self.session_service = SessionService()
    
    def execute(self, session_id: str) -> Dict[str, Any]:
        session = self.session_service.update_session(
            session_id=session_id,
            status="archived"
        )
        result = session.to_dict() if session else {}
        result["is_archived"] = True
        result["is_active"] = False
        return result
