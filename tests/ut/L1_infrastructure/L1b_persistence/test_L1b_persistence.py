"""
L1b Persistence Service Unit Tests

单元测试：测试持久化服务的基本功能
"""

import pytest
from services.L1_infrastructure.L1b_persistence.persistence_service import PersistenceService
from services.L1_infrastructure.L1b_persistence.file_storage import FileStorage
from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory


class TestPersistenceService:
    """测试持久化服务"""

    def test_save_and_load(self, test_report):
        """测试保存和加载数据"""
        service = PersistenceService()

        inputs = {
            "entity_type": "projects",
            "data": {
                "name": "Test Project",
                "description": "A test project"
            }
        }

        entity_id = service.save(inputs["entity_type"], inputs["data"])
        loaded_data = service.load(inputs["entity_type"], entity_id)

        test_report(
            test_points=["测试保存和加载功能"],
            inputs=inputs,
            outputs={
                "entity_id": entity_id,
                "loaded_data": loaded_data
            }
        )

        assert entity_id is not None
        assert loaded_data is not None
        assert loaded_data["name"] == inputs["data"]["name"]

    def test_list_entities(self, test_report):
        """测试列出实体"""
        service = PersistenceService()

        inputs = {
            "entity_type": "sessions",
            "data": {
                "name": "Test Session"
            }
        }

        service.save(inputs["entity_type"], inputs["data"])
        entities = service.list(inputs["entity_type"])

        test_report(
            test_points=["测试列表功能"],
            inputs=inputs,
            outputs={
                "entity_count": len(entities)
            }
        )

        assert len(entities) > 0


class TestFileStorage:
    """测试文件存储"""

    def test_storage_factory(self, test_report):
        """测试存储工厂 - 通过PersistenceService验证持久化"""
        # 使用PersistenceService（内部使用StorageFactory）来测试
        service = PersistenceService()
        
        # 使用projects类型（会被TestDataCollector收集）
        test_data = {
            "name": "Factory Test Project",
            "description": "Created via storage factory"
        }
        entity_id = service.save("projects", test_data)
        loaded_data = service.load("projects", entity_id)
        
        storage = StorageFactory.create()

        test_report(
            test_points=["测试存储工厂创建", "验证工厂创建的存储可持久化数据"],
            inputs={},
            outputs={
                "storage_type": type(storage).__name__,
                "base_path": storage.get_base_path(),
                "entity_id": entity_id,
                "data_saved": loaded_data is not None
            }
        )

        assert storage is not None
        assert isinstance(storage, FileStorage)
        assert loaded_data is not None
        assert loaded_data["name"] == "Factory Test Project"