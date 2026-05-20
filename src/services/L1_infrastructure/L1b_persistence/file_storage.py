import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional


class FileStorage:
    def __init__(self, base_path: str, env: str = "dev"):
        self.base_path = Path(base_path) / env
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.env = env

    def _get_file_path(self, entity_type: str) -> Path:
        file_name = f"{entity_type}.json"
        return self.base_path / file_name

    def _ensure_file_exists(self, file_path: Path) -> None:
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _read_all(self, entity_type: str) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(entity_type)
        self._ensure_file_exists(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _write_all(self, entity_type: str, data: List[Dict[str, Any]]) -> None:
        file_path = self._get_file_path(entity_type)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def save(self, entity_type: str, data: Dict[str, Any]) -> str:
        all_data = self._read_all(entity_type)
        
        # 根据实体类型确定主键字段
        entity_type_id_map = {
            'projects': 'project_id',
            'workspace_configs': 'config_id',
            'model_configs': 'config_id',
            'sessions': 'session_id',
            'dialogs': 'dialog_id',
            'messages': 'message_id',
            'task_groups': 'task_group_id',
            'tasks': 'task_id',
            'events': 'record_id',
            'llm_calls': 'call_id',
            'tool_calls': 'call_id',
            'short_term_memory': 'memory_id',
            'long_term_memory': 'memory_id',
            'memory_compression': 'memory_id'
        }
        
        id_field = entity_type_id_map.get(entity_type)
        
        # 如果实体类型不在映射中，使用默认的 id 字段列表
        if not id_field or id_field not in data:
            id_fields = ['entity_id', 'session_id', 'dialog_id', 'message_id', 
                        'project_id', 'config_id', 'task_id', 'task_group_id',
                        'record_id', 'call_id']
            for field_name in id_fields:
                if field_name in data:
                    id_field = field_name
                    break
        
        entity_id = data.get(id_field) if id_field else None

        if entity_id and id_field:
            for i, item in enumerate(all_data):
                if item.get(id_field) == entity_id:
                    all_data[i] = data
                    self._write_all(entity_type, all_data)
                    return entity_id

        all_data.append(data)
        self._write_all(entity_type, all_data)
        return entity_id if entity_id else ''

    def load(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        all_data = self._read_all(entity_type)
        for item in all_data:
            if item.get('entity_id') == entity_id:
                return item
        return None

    def list(self, entity_type: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        all_data = self._read_all(entity_type)
        if filters is None:
            return all_data

        result = []
        for item in all_data:
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                result.append(item)
        return result

    def delete(self, entity_type: str, entity_id: str) -> bool:
        all_data = self._read_all(entity_type)
        original_length = len(all_data)
        all_data = [item for item in all_data if item.get('entity_id') != entity_id]

        if len(all_data) < original_length:
            self._write_all(entity_type, all_data)
            return True
        return False

    def exists(self, entity_type: str, entity_id: str) -> bool:
        return self.load(entity_type, entity_id) is not None

    def get_base_path(self) -> str:
        return str(self.base_path)
