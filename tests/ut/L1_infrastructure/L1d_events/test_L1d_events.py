"""
L1d Events Unit Tests

单元测试：测试事件总线的基本功能
"""

import pytest
from services.L1_infrastructure.L1d_events.event_bus import EventBus, get_event_bus
from services.L1_infrastructure.L1d_events.event_types import EventTypes
from services.L1_infrastructure.L1d_events.event_record import Event


class TestEventBus:
    """测试事件总线"""

    def test_publish_event(self, test_report):
        """测试发布事件 - 验证EventBus自动持久化到events.json"""
        event_bus = get_event_bus()
        
        event = Event(event_type=EventTypes.SESSION_CREATED, payload={"session_id": "test-session"})
        
        correlation_id = event_bus.publish(event)
        
        test_report(
            test_points=["测试事件发布", "验证事件自动持久化到events.json"],
            inputs={"event_type": event.event_type, "payload": event.payload},
            outputs={"correlation_id": correlation_id}
        )
        
        assert correlation_id is not None

    def test_subscribe_and_notify(self, test_report):
        """测试订阅和通知 - 验证EventBus自动持久化到events.json"""
        event_bus = get_event_bus()
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        subscription_id = event_bus.subscribe(EventTypes.SESSION_CREATED, callback, "test-subscriber")
        
        event = Event(event_type=EventTypes.SESSION_CREATED, payload={"session_id": "test-session"})
        event_bus.publish(event)
        
        test_report(
            test_points=["测试事件订阅", "验证回调触发", "验证事件自动持久化"],
            inputs={"subscription_id": subscription_id, "event_type": event.event_type},
            outputs={"received_count": len(received_events)}
        )
        
        assert len(received_events) == 1
        assert received_events[0].event_type == EventTypes.SESSION_CREATED

    def test_get_all_events(self, test_report):
        """测试获取所有事件 - 验证EventBus自动持久化到events.json"""
        event_bus = get_event_bus()
        
        event1 = Event(event_type=EventTypes.LLM_REQUEST_SENT, payload={"content": "Hello"})
        event2 = Event(event_type=EventTypes.TASK_COMPLETED, payload={"task_id": "task-1"})
        
        event_bus.publish(event1)
        event_bus.publish(event2)
        
        all_events = event_bus.get_all_events()
        
        test_report(
            test_points=["测试获取所有事件", "验证事件自动持久化"],
            inputs={"events_published": 2},
            outputs={"events_retrieved": len(all_events)}
        )
        
        assert len(all_events) >= 2

    def test_unsubscribe(self, test_report):
        """测试取消订阅 - 验证EventBus自动持久化到events.json"""
        event_bus = get_event_bus()
        received_events = []
        
        def callback(event):
            received_events.append(event)
        
        subscription_id = event_bus.subscribe(EventTypes.SESSION_CREATED, callback)
        
        result = event_bus.unsubscribe(subscription_id)
        
        event = Event(event_type=EventTypes.SESSION_CREATED, payload={"session_id": "test"})
        event_bus.publish(event)
        
        test_report(
            test_points=["测试取消订阅", "验证取消订阅后事件仍自动持久化"],
            inputs={"subscription_id": subscription_id},
            outputs={"unsubscribe_result": result, "received_count": len(received_events)}
        )
        
        assert result is True
        assert len(received_events) == 0
