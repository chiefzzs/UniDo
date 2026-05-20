"""
L2b Memory and State Management - Memory Service

记忆管理服务：负责短期记忆、长期记忆和记忆压缩
"""

import uuid
from datetime import datetime
from typing import List, Dict

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory


class MemoryService:
    """
    Memory management service for handling short-term and long-term memory.
    """

    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def add_to_short_term_memory(self, session_id: str, content: str, memory_type: str = "working") -> Dict:
        memory_entry = {
            'memory_id': f"mem-{uuid.uuid4().hex[:12]}",
            'session_id': session_id,
            'type': memory_type,
            'content': content,
            'created_at': datetime.now().isoformat()
        }
        self.persistence.save('short_term_memory', memory_entry)
        return memory_entry

    def get_short_term_memory(self, session_id: str, memory_type: str = None) -> List[Dict]:
        all_memory = self.persistence.list('short_term_memory')
        result = [m for m in all_memory if m.get('session_id') == session_id]

        if memory_type:
            result = [m for m in result if m.get('type') == memory_type]

        return result

    def move_to_long_term_memory(self, memory_entry: Dict) -> Dict:
        long_term_entry = {
            **memory_entry,
            'memory_id': f"lterm-{uuid.uuid4().hex[:12]}",
            'moved_at': datetime.now().isoformat()
        }
        self.persistence.save('long_term_memory', long_term_entry)
        return long_term_entry

    def get_long_term_memory(self, session_id: str) -> List[Dict]:
        all_memory = self.persistence.list('long_term_memory')
        return [m for m in all_memory if m.get('session_id') == session_id]

    def compress_memory(self, session_id: str) -> Dict:
        st_memory = self.get_short_term_memory(session_id)
        compressed = {
            'memory_id': f"comp-{uuid.uuid4().hex[:12]}",
            'session_id': session_id,
            'original_count': len(st_memory),
            'compressed_summary': f"Compressed {len(st_memory)} memory entries",
            'compressed_at': datetime.now().isoformat()
        }
        self.persistence.save('memory_compression', compressed)
        return compressed
