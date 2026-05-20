import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from .file_storage import FileStorage
from .storage_factory import StorageFactory

# 延迟导入以避免循环依赖
_storage_config_service = None

def _get_storage_config_service():
    global _storage_config_service
    if _storage_config_service is None:
        from services.L1_infrastructure.L1e_storage_config import get_storage_config_service
        _storage_config_service = get_storage_config_service()
    return _storage_config_service


class PersistenceService:
    ENTITY_PREFIXES = {
        'projects': 'proj-',
        'sessions': 'sess-',
        'llm_calls': 'llm-',
        'events': 'evt-',
        'prompts': 'prompt-',
        'workspace_configs': 'ws-',
        'model_configs': 'model-',
        'tool_configs': 'tool-',
        'dialogs': 'dialog-',
        'messages': 'msg-',
        'task_groups': 'tg-',
        'tasks': 'task-',
        'tools': 'tool-',
        'skills': 'skill-',
        'auto_registration_config': 'arc-',
    }

    def __init__(self, storage: FileStorage = None):
        if storage is None:
            storage = StorageFactory.create()
        self._storage = storage
        self._storage_config = _get_storage_config_service()

    def _generate_entity_id(self, entity_type: str) -> str:
        prefix = self.ENTITY_PREFIXES.get(entity_type, 'ent-')
        return f"{prefix}{uuid.uuid4().hex[:12]}"

    def _add_timestamps(self, data: Dict[str, Any], is_new: bool = True) -> Dict[str, Any]:
        now = datetime.now().isoformat()
        if is_new:
            data['created_at'] = now
        data['updated_at'] = now
        return data

    def save(self, entity_type: str, data: Dict[str, Any]) -> str:
        """
        保存实体数据，根据存储配置决定是否持久化
        
        :param entity_type: 实体类型
        :param data: 实体数据
        :return: 实体ID（如果配置为不存储则返回空字符串）
        """
        # 检查是否需要持久化该类型
        if not self._storage_config.should_persist(entity_type):
            # 如果配置为不存储，生成ID但不实际保存
            if 'entity_id' not in data:
                return self._generate_entity_id(entity_type)
            return data.get('entity_id', '')
        
        is_new = 'entity_id' not in data or not self._storage.exists(entity_type, data.get('entity_id'))

        if is_new and 'entity_id' not in data:
            data['entity_id'] = self._generate_entity_id(entity_type)

        data = self._add_timestamps(data, is_new)
        return self._storage.save(entity_type, data)

    def load(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        return self._storage.load(entity_type, entity_id)

    def list(self, entity_type: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        return self._storage.list(entity_type, filters)

    def delete(self, entity_type: str, entity_id: str) -> bool:
        return self._storage.delete(entity_type, entity_id)

    def exists(self, entity_type: str, entity_id: str) -> bool:
        return self._storage.exists(entity_type, entity_id)

    def get_storage_path(self) -> str:
        return self._storage.get_base_path()


_persistence_service: Optional[PersistenceService] = None


def get_persistence_service() -> PersistenceService:
    global _persistence_service
    if _persistence_service is None:
        _persistence_service = PersistenceService()
    return _persistence_service
