"""
L1 System Tests - UI Scenarios

测试系统基础功能和UI场景集成。
"""

def test_system_info():
    """测试系统信息获取"""
    import platform
    import sys
    
    # 验证系统信息
    assert platform.system() in ['Windows', 'Linux', 'Darwin']
    assert sys.version_info >= (3, 8)
    
    print(f"✅ 系统信息: {platform.system()} {platform.release()}")
    print(f"✅ Python版本: {sys.version}")


def test_event_bus_available():
    """测试事件总线可用性"""
    from services.L1_infrastructure.L1d_events import get_event_bus
    
    bus = get_event_bus()
    assert bus is not None
    print("✅ 事件总线可用")


def test_storage_available():
    """测试存储服务可用性"""
    from services.L1_infrastructure.L1b_persistence import get_storage
    
    storage = get_storage()
    assert storage is not None
    print("✅ 存储服务可用")


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
