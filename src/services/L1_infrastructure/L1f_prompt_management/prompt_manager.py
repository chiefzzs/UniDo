"""
L1f Prompt Management Service

提供系统提示词的管理和读取功能，支持动态加载和缓存提示词配置。

职责：
- 从配置文件加载系统提示词
- 提供提示词的获取接口
- 支持环境信息的动态注入
- 缓存提示词以提高性能
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PromptConfig:
    """提示词配置数据类"""
    name: str
    content: str
    description: str = ""
    category: str = "system"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PromptManager:
    """
    提示词管理器
    
    负责加载、缓存和提供系统提示词。
    """
    
    _instance: Optional['PromptManager'] = None
    
    def __init__(self):
        self._prompts: Dict[str, PromptConfig] = {}
        self._cache: Dict[str, str] = {}
        self._base_path = self._get_base_path()
        self._load_prompts()
    
    def _get_base_path(self) -> Path:
        """获取提示词配置文件的基础路径"""
        # 从 prompt_manager.py 向上走 4 层到达项目根目录，然后加上 src/prompt
        # __file__ = d:\learnning\260518\src\services\L1_infrastructure\L1f_prompt_management\prompt_manager.py
        # .parent = L1f_prompt_management
        # .parent.parent = L1_infrastructure  
        # .parent.parent.parent = services
        # .parent.parent.parent.parent = src
        # .parent.parent.parent.parent.parent = 260518 (项目根目录)
        return Path(__file__).parent.parent.parent.parent.parent / 'src' / 'prompt'
    
    def _load_prompts(self):
        """从配置文件加载所有提示词"""
        try:
            # 加载系统提示词
            system_prompts_path = self._base_path / 'system_prompts.json'
            if system_prompts_path.exists():
                with open(system_prompts_path, 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)
                
                for name, content in prompts_data.items():
                    self._prompts[name] = PromptConfig(
                        name=name,
                        content=content,
                        category="system",
                        description=f"系统提示词: {name}"
                    )
                    self._cache[name] = content
                
                print(f"✅ PromptManager: 已加载 {len(self._prompts)} 个系统提示词")
            else:
                print(f"⚠️ PromptManager: 系统提示词文件不存在: {system_prompts_path}")
                
        except Exception as e:
            print(f"❌ PromptManager: 加载提示词失败: {e}")
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        获取指定名称的提示词内容
        
        Args:
            prompt_name: 提示词名称
            
        Returns:
            提示词内容，如果不存在则返回 None
        """
        return self._cache.get(prompt_name)
    
    def get_prompt_config(self, prompt_name: str) -> Optional[PromptConfig]:
        """
        获取指定名称的提示词配置
        
        Args:
            prompt_name: 提示词名称
            
        Returns:
            PromptConfig 对象，如果不存在则返回 None
        """
        return self._prompts.get(prompt_name)
    
    def list_prompts(self) -> Dict[str, PromptConfig]:
        """获取所有已加载的提示词配置"""
        return self._prompts
    
    def get_all_prompt_names(self) -> list:
        """获取所有提示词名称列表"""
        return list(self._prompts.keys())
    
    def build_user_input_context(self, user_input: str, env_info: Dict[str, Any] = None) -> str:
        """
        构建用户输入的完整上下文，包含系统提醒和环境信息
        
        Args:
            user_input: 用户原始输入
            env_info: 环境信息字典（可选）
            
        Returns:
            包含系统提醒的完整用户输入内容
        """
        context_parts = []
        
        # 添加待办事项提醒
        todo_reminder = self.get_prompt('todo_reminder')
        if todo_reminder:
            context_parts.append(f"<system-reminder>\n\n{todo_reminder}\n\n</system-reminder>")
        
        # 添加环境信息提醒
        if env_info:
            env_str = "\n<env>\n"
            for key, value in env_info.items():
                env_str += f"{key}: {value}\n"
            env_str += "</env>\n"
            
            important_instructions = self.get_prompt('important_instructions')
            if important_instructions:
                env_context = f"<system-reminder>\nAs you answer the user's questions, you can use the following context:\n\n{env_str}\n# important-instruction-reminders\n{important_instructions}\n\n</system-reminder>"
                context_parts.append(env_context)
        
        # 添加语言设置提醒
        language_settings = self.get_prompt('response_language_settings')
        if language_settings:
            context_parts.append(f"<system-reminder>\n\n{language_settings}\n\n</system-reminder>")
        
        # 添加技能检查提醒
        skill_check = self.get_prompt('skill_check_reminder')
        if skill_check:
            context_parts.append(f"<system-reminder>\n{skill_check}\n\n\n\n</system-reminder>")
        
        # 添加用户输入
        context_parts.append(f"\n<user_input>\n{user_input}\n</user_input>")
        
        return "\n".join(context_parts)
    
    def build_user_message_for_llm(self, user_input: str, env_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        构建用于LLM调用的用户消息对象
        
        Args:
            user_input: 用户原始输入
            env_info: 环境信息字典（可选）
            
        Returns:
            符合LLM消息格式的字典，每个系统提醒为独立的text元素
        """
        content_parts = []
        
        # 1. 添加待办事项提醒
        todo_reminder = self.get_prompt('todo_reminder')
        if todo_reminder:
            content_parts.append({
                "type": "text",
                "text": f"<system-reminder>\n\n{todo_reminder}\n\n</system-reminder>"
            })
        
        # 2. 添加环境信息提醒
        if env_info:
            env_str = "\n<env>\n"
            for key, value in env_info.items():
                env_str += f"{key}: {value}\n"
            env_str += "</env>\n"
            
            important_instructions = self.get_prompt('important_instructions')
            if important_instructions:
                env_context = f"<system-reminder>\nAs you answer the user's questions, you can use the following context:\n\n{env_str}\n# important-instruction-reminders\n{important_instructions}\n\n</system-reminder>"
                content_parts.append({
                    "type": "text",
                    "text": env_context
                })
        
        # 3. 添加语言设置提醒
        language_settings = self.get_prompt('response_language_settings')
        if language_settings:
            content_parts.append({
                "type": "text",
                "text": f"<system-reminder>\n\n{language_settings}\n\n</system-reminder>"
            })
        
        # 4. 添加技能检查提醒
        skill_check = self.get_prompt('skill_check_reminder')
        if skill_check:
            content_parts.append({
                "type": "text",
                "text": f"<system-reminder>\n{skill_check}\n\n\n\n</system-reminder>"
            })
        
        # 5. 添加用户输入
        content_parts.append({
            "type": "text",
            "text": f"\n<user_input>\n{user_input}\n</user_input>"
        })
        
        return {
            "role": "user",
            "content": content_parts
        }
    
    def refresh(self):
        """重新加载所有提示词配置"""
        self._prompts.clear()
        self._cache.clear()
        self._load_prompts()
    
    @classmethod
    def get_instance(cls) -> 'PromptManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_prompt_manager() -> PromptManager:
    """获取提示词管理器实例"""
    return PromptManager.get_instance()
