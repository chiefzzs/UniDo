"""
L2a Project and Configuration Management - Model Config Service

模型配置管理服务：负责模型配置的创建、查询、更新、删除
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory

from .models import ModelConfig


class ModelConfigService:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()

    def _generate_id(self) -> str:
        return f"model-config-{uuid.uuid4().hex[:12]}"

    def create_model_config(self, name: str, model_name: str, api_type: str,
                          api_address: str, api_key: str, parameters: Dict = None) -> ModelConfig:
        config = ModelConfig(
            config_id=self._generate_id(),
            name=name,
            model_name=model_name,
            api_type=api_type,
            api_address=api_address,
            api_key=api_key,
            parameters=parameters or {}
        )
        self.persistence.save('model_configs', config.to_dict())
        return config

    def get_model_config(self, config_id: str) -> Optional[ModelConfig]:
        all_configs = self.persistence.list('model_configs')
        for c in all_configs:
            if c.get('config_id') == config_id:
                return ModelConfig.from_dict(c)
        return None

    def update_model_config(self, config_id: str, **kwargs) -> Optional[ModelConfig]:
        all_configs = self.persistence.list('model_configs')
        for i, c in enumerate(all_configs):
            if c.get('config_id') == config_id:
                c.update(kwargs)
                c['updated_at'] = datetime.now().isoformat()
                all_configs[i] = c
                self.persistence.save('model_configs', c)
                return ModelConfig.from_dict(c)
        return None

    def delete_model_config(self, config_id: str) -> bool:
        all_configs = self.persistence.list('model_configs')
        new_configs = [c for c in all_configs if c.get('config_id') != config_id]
        if len(new_configs) == len(all_configs):
            return False

        for c in all_configs:
            if c.get('config_id') == config_id:
                self.persistence._write_all('model_configs', new_configs)
                return True
        return False

    def list_model_configs(self) -> List[ModelConfig]:
        all_configs = self.persistence.list('model_configs')
        return [ModelConfig.from_dict(c) for c in all_configs]
