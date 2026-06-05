"""
Event Console Printer

事件控制台打印服务：
- 订阅 EventBus 所有事件
- 将事件打印到控制台
- 支持配置过滤某些事件（可选）

架构层级：L1 基础设施层
"""

import json
from typing import Set, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConsolePrinterConfig:
    """控制台打印配置"""
    enabled: bool = True
    exclude_event_types: Set[str] = field(default_factory=set)
    show_payload: bool = True
    show_correlation_id: bool = True
    show_timestamp: bool = True


class EventConsolePrinter:
    """
    事件控制台打印服务
    
    订阅 EventBus 并将事件打印到控制台
    """
    
    def __init__(self, config: Optional[ConsolePrinterConfig] = None):
        self.config = config or ConsolePrinterConfig()
        self._event_bus = None
        self._initialized = False
    
    def initialize(self, event_bus):
        """
        初始化并订阅事件总线
        
        Args:
            event_bus: EventBus 实例
        """
        if self._initialized:
            return
        
        self._event_bus = event_bus
        
        # 订阅所有事件（使用 '*' 通配符）
        self._event_bus.subscribe('*', self._on_event, 'event_console_printer')
        self._initialized = True
        print("[PASS] EventConsolePrinter initialized, listening to all events")
    
    def _on_event(self, event, event_record, correlation_id: str):
        """
        事件回调处理
        
        Args:
            event: Event 对象
            event_record: EventRecord 对象
            correlation_id: 关联ID
        """
        if not self.config.enabled:
            return
        
        event_type = event.event_type
        
        # 检查是否排除
        if event_type in self.config.exclude_event_types:
            return
        
        # 构建打印内容
        output_parts = []
        
        # 前缀
        output_parts.append(f"[CONSOLE-PRINT] Event received")
        
        # 事件类型
        output_parts.append(f"type={event_type}")
        
        # 关联ID
        if self.config.show_correlation_id and correlation_id:
            output_parts.append(f"corr_id={correlation_id[:12]}...")
        
        # 时间戳
        if self.config.show_timestamp and hasattr(event, 'timestamp'):
            if isinstance(event.timestamp, datetime):
                ts_str = event.timestamp.strftime("%H:%M:%S.%f")[:-3]
                output_parts.append(f"time={ts_str}")
            else:
                output_parts.append(f"time={str(event.timestamp)}")
        
        # 源信息
        if hasattr(event, 'source_service') and event.source_service:
            output_parts.append(f"from={event.source_service}")
        
        # 打印
        print(" ".join(output_parts))
        
        # 打印载荷
        if self.config.show_payload and hasattr(event, 'payload') and event.payload:
            try:
                payload_str = json.dumps(event.payload, ensure_ascii=False, indent=2)
                print(f"   payload:\n{payload_str}")
            except Exception:
                print(f"   payload: {event.payload}")
    
    def add_excluded_event(self, event_type: str):
        """添加要排除的事件类型"""
        self.config.exclude_event_types.add(event_type)
    
    def remove_excluded_event(self, event_type: str):
        """移除排除的事件类型"""
        self.config.exclude_event_types.discard(event_type)
    
    def enable(self):
        """启用打印"""
        self.config.enabled = True
    
    def disable(self):
        """禁用打印"""
        self.config.enabled = False


# 全局单例
_printer_instance: Optional[EventConsolePrinter] = None


def get_event_console_printer() -> EventConsolePrinter:
    """获取事件控制台打印器单例"""
    global _printer_instance
    if _printer_instance is None:
        _printer_instance = EventConsolePrinter()
    return _printer_instance
