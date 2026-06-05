"""
L2b Memory and State Management - Session Service

会话管理服务：负责会话的创建、查询、更新、删除
"""

from datetime import datetime
from typing import List, Optional

from services.L1_infrastructure.L1a_id_generator.id_generator import generate_session_id
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes

from .models import Session


class SessionService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()

    def create_session(self, project_id: str, name: str, session_id: str = None) -> Session:
        session = Session(
            session_id=session_id or generate_session_id(),
            project_id=project_id,
            name=name
        )
        self.persistence.save('sessions', session.to_dict())

        if self.event_bus:
            self.event_bus.publish(Event(
                event_type=EventTypes.SESSION_CREATED,
                payload={'session_id': session.session_id, 'project_id': project_id}
            ))

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        all_sessions = self.persistence.list('sessions')
        for s in all_sessions:
            if s.get('session_id') == session_id:
                return Session.from_dict(s)
        return None

    def update_session(self, session_id: str, **kwargs) -> Optional[Session]:
        all_sessions = self.persistence.list('sessions')
        for i, s in enumerate(all_sessions):
            if s.get('session_id') == session_id:
                s.update(kwargs)
                s['updated_at'] = datetime.now().isoformat()
                all_sessions[i] = s
                self.persistence.save('sessions', s)
                return Session.from_dict(s)
        return None

    def delete_session(self, session_id: str) -> bool:
        all_sessions = self.persistence.list('sessions')
        for s in all_sessions:
            if s.get('session_id') == session_id:
                new_sessions = [s for s in all_sessions if s.get('session_id') != session_id]
                self.persistence._write_all('sessions', new_sessions)

                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type=EventTypes.SESSION_DELETED,
                        payload={'session_id': session_id}
                    ))
                return True
        return False

    def list_sessions(self, project_id: str = None, status: str = None) -> List[Session]:
        all_sessions = self.persistence.list('sessions')
        result = [Session.from_dict(s) for s in all_sessions]

        if project_id:
            result = [s for s in result if s.project_id == project_id]
        if status:
            result = [s for s in result if s.status == status]

        return result
