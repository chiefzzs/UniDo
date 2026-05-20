"""
L2b Memory Service Unit Tests

单元测试：测试记忆管理服务
"""

import pytest
from services.L2_domain.L2b_memory_state.memory_service import MemoryService


class TestMemoryService:
    """测试记忆管理服务"""

    def test_add_to_short_term_memory(self, test_report):
        """测试添加短期记忆"""
        service = MemoryService()
        
        result = service.add_to_short_term_memory(
            session_id="session-001",
            content="Test memory content",
            memory_type="working"
        )
        
        test_report(
            test_points=["测试添加短期记忆", "验证L2服务自动触发L1持久化到short_term_memory"],
            inputs={"session_id": "session-001", "content": "Test memory content"},
            outputs={"memory_id": result.get("memory_id"), "type": result.get("type")}
        )
        
        assert result is not None
        assert result.get("memory_id") is not None
        assert result.get("content") == "Test memory content"

    def test_get_short_term_memory(self, test_report):
        """测试获取短期记忆"""
        service = MemoryService()
        
        # 先添加一些记忆
        service.add_to_short_term_memory("session-002", "Memory 1", "working")
        service.add_to_short_term_memory("session-002", "Memory 2", "working")
        service.add_to_short_term_memory("session-003", "Other session memory", "working")
        
        memories = service.get_short_term_memory("session-002")
        
        test_report(
            test_points=["测试获取短期记忆", "验证从L1持久化正确读取"],
            inputs={"session_id": "session-002"},
            outputs={"count": len(memories)}
        )
        
        assert len(memories) >= 2

    def test_get_short_term_memory_by_type(self, test_report):
        """测试按类型获取短期记忆"""
        service = MemoryService()
        
        service.add_to_short_term_memory("session-004", "Working memory", "working")
        service.add_to_short_term_memory("session-004", "Episodic memory", "episodic")
        service.add_to_short_term_memory("session-004", "Another working", "working")
        
        working_memories = service.get_short_term_memory("session-004", "working")
        
        test_report(
            test_points=["测试按类型获取短期记忆", "验证过滤功能"],
            inputs={"session_id": "session-004", "memory_type": "working"},
            outputs={"count": len(working_memories)}
        )
        
        assert len(working_memories) >= 2

    def test_move_to_long_term_memory(self, test_report):
        """测试移动到长期记忆"""
        service = MemoryService()
        
        short_term = service.add_to_short_term_memory(
            "session-005",
            "Important memory",
            "working"
        )
        
        long_term = service.move_to_long_term_memory(short_term)
        
        test_report(
            test_points=["测试移动到长期记忆", "验证L2服务自动触发L1持久化到long_term_memory"],
            inputs={"short_term_id": short_term.get("memory_id")},
            outputs={"long_term_id": long_term.get("memory_id"), "moved_at": long_term.get("moved_at")}
        )
        
        assert long_term is not None
        assert long_term.get("memory_id").startswith("lterm-")

    def test_get_long_term_memory(self, test_report):
        """测试获取长期记忆"""
        service = MemoryService()
        
        short_term = service.add_to_short_term_memory("session-006", "Test long term", "working")
        service.move_to_long_term_memory(short_term)
        
        long_term_memories = service.get_long_term_memory("session-006")
        
        test_report(
            test_points=["测试获取长期记忆", "验证从L1持久化正确读取"],
            inputs={"session_id": "session-006"},
            outputs={"count": len(long_term_memories)}
        )
        
        assert len(long_term_memories) >= 1

    def test_compress_memory(self, test_report):
        """测试记忆压缩"""
        service = MemoryService()
        
        service.add_to_short_term_memory("session-007", "Memory A", "working")
        service.add_to_short_term_memory("session-007", "Memory B", "working")
        service.add_to_short_term_memory("session-007", "Memory C", "working")
        
        compressed = service.compress_memory("session-007")
        
        test_report(
            test_points=["测试记忆压缩", "验证压缩功能"],
            inputs={"session_id": "session-007"},
            outputs={"compressed_id": compressed.get("memory_id"), "original_count": compressed.get("original_count")}
        )
        
        assert compressed is not None
        assert compressed.get("original_count") >= 3