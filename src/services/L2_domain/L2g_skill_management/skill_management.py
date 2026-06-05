"""
L2g Skill Management Service - Implementation

技能管理服务负责管理技能的注册、配置和查询。
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes


@dataclass
class SkillDefinition:
    skill_id: str
    skill_name: str
    category: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    skill_type: str = "native"
    timeout: float = 60.0
    retry_config: Dict[str, Any] = field(default_factory=dict)
    is_async: bool = False
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillDefinition':
        return cls(**data)


class SkillRegistry:
    _instance = None
    _skills: Dict[str, SkillDefinition] = {}
    _implementations: Dict[str, Callable] = {}

    @classmethod
    def get_instance(cls) -> 'SkillRegistry':
        if cls._instance is None:
            cls._instance = SkillRegistry()
        return cls._instance

    def register_skill(self, skill: SkillDefinition, implementation: Callable = None):
        self._skills[skill.skill_id] = skill
        if skill.skill_name:
            self._skills[f"name:{skill.skill_name}"] = skill
        if implementation:
            self._implementations[skill.skill_id] = implementation

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self._skills.get(skill_id) or self._skills.get(f"name:{skill_id}")

    def get_implementation(self, skill_id: str) -> Optional[Callable]:
        return self._implementations.get(skill_id)

    def list_skills(self, category: str = None) -> List[SkillDefinition]:
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if s.category == category]
        unique_skills = []
        seen_ids = set()
        for s in skills:
            if s.skill_id not in seen_ids and not s.skill_id.startswith('name:'):
                seen_ids.add(s.skill_id)
                unique_skills.append(s)
        return unique_skills

    def unregister_skill(self, skill_id: str):
        skill = self._skills.get(skill_id)
        if skill:
            self._skills.pop(skill_id, None)
            self._skills.pop(f"name:{skill.skill_name}", None)
            self._implementations.pop(skill_id, None)


class SkillManagementService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()
        self.registry = SkillRegistry.get_instance()

    def _generate_id(self) -> str:
        return f"skill-{uuid.uuid4().hex[:12]}"

    def register_skill(self, skill_name: str, category: str, description: str,
                     parameters: Dict = None, skill_type: str = "native",
                     timeout: float = 60.0, is_async: bool = False,
                     implementation: Callable = None) -> SkillDefinition:
        skill = SkillDefinition(
            skill_id=self._generate_id(),
            skill_name=skill_name,
            category=category,
            description=description,
            parameters=parameters or {},
            skill_type=skill_type,
            timeout=timeout,
            is_async=is_async
        )

        self.registry.register_skill(skill, implementation)
        self.persistence.save('skill_definitions', skill.to_dict())

        self.event_bus.publish(Event(
            event_type=EventTypes.SKILL_REGISTERED,
            payload={'skill_id': skill.skill_id, 'skill_name': skill.skill_name}
        ))

        return skill

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        skill = self.registry.get_skill(skill_id)
        if skill:
            return skill

        all_skills = self.persistence.list('skill_definitions')
        for s in all_skills:
            if s.get('skill_id') == skill_id:
                return SkillDefinition.from_dict(s)
        return None

    def get_skill_implementation(self, skill_id: str) -> Optional[Callable]:
        return self.registry.get_implementation(skill_id)

    def list_skills(self, category: str = None) -> List[SkillDefinition]:
        registered_skills = self.registry.list_skills(category=category)

        if not registered_skills and category is None:
            all_skills = self.persistence.list('skill_definitions')
            return [SkillDefinition.from_dict(s) for s in all_skills]

        return registered_skills

    def update_skill(self, skill_id: str, **kwargs) -> Optional[SkillDefinition]:
        all_skills = self.persistence.list('skill_definitions')
        for i, s in enumerate(all_skills):
            if s.get('skill_id') == skill_id:
                s.update(kwargs)
                s['updated_at'] = datetime.now().isoformat()
                all_skills[i] = s
                self.persistence.save('skill_definitions', s)

                skill_def = SkillDefinition.from_dict(s)
                self.registry.register_skill(skill_def)

                return skill_def
        return None

    def unregister_skill(self, skill_id: str) -> bool:
        skill = self.get_skill(skill_id)
        if not skill:
            return False

        self.registry.unregister_skill(skill_id)

        all_skills = self.persistence.list('skill_definitions')
        new_skills = [s for s in all_skills if s.get('skill_id') != skill_id]
        self.persistence._write_all('skill_definitions', new_skills)

        self.event_bus.publish(Event(
            event_type=EventTypes.SKILL_UNREGISTERED,
            payload={'skill_id': skill_id}
        ))

        return True
