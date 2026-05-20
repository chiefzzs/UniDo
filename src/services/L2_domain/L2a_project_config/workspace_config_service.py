"""
L2a Project and Configuration Management - Workspace Config Service

工作区配置管理服务：负责工作区配置的创建、查询、更新、删除
"""

import uuid
import os
from datetime import datetime
from typing import List, Optional

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory

from .models import WorkspaceConfig


class WorkspaceConfigService:
    def __init__(self, persistence_service=None):
        self.persistence = persistence_service or StorageFactory.create()
        # 项目根目录（相对于当前文件的路径）
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

    def _generate_id(self) -> str:
        return f"ws-config-{uuid.uuid4().hex[:12]}"
    
    def _resolve_path(self, root_path: str) -> str:
        """
        解析路径：如果是相对路径，转换为相对于项目根目录的绝对路径
        """
        # 如果已经是绝对路径，直接返回
        if os.path.isabs(root_path):
            return root_path
        
        # 否则，将相对路径转换为绝对路径（相对于项目根目录）
        absolute_path = os.path.abspath(os.path.join(self.project_root, root_path))
        return absolute_path
    
    def _ensure_directory_exists(self, path: str) -> bool:
        """
        确保目录存在，如果不存在则创建
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                return True
            return True
        except Exception as e:
            print(f"创建目录失败: {e}")
            return False

    def create_workspace_config(self, name: str, root_path: str, type: str = "local", encoding: str = "utf-8", excluded_patterns: List[str] = None) -> WorkspaceConfig:
        # 解析路径（支持相对路径）
        resolved_path = self._resolve_path(root_path)
        
        # 确保目录存在
        self._ensure_directory_exists(resolved_path)
        
        config = WorkspaceConfig(
            config_id=self._generate_id(),
            name=name,
            root_path=resolved_path,
            type=type,
            encoding=encoding,
            excluded_patterns=excluded_patterns or []
        )
        self.persistence.save('workspace_configs', config.to_dict())
        return config

    def get_workspace_config(self, config_id: str) -> Optional[WorkspaceConfig]:
        all_configs = self.persistence.list('workspace_configs')
        for c in all_configs:
            if c.get('config_id') == config_id:
                return WorkspaceConfig.from_dict(c)
        return None

    def update_workspace_config(self, config_id: str, **kwargs) -> Optional[WorkspaceConfig]:
        all_configs = self.persistence.list('workspace_configs')
        for i, c in enumerate(all_configs):
            if c.get('config_id') == config_id:
                # 如果更新了 root_path，需要解析相对路径并确保目录存在
                if 'root_path' in kwargs:
                    kwargs['root_path'] = self._resolve_path(kwargs['root_path'])
                    self._ensure_directory_exists(kwargs['root_path'])
                
                c.update(kwargs)
                c['updated_at'] = datetime.now().isoformat()
                all_configs[i] = c
                self.persistence.save('workspace_configs', c)
                return WorkspaceConfig.from_dict(c)
        return None

    def delete_workspace_config(self, config_id: str) -> bool:
        all_configs = self.persistence.list('workspace_configs')
        new_configs = [c for c in all_configs if c.get('config_id') != config_id]
        if len(new_configs) == len(all_configs):
            return False

        for c in all_configs:
            if c.get('config_id') == config_id:
                self.persistence._write_all('workspace_configs', new_configs)
                return True
        return False

    def list_workspace_configs(self) -> List[WorkspaceConfig]:
        all_configs = self.persistence.list('workspace_configs')
        return [WorkspaceConfig.from_dict(c) for c in all_configs]
