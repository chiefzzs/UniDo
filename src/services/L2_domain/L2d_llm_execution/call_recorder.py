"""
L2d LLM Execution Service - Call Recorder

调用记录器，负责LLM调用记录的存储和查询。
"""

import threading
from typing import List, Optional, Dict
from .interfaces import LoopbackStore
from .models import LLMCallRecord
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory


class CallRecorder:
    """LLM调用记录器"""
    
    def __init__(self, persistence_service=None):
        self._persistence = persistence_service or StorageFactory.create()
        self._mode = 'record'
    
    def set_mode(self, mode: str):
        """设置记录模式"""
        self._mode = mode
    
    def save(self, record: LLMCallRecord):
        """保存调用记录（回放模式不保存）"""
        if self._mode == 'loopback':
            return
        self._persistence.save('llm_calls', record.to_dict())
    
    def get(self, call_id: str) -> Optional[LLMCallRecord]:
        """获取调用记录"""
        all_records = self._persistence.list('llm_calls')
        for r in all_records:
            if r.get('call_id') == call_id:
                return LLMCallRecord.from_dict(r)
        return None
    
    def list(self, dialog_id: str = None, limit: int = 100) -> List[LLMCallRecord]:
        """列出调用记录"""
        all_records = self._persistence.list('llm_calls')
        result = [LLMCallRecord.from_dict(r) for r in all_records]
        
        if dialog_id:
            result = [r for r in result if r.dialog_id == dialog_id]
        
        result.sort(key=lambda x: x.created_at, reverse=True)
        return result[:limit]


class PersistenceLoopbackStore(LoopbackStore):
    """基于持久化服务的回放数据存储"""
    
    def __init__(self, persistence_service=None):
        """
        初始化回放存储
        
        Args:
            persistence_service: 持久化服务实例，默认使用 StorageFactory
        """
        self._persistence = persistence_service or StorageFactory.create()
        self._records: List[Dict] = []
        self._index = 0
        self._loaded = False
        self._lock = threading.Lock()
    
    def load(self) -> List[Dict]:
        """从持久化服务加载回放数据"""
        try:
            all_records = self._persistence.list('llm_calls')
            
            if not all_records:
                print(f"❌ 未找到任何LLM调用记录")
                return []
            
            self._records = all_records
            self._loaded = True
            self._index = 0
            
            print(f"✅ 已加载 {len(self._records)} 条LLM调用记录用于回放")
            return self._records
            
        except Exception as e:
            print(f"❌ 加载回放数据失败：{e}")
            return []
    
    def get_next(self) -> Optional[Dict]:
        """获取下一条记录"""
        with self._lock:
            if not self._loaded:
                self.load()
            
            if self._index < len(self._records):
                record = self._records[self._index]
                self._index += 1
                return record
        return None
    
    def reset(self):
        """重置索引"""
        with self._lock:
            self._index = 0
    
    @property
    def has_more(self) -> bool:
        """是否还有更多记录"""
        if not self._loaded:
            self.load()
        return self._index < len(self._records)
