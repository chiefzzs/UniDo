import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_CONFIG = [
    {"entity_type": "projects", "persist": True, "description": "项目数据"},
    {"entity_type": "sessions", "persist": True, "description": "会话数据"},
    {"entity_type": "messages", "persist": True, "description": "消息数据"},
    {"entity_type": "dialogs", "persist": True, "description": "对话数据"},
    {"entity_type": "llm_calls", "persist": True, "description": "LLM调用记录"},
    {"entity_type": "events", "persist": True, "description": "事件记录"},
    {"entity_type": "task_groups", "persist": True, "description": "任务组数据"},
    {"entity_type": "tasks", "persist": True, "description": "任务数据"},
    {"entity_type": "workspace_configs", "persist": True, "description": "工作区配置"},
    {"entity_type": "model_configs", "persist": True, "description": "模型配置"},
    {"entity_type": "tool_configs", "persist": True, "description": "工具配置"},
    {"entity_type": "tools", "persist": True, "description": "工具定义"},
    {"entity_type": "skills", "persist": True, "description": "技能定义"},
    {"entity_type": "short_term_memory", "persist": False, "description": "短期记忆"},
    {"entity_type": "long_term_memory", "persist": True, "description": "长期记忆"},
    {"entity_type": "api_requests", "persist": True, "description": "API请求日志"},
    {"entity_type": "websocket_messages", "persist": True, "description": "WebSocket消息日志"},
]


class StorageConfigService:
    """
    存储配置服务 - 管理实体类型的持久化配置
    
    功能：
    1. 持久化服务读取配置信息，控制哪些类型要存储，哪些不存储
    2. 当遇到未知的新类型要持久化，自动追加到配置服务中，缺省是要存储的
    3. 提供CRUD操作接口
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认配置路径
            base_dir = Path(__file__).parent.parent.parent.parent
            self.config_path = base_dir / "data" / "dev" / "storage_config.json"
        else:
            self.config_path = Path(config_path)
        
        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载或初始化配置
        self._config = self._load_config()
    
    def _load_config(self) -> List[Dict[str, Any]]:
        """加载存储配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return DEFAULT_CONFIG.copy()
        else:
            # 如果配置文件不存在，创建默认配置
            self._save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: List[Dict[str, Any]]) -> None:
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def should_persist(self, entity_type: str) -> bool:
        """
        判断指定实体类型是否应该持久化
        
        如果实体类型不存在于配置中，会自动添加并返回True（缺省存储）
        """
        # 查找现有配置
        for item in self._config:
            if item['entity_type'] == entity_type:
                return item.get('persist', True)
        
        # 如果不存在，自动添加新类型，缺省为存储
        new_config = {
            "entity_type": entity_type,
            "persist": True,
            "description": f"自动发现的类型: {entity_type}",
            "auto_discovered": True,
            "discovered_at": datetime.now().isoformat()
        }
        self._config.append(new_config)
        self._save_config(self._config)
        return True
    
    def get_config(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """获取指定实体类型的配置"""
        for item in self._config:
            if item['entity_type'] == entity_type:
                return item
        return None
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """获取所有存储配置"""
        return self._config.copy()
    
    def update_config(self, entity_type: str, persist: bool, description: str = None) -> bool:
        """
        更新指定实体类型的配置
        
        :param entity_type: 实体类型
        :param persist: 是否持久化
        :param description: 描述（可选）
        :return: 是否更新成功
        """
        for item in self._config:
            if item['entity_type'] == entity_type:
                item['persist'] = persist
                if description is not None:
                    item['description'] = description
                item['updated_at'] = datetime.now().isoformat()
                self._save_config(self._config)
                return True
        return False
    
    def add_config(self, entity_type: str, persist: bool = True, description: str = "") -> Dict[str, Any]:
        """
        添加新的实体类型配置
        
        :param entity_type: 实体类型
        :param persist: 是否持久化（默认True）
        :param description: 描述
        :return: 新添加的配置项
        """
        # 检查是否已存在
        if self.get_config(entity_type):
            raise ValueError(f"Entity type '{entity_type}' already exists")
        
        new_config = {
            "entity_type": entity_type,
            "persist": persist,
            "description": description or f"自定义类型: {entity_type}",
            "created_at": datetime.now().isoformat()
        }
        self._config.append(new_config)
        self._save_config(self._config)
        return new_config
    
    def delete_config(self, entity_type: str) -> bool:
        """
        删除指定实体类型的配置
        
        :param entity_type: 实体类型
        :return: 是否删除成功
        """
        original_length = len(self._config)
        self._config = [item for item in self._config if item['entity_type'] != entity_type]
        
        if len(self._config) < original_length:
            self._save_config(self._config)
            return True
        return False
    
    def get_persist_types(self) -> List[str]:
        """获取需要持久化的实体类型列表"""
        return [item['entity_type'] for item in self._config if item.get('persist', True)]
    
    def get_non_persist_types(self) -> List[str]:
        """获取不需要持久化的实体类型列表"""
        return [item['entity_type'] for item in self._config if not item.get('persist', True)]
    
    # 以下方法用于兼容前端 API 接口
    def list(self) -> List[Dict[str, Any]]:
        """获取所有存储配置（别名）"""
        return self.list_configs()
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建存储配置"""
        entity_type = data.get('entity_type')
        if not entity_type:
            raise ValueError("entity_type is required")
        persist = data.get('persist', True)
        description = data.get('description', '')
        return self.add_config(entity_type, persist, description)
    
    def update(self, entity_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新存储配置"""
        persist = data.get('persist')
        description = data.get('description')
        if persist is not None and self.update_config(entity_type, persist, description):
            return self.get_config(entity_type)
        return None
    
    def delete(self, entity_type: str) -> Dict[str, Any]:
        """删除存储配置"""
        success = self.delete_config(entity_type)
        return {"success": success, "entity_type": entity_type}
    
    def get(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """获取指定实体类型的配置（别名）"""
        return self.get_config(entity_type)


# 全局单例
_storage_config_service: Optional[StorageConfigService] = None


def get_storage_config_service() -> StorageConfigService:
    """获取存储配置服务的单例实例"""
    global _storage_config_service
    if _storage_config_service is None:
        _storage_config_service = StorageConfigService()
    return _storage_config_service
