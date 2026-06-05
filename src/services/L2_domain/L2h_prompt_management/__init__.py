"""
L2h Prompt Management Service Module

提供提示词模板的 CRUD 操作、版本管理和变量替换功能。
"""

from .prompt_management_service import (
    PromptManagementService,
    Prompt,
    PromptVersion,
    PromptVariable,
    get_prompt_management_service
)

__all__ = [
    'PromptManagementService',
    'Prompt',
    'PromptVersion',
    'PromptVariable',
    'get_prompt_management_service'
]