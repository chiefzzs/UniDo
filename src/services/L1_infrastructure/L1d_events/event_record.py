import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:12]}")
    event_type: str = ''
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    source_component: str = ''
    source_service: str = ''

    def to_record(self, correlation_id: str = None, stored_at: str = None) -> 'EventRecord':
        return EventRecord(
            record_id=f"rec-{uuid.uuid4().hex[:12]}",
            event_id=self.event_id,
            event_type=self.event_type,
            timestamp=self.timestamp.isoformat(),
            payload=self.payload,
            stored_at=stored_at or datetime.now().isoformat(),
            source_component=self.source_component,
            source_service=self.source_service,
            correlation_id=correlation_id or ''
        )


@dataclass
class EventRecord:
    record_id: str
    event_id: str
    event_type: str
    timestamp: str
    payload: Dict[str, Any]
    stored_at: str
    source_component: str
    source_service: str
    correlation_id: str = ''

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventRecord':
        return cls(
            record_id=data.get('record_id', ''),
            event_id=data.get('event_id', ''),
            event_type=data.get('event_type', ''),
            timestamp=data.get('timestamp', ''),
            payload=data.get('payload', {}),
            stored_at=data.get('stored_at', ''),
            source_component=data.get('source_component', ''),
            source_service=data.get('source_service', ''),
            correlation_id=data.get('correlation_id', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'record_id': self.record_id,
            'event_id': self.event_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'stored_at': self.stored_at,
            'source_component': self.source_component,
            'source_service': self.source_service,
            'correlation_id': self.correlation_id
        }
