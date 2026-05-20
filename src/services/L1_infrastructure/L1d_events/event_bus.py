import uuid
import threading
from datetime import datetime
from typing import Callable, List, Optional, Dict, Any

from .event_record import Event, EventRecord
from .event_types import EventTypes
from .subscription import Subscription, SubscriptionManager


class EventBusConfig:
    """
    事件总线配置类
    """
    def __init__(self):
        # 是否启用持久化（缺省打开）
        self.persistence_enabled = True
        # 是否持久化完整的payload（缺省打开）
        self.persist_full_payload = True
        # 是否启用内存缓存
        self.memory_cache_enabled = True


class EventBus:
    _instance: Optional['EventBus'] = None
    _lock = threading.Lock()

    def __init__(self, persistence_service=None):
        self._subscription_manager = SubscriptionManager()
        self._persistence_service = persistence_service
        self._memory_cache: Dict[str, List[EventRecord]] = {}
        self._correlation_index: Dict[str, List[str]] = {}
        self._config = EventBusConfig()

    def publish(self, event: Event, correlation_id: str = None, persist: bool = None) -> str:
        """
        发布事件
        
        Args:
            event: 事件对象
            correlation_id: 关联ID，用于追踪相关事件
            persist: 是否持久化（None表示使用全局配置）
            
        Returns:
            correlation_id
        """
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        stored_at = datetime.now().isoformat()
        event_record = event.to_record(correlation_id, stored_at)

        # 根据配置决定是否缓存到内存
        if self._config.memory_cache_enabled:
            if correlation_id not in self._memory_cache:
                self._memory_cache[correlation_id] = []
            self._memory_cache[correlation_id].append(event_record)

            if correlation_id not in self._correlation_index:
                self._correlation_index[correlation_id] = []
            self._correlation_index[correlation_id].append(event_record.record_id)

        # 根据配置决定是否持久化
        should_persist = persist if persist is not None else self._config.persistence_enabled
        if should_persist and self._persistence_service:
            record_dict = event_record.to_dict()
            
            # 如果配置为不持久化完整payload，只存储关键信息
            if not self._config.persist_full_payload:
                record_dict = {
                    'record_id': record_dict.get('record_id'),
                    'event_id': record_dict.get('event_id'),
                    'event_type': record_dict.get('event_type'),
                    'timestamp': record_dict.get('timestamp'),
                    'stored_at': record_dict.get('stored_at'),
                    'correlation_id': record_dict.get('correlation_id'),
                    'entity_id': record_dict.get('entity_id'),
                    'created_at': record_dict.get('created_at'),
                    'updated_at': record_dict.get('updated_at'),
                    'payload': {
                        'source_component': record_dict.get('payload', {}).get('source_component'),
                        'source_service': record_dict.get('payload', {}).get('source_service')
                    }
                }
            
            self._persistence_service.save('events', record_dict)

        self._notify_subscribers(event, event_record)

        return correlation_id
    
    def get_config(self) -> EventBusConfig:
        """获取事件总线配置"""
        return self._config
    
    def set_config(self, config: EventBusConfig):
        """设置事件总线配置"""
        self._config = config

    def _notify_subscribers(self, event: Event, event_record: EventRecord):
        subscriptions = self._subscription_manager.get_by_type(event.event_type)
        for sub in subscriptions:
            try:
                # 尝试传递三个参数，如果回调不接受则降级为只传递event
                import inspect
                sig = inspect.signature(sub.callback)
                if len(sig.parameters) >= 3:
                    sub.callback(event, event_record, event_record.correlation_id)
                elif len(sig.parameters) >= 1:
                    sub.callback(event)
                else:
                    sub.callback()
            except Exception as e:
                print(f"Error in event callback: {e}")

    def subscribe(self, event_type: str, callback: Callable, subscriber_name: str = '') -> str:
        subscription = Subscription.create(event_type, callback, subscriber_name)
        return self._subscription_manager.add(subscription)

    def unsubscribe(self, subscription_id: str) -> bool:
        return self._subscription_manager.remove(subscription_id)

    def get_events_by_correlation(self, correlation_id: str) -> List[EventRecord]:
        records = []
        if correlation_id in self._memory_cache:
            records.extend(self._memory_cache[correlation_id])

        if self._persistence_service:
            stored_records = self._persistence_service.list('events', {'correlation_id': correlation_id})
            for data in stored_records:
                record = EventRecord.from_dict(data)
                if record not in records:
                    records.append(record)

        return records

    def get_events_by_type(self, event_type: str) -> List[EventRecord]:
        records = []
        for correlation_id, cache in self._memory_cache.items():
            for record in cache:
                if record.event_type == event_type:
                    records.append(record)

        if self._persistence_service:
            stored_records = self._persistence_service.list('events', {'event_type': event_type})
            for data in stored_records:
                record = EventRecord.from_dict(data)
                if record not in records:
                    records.append(record)

        return records

    def clear_cache(self):
        self._memory_cache.clear()
        self._correlation_index.clear()
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """获取所有事件（从内存和持久化）"""
        all_events = []
        seen_record_ids = set()
        
        # 从内存缓存获取
        for correlation_id, cache in self._memory_cache.items():
            for record in cache:
                if record.record_id not in seen_record_ids:
                    all_events.append(record.to_dict())
                    seen_record_ids.add(record.record_id)
        
        # 从持久化存储获取
        if self._persistence_service:
            try:
                stored_records = self._persistence_service.list('events')
                for data in stored_records:
                    record_id = data.get('record_id')
                    if record_id and record_id not in seen_record_ids:
                        all_events.append(data)
                        seen_record_ids.add(record_id)
            except Exception as e:
                print(f"Error loading events from persistence: {e}")
        
        return all_events

    @classmethod
    def get_instance(cls) -> 'EventBus':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def set_persistence_service(cls, persistence_service):
        if cls._instance is None:
            cls._instance = cls(persistence_service)
        else:
            cls._instance._persistence_service = persistence_service

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            if cls._instance:
                cls._instance._subscription_manager.clear()
                cls._instance._memory_cache.clear()
                cls._instance._correlation_index.clear()
            cls._instance = None


def get_event_bus() -> EventBus:
    return EventBus.get_instance()
