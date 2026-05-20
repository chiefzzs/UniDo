"""
L1e Storage Configuration Service - 存储配置服务

提供持久化类型配置管理，控制哪些类型需要存储，哪些不需要存储。
当遇到未知的新类型时，自动追加到配置中，缺省为存储。
"""

from .storage_config_service import StorageConfigService, get_storage_config_service

__all__ = ['StorageConfigService', 'get_storage_config_service']
