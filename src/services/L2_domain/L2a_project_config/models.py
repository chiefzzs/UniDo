"""
L2a Project and Configuration Management - Data Models

数据模型定义：Project, WorkspaceConfig, ModelConfig
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict, fields


@dataclass
class Project:
    project_id: str
    name: str
    description: str = ""
    workspace_config_id: str = ""
    model_config_id: str = ""
    tool_config_ids: List[str] = field(default_factory=list)
    status: str = "active"
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        # 获取类定义的字段名称
        field_names = {f.name for f in fields(cls)}
        # 只保留类支持的字段
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)


@dataclass
class WorkspaceConfig:
    config_id: str
    name: str
    root_path: str
    type: str = "local"
    encoding: str = "utf-8"
    excluded_patterns: List[str] = field(default_factory=list)
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
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceConfig':
        # 获取类定义的字段名称
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        # 只保留类支持的字段
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)


@dataclass
class ModelConfig:
    config_id: str
    name: str
    model_name: str
    api_type: str
    api_address: str
    api_key: str
    parameters: Dict[str, Any] = field(default_factory=dict)
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        # 获取类定义的字段名称
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        # 只保留类支持的字段
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)
