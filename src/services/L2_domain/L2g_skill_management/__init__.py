"""
L2g Skill Management Service

L2g 技能管理服务负责管理技能的注册、配置和查询。

职责：
- 技能注册：注册新的技能及其实现
- 技能配置：管理技能的参数配置和元数据
- 技能查询：按类别、名称等条件查询技能
- 技能调度：判断技能类型并调度执行

依赖 L1 层：
- L1b 持久化服务：用于存储技能配置
- L1d 事件系统：发布技能注册事件
"""

from .skill_management import (
    SkillManagementService,
    SkillRegistry,
    SkillDefinition
)


def get_skill_management_service() -> SkillManagementService:
    """获取技能管理服务实例"""
    return SkillManagementService()


def get_skill_registry() -> SkillRegistry:
    """获取技能注册表单例"""
    return SkillRegistry.get_instance()
