"""
L2b Memory and State Management - Base Log Service

提供日志服务的基础功能，作为 API 和 WebSocket 日志服务的基类
"""

import json
import uuid
from typing import Dict, Any, Optional
from services.L1_infrastructure import get_persistence_service


class BaseLogService:
    """日志服务基类"""
    
    def __init__(self):
        self.persistence = get_persistence_service()
    
    def generate_log_id(self, prefix: str = "log") -> str:
        """生成日志ID"""
        return f"{prefix}-{uuid.uuid4().hex[:12]}"
    
    def _serialize_payload(self, payload: Any) -> Any:
        """
        序列化消息内容
        
        :param payload: 消息内容
        :return: 序列化后的内容（dict 或 str）
        """
        if payload is None:
            return None
        
        if isinstance(payload, dict):
            return payload
        elif isinstance(payload, str):
            try:
                return json.loads(payload)
            except:
                return payload
        else:
            return json.dumps(payload, ensure_ascii=False)
    
    def _save_log(self, collection: str, log_data: Dict[str, Any]) -> str:
        """
        保存日志到持久化存储
        
        :param collection: 集合名称
        :param log_data: 日志数据
        :return: 日志ID
        """
        self.persistence.save(collection, log_data)
        return log_data.get('log_id', '')
    
    def _get_logs(self, collection: str, filters: Dict[str, Any] = None) -> list:
        """
        查询日志列表
        
        :param collection: 集合名称
        :param filters: 过滤条件
        :return: 日志列表
        """
        return self.persistence.list(collection, filters or {})
    
    def _get_log(self, collection: str, log_id: str) -> Optional[Dict[str, Any]]:
        """
        查询单个日志
        
        :param collection: 集合名称
        :param log_id: 日志ID
        :return: 日志详情
        """
        logs = self.persistence.list(collection, {"log_id": log_id})
        return logs[0] if logs else None
