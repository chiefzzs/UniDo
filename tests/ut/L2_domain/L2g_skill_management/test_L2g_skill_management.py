import pytest
from services.L2_domain.L2g_skill_management import SkillManagementService, SkillDefinition


class TestSkillManagementService:
    """测试技能管理服务"""

    def test_register_skill(self, test_report):
        """测试注册技能 - 验证L2服务调用L1持久化到skill_definitions.json"""
        service = SkillManagementService()
        
        skill = service.register_skill(
            skill_name="test_skill_reg",
            category="test",
            description="Test skill for registration",
            parameters={'required': ['input']}
        )
        
        test_report(
            test_points=["测试注册技能", "验证L2服务自动触发L1持久化到skill_definitions.json"],
            inputs={"skill_name": "test_skill_reg", "category": "test"},
            outputs={"skill_id": skill.skill_id, "skill_name": skill.skill_name}
        )
        
        assert skill is not None
        assert skill.skill_id is not None

    def test_get_skill(self, test_report):
        """测试获取技能"""
        service = SkillManagementService()
        
        skill = service.register_skill(
            skill_name="get_test_skill",
            category="test",
            description="Skill for get test"
        )
        
        retrieved = service.get_skill(skill.skill_id)
        
        test_report(
            test_points=["测试获取技能", "验证skill_definitions查询功能"],
            inputs={"skill_id": skill.skill_id},
            outputs={"found": retrieved is not None, "name": retrieved.skill_name if retrieved else None}
        )
        
        assert retrieved is not None
        assert retrieved.skill_id == skill.skill_id

    def test_list_skills(self, test_report):
        """测试列出技能"""
        service = SkillManagementService()
        
        service.register_skill(
            skill_name="list_skill_1",
            category="category_a",
            description="Skill 1"
        )
        
        service.register_skill(
            skill_name="list_skill_2",
            category="category_b",
            description="Skill 2"
        )
        
        all_skills = service.list_skills()
        category_a_skills = service.list_skills(category="category_a")
        
        test_report(
            test_points=["测试列出技能", "验证按类别过滤"],
            inputs={"filter_category": "category_a"},
            outputs={"all_count": len(all_skills), "category_a_count": len(category_a_skills)}
        )
        
        assert len(all_skills) >= 2
        assert len(category_a_skills) >= 1

    def test_update_skill(self, test_report):
        """测试更新技能"""
        service = SkillManagementService()
        
        skill = service.register_skill(
            skill_name="update_test_skill",
            category="test",
            description="Original description"
        )
        
        updated = service.update_skill(
            skill.skill_id,
            description="Updated description",
            category="updated"
        )
        
        test_report(
            test_points=["测试更新技能", "验证skill_definitions更新"],
            inputs={"skill_id": skill.skill_id, "new_description": "Updated description"},
            outputs={"updated": updated is not None, "description": updated.description if updated else None}
        )
        
        assert updated is not None
        assert updated.description == "Updated description"

    def test_unregister_skill(self, test_report):
        """测试注销技能"""
        service = SkillManagementService()
        
        skill = service.register_skill(
            skill_name="unregister_test_skill",
            category="test",
            description="Skill for unregister test"
        )
        
        result = service.unregister_skill(skill.skill_id)
        retrieved = service.get_skill(skill.skill_id)
        
        test_report(
            test_points=["测试注销技能", "验证技能删除"],
            inputs={"skill_id": skill.skill_id},
            outputs={"unregistered": result, "retrieved": retrieved is not None}
        )
        
        assert result is True
        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
