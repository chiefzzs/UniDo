"""
EventWebSocketPlugin - WebSocket事件订阅插件

订阅 EventBus 并将事件推送到所有WebSocket连接。
"""

from .event_websocket_plugin import EventWebSocketPlugin, get_websocket_plugin

__all__ = ['EventWebSocketPlugin', 'get_websocket_plugin']
