from typing import Dict, Any
from services.L2_domain.L2b_memory_state.session_service import SessionService

class CreateSession:
    def __init__(self):
        self.session_service = SessionService()
    
    def execute(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        project_id = session_data.get("project_id", "")
        name = session_data.get("name", "New Session")
        session = self.session_service.create_session(
            project_id=project_id,
            name=name
        )
        return session.to_dict()
