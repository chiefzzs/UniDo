"""
L2h Prompt Management Service

提供提示词模板的 CRUD 操作、版本管理和变量替换功能。

职责：
- 提示词模板的 CRUD 操作
- 提示词版本管理
- 提示词模板变量替换
- 为 L2a message 提供提示词关联功能
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from services.L1_infrastructure.L1b_persistence import PersistenceService
from services.L1_infrastructure.L1d_events import EventBus, Event
from services.L1_infrastructure.L1a_id_generator import generate_prompt_id, generate_version_id


@dataclass
class PromptVariable:
    """提示词变量定义"""
    name: str
    default_value: Optional[str] = None
    description: str = ""
    required: bool = False


@dataclass
class Prompt:
    """提示词模板数据类"""
    prompt_id: str
    name: str
    category: str
    content: str
    version: str = "1.0"
    variables: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    content_path: str = ""


@dataclass
class PromptVersion:
    """提示词版本数据类"""
    version_id: str
    prompt_id: str
    version: str
    content: str
    change_description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"


class PromptManagementService:
    """
    提示词管理服务
    
    负责提示词模板的管理，包括创建、读取、更新、删除和版本管理。
    """
    
    def __init__(self, persistence_service: PersistenceService = None, event_bus: EventBus = None):
        self._persistence = persistence_service or PersistenceService()
        self._event_bus = event_bus or EventBus.get_instance()
        self._prompts: Dict[str, Prompt] = {}
        self._versions: Dict[str, List[PromptVersion]] = {}
        self._load_prompts()
    
    def _load_prompts(self):
        """从持久化存储加载所有提示词"""
        try:
            # 加载提示词列表
            prompts_list = self._persistence.list('prompts')
            for prompt_data in prompts_list:
                # 如果数据中有 content_path，从文件加载内容
                if 'content_path' in prompt_data and not prompt_data.get('content'):
                    content = self._load_content_from_file(prompt_data['content_path'])
                    prompt_data['content'] = content
                
                prompt = Prompt(**prompt_data)
                self._prompts[prompt.prompt_id] = prompt
            
            # 加载版本历史
            versions_list = self._persistence.list('prompt_versions')
            for version_data in versions_list:
                version = PromptVersion(**version_data)
                if version.prompt_id not in self._versions:
                    self._versions[version.prompt_id] = []
                self._versions[version.prompt_id].append(version)
            
            print(f"✅ PromptManagementService: 已加载 {len(self._prompts)} 个提示词")
        except Exception as e:
            print(f"❌ PromptManagementService: 加载提示词失败: {e}")
    
    def _load_content_from_file(self, content_path: str) -> str:
        """从文件路径加载提示词内容"""
        try:
            # 构建完整路径：src/data/prompt/{content_path}
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            full_path = os.path.join(base_path, 'data', 'prompt', content_path)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ 加载提示词文件失败 {content_path}: {e}")
            return ""
    
    def _save_prompts(self):
        """保存所有提示词到持久化存储"""
        for prompt in self._prompts.values():
            data = prompt.__dict__.copy()
            data['entity_id'] = prompt.prompt_id
            self._persistence.save('prompts', data)
    
    def _save_versions(self):
        """保存所有版本到持久化存储"""
        for versions in self._versions.values():
            for version in versions:
                data = version.__dict__.copy()
                data['entity_id'] = version.version_id
                self._persistence.save('prompt_versions', data)
    
    def _parse_variables(self, content: str) -> List[str]:
        """从提示词内容中解析变量列表"""
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, content)
        return list(set(matches))
    
    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        parts = current_version.split('.')
        if len(parts) == 3:
            major, minor, patch = parts
            return f"{major}.{minor}.{int(patch) + 1}"
        return f"{current_version}.1"
    
    def create_prompt(self, name: str, category: str, content: str, is_active: bool = True) -> Prompt:
        """
        创建新的提示词模板
        
        Args:
            name: 提示词名称
            category: 提示词分类
            content: 提示词内容
            is_active: 是否激活
        
        Returns:
            创建的提示词对象
        """
        prompt_id = generate_prompt_id()
        variables = self._parse_variables(content)
        
        prompt = Prompt(
            prompt_id=prompt_id,
            name=name,
            category=category,
            content=content,
            variables=variables,
            is_active=is_active
        )
        
        self._prompts[prompt_id] = prompt
        
        # 创建初始版本记录
        initial_version = PromptVersion(
            version_id=generate_version_id(),
            prompt_id=prompt_id,
            version="1.0",
            content=content,
            change_description="初始版本"
        )
        self._versions[prompt_id] = [initial_version]
        
        # 保存到持久化存储
        self._save_prompts()
        self._save_versions()
        
        # 发布事件
        self._event_bus.publish(Event(
            event_type="prompt.created",
            payload={
                'prompt_id': prompt_id,
                'name': name,
                'category': category,
                'version': "1.0"
            }
        ))
        
        print(f"✅ 创建提示词: {name} ({prompt_id})")
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """
        获取指定ID的提示词
        
        Args:
            prompt_id: 提示词ID
        
        Returns:
            提示词对象，如果不存在则返回 None
        """
        return self._prompts.get(prompt_id)
    
    def update_prompt(self, prompt_id: str, content: Optional[str] = None, 
                      name: Optional[str] = None, category: Optional[str] = None,
                      is_active: Optional[bool] = None) -> Optional[Prompt]:
        """
        更新提示词模板
        
        Args:
            prompt_id: 提示词ID
            content: 新的提示词内容（可选）
            name: 新的提示词名称（可选）
            category: 新的分类（可选）
            is_active: 是否激活（可选）
        
        Returns:
            更新后的提示词对象，如果不存在则返回 None
        """
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return None
        
        old_version = prompt.version
        
        # 更新字段
        if name is not None:
            prompt.name = name
        if category is not None:
            prompt.category = category
        if content is not None:
            prompt.content = content
            prompt.variables = self._parse_variables(content)
        if is_active is not None:
            prompt.is_active = is_active
        
        # 递增版本号
        prompt.version = self._increment_version(prompt.version)
        prompt.updated_at = datetime.now().isoformat()
        
        # 创建新版本记录
        change_desc = f"更新提示词"
        if content:
            change_desc += " (内容变更)"
        if name:
            change_desc += f" (名称: {name})"
        
        new_version = PromptVersion(
            version_id=generate_version_id(),
            prompt_id=prompt_id,
            version=prompt.version,
            content=prompt.content,
            change_description=change_desc
        )
        self._versions[prompt_id].append(new_version)
        
        # 保存到持久化存储
        self._save_prompts()
        self._save_versions()
        
        # 发布事件
        self._event_bus.publish(Event(
            event_type="prompt.updated",
            payload={
                'prompt_id': prompt_id,
                'old_version': old_version,
                'new_version': prompt.version
            }
        ))
        
        print(f"✅ 更新提示词: {prompt.name} ({prompt.version})")
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """
        软删除提示词
        
        Args:
            prompt_id: 提示词ID
        
        Returns:
            如果删除成功返回 True，否则返回 False
        """
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return False
        
        prompt.is_active = False
        prompt.updated_at = datetime.now().isoformat()
        
        # 保存到持久化存储
        self._save_prompts()
        
        # 发布事件
        self._event_bus.publish(Event(
            event_type="prompt.deleted",
            payload={
                'prompt_id': prompt_id,
                'name': prompt.name
            }
        ))
        
        print(f"✅ 软删除提示词: {prompt.name}")
        return True
    
    def list_prompts(self, category: Optional[str] = None, 
                     include_inactive: bool = False) -> List[Prompt]:
        """
        获取提示词列表
        
        Args:
            category: 分类过滤（可选）
            include_inactive: 是否包含非激活的提示词
        
        Returns:
            提示词列表
        """
        prompts = list(self._prompts.values())
        
        # 过滤非激活的提示词
        if not include_inactive:
            prompts = [p for p in prompts if p.is_active]
        
        # 按分类过滤
        if category:
            prompts = [p for p in prompts if p.category == category]
        
        # 按更新时间排序
        prompts.sort(key=lambda p: p.updated_at, reverse=True)
        
        return prompts
    
    def render_prompt(self, prompt_id: str, variables: Dict[str, str]) -> str:
        """
        渲染提示词，替换变量
        
        Args:
            prompt_id: 提示词ID
            variables: 变量键值对
        
        Returns:
            替换后的提示词内容
        
        Raises:
            ValueError: 如果存在未提供的必需变量
        """
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            raise ValueError(f"提示词不存在: {prompt_id}")
        
        content = prompt.content
        
        # 替换变量
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", var_value)
        
        # 检查未替换的变量
        remaining = self._parse_variables(content)
        if remaining:
            raise ValueError(f"未提供的变量: {remaining}")
        
        return content
    
    def get_versions(self, prompt_id: str) -> List[PromptVersion]:
        """
        获取提示词的版本历史
        
        Args:
            prompt_id: 提示词ID
        
        Returns:
            版本列表，按创建时间倒序排列
        """
        versions = self._versions.get(prompt_id, [])
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions
    
    def rollback(self, prompt_id: str, version: str) -> bool:
        """
        回滚到指定版本
        
        Args:
            prompt_id: 提示词ID
            version: 目标版本号
        
        Returns:
            如果回滚成功返回 True，否则返回 False
        """
        prompt = self._prompts.get(prompt_id)
        if not prompt:
            return False
        
        versions = self._versions.get(prompt_id, [])
        target_version = next((v for v in versions if v.version == version), None)
        
        if not target_version:
            return False
        
        # 保存当前内容作为新版本
        before_version = PromptVersion(
            version_id=generate_version_id(),
            prompt_id=prompt_id,
            version=prompt.version,
            content=prompt.content,
            change_description=f"回滚前版本"
        )
        self._versions[prompt_id].append(before_version)
        
        # 恢复目标版本内容
        prompt.content = target_version.content
        prompt.variables = self._parse_variables(target_version.content)
        prompt.version = self._increment_version(prompt.version)
        prompt.updated_at = datetime.now().isoformat()
        
        # 创建回滚版本记录
        rollback_version = PromptVersion(
            version_id=generate_version_id(),
            prompt_id=prompt_id,
            version=prompt.version,
            content=prompt.content,
            change_description=f"回滚到版本 {version}"
        )
        self._versions[prompt_id].append(rollback_version)
        
        # 保存到持久化存储
        self._save_prompts()
        self._save_versions()
        
        # 发布事件
        self._event_bus.publish(Event(
            event_type="prompt.rollback",
            payload={
                'prompt_id': prompt_id,
                'target_version': version,
                'new_version': prompt.version
            }
        ))
        
        print(f"✅ 回滚提示词: {prompt.name} -> {version}")
        return True
    
    def refresh(self):
        """重新加载所有提示词"""
        self._prompts.clear()
        self._versions.clear()
        self._load_prompts()


# 服务实例
_prompt_management_service: Optional[PromptManagementService] = None


def get_prompt_management_service() -> PromptManagementService:
    """获取提示词管理服务实例"""
    global _prompt_management_service
    if _prompt_management_service is None:
        _prompt_management_service = PromptManagementService()
    return _prompt_management_service