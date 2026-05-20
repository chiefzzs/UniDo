from typing import Dict, Any
from services.L2_domain.L2b_memory_state.session_service import SessionService

class UpdateSession:
    def __init__(self):
        self.session_service = SessionService()
    
    def execute(self, session_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        session = self.session_service.update_session(
            session_id=session_id,
            name=update_data.get("name")
        )
        return session.to_dict() if session else {}
