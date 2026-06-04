"""
L2f Tool Management Service - Implementation

工具管理服务负责管理工具的定义、注册、配置和查询。
"""

import uuid
import json
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
class ToolDefinition:
    tool_id: str
    tool_name: str
    category: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    tool_type: str = "native"
    timeout: float = 30.0
    retry_config: Dict[str, Any] = field(default_factory=dict)
    is_async: bool = False
    is_task_group_tool: bool = False
    # 平台兼容性字段
    supported_os: List[str] = field(default_factory=list)  # 支持的操作系统：windows/linux/macos，空列表表示所有平台
    supported_terminals: List[str] = field(default_factory=list)  # 支持的终端：powershell/bash/zsh，空列表表示所有终端
    platform_aliases: Dict[str, str] = field(default_factory=dict)  # 平台别名映射：{"windows": "dir", "linux": "ls"}
    is_active: bool = True  # 是否激活（根据当前平台自动设置）
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
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolDefinition':
        # 处理旧数据兼容
        data = data.copy()
        if 'is_task_group_tool' not in data:
            data['is_task_group_tool'] = False
        # 平台兼容性字段默认值
        if 'supported_os' not in data:
            data['supported_os'] = []
        if 'supported_terminals' not in data:
            data['supported_terminals'] = []
        if 'platform_aliases' not in data:
            data['platform_aliases'] = {}
        if 'is_active' not in data:
            data['is_active'] = True
        return cls(**data)

    def set_active_based_on_platform(self, os_type: str = None, terminal: str = None) -> bool:
        """
        根据当前平台设置工具的激活状态
        :param os_type: 操作系统类型
        :param terminal: 终端类型
        :return: 设置后的激活状态
        """
        if not os_type:
            os_type = self._get_current_os()
        
        self.is_active = self.is_supported_on_platform(os_type, terminal)
        return self.is_active

    @staticmethod
    def _get_current_os() -> str:
        """获取当前操作系统类型"""
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('linux'):
            return 'linux'
        elif sys.platform.startswith('darwin'):
            return 'macos'
        return 'unknown'

    def is_supported_on_platform(self, os_type: str = None, terminal: str = None) -> bool:
        """
        检查工具是否支持当前平台
        :param os_type: 操作系统类型（windows/linux/macos）
        :param terminal: 终端类型（powershell/bash/zsh）
        :return: 是否支持
        """
        # 如果没有限制，返回 True
        if not self.supported_os and not self.supported_terminals:
            return True
        
        # 检查操作系统
        if os_type and self.supported_os:
            if os_type.lower() not in [os.lower() for os in self.supported_os]:
                return False
        
        # 检查终端类型
        if terminal and self.supported_terminals:
            if terminal.lower() not in [t.lower() for t in self.supported_terminals]:
                return False
        
        return True

    def get_platform_alias(self, os_type: str = None) -> Optional[str]:
        """
        获取当前平台的工具别名
        :param os_type: 操作系统类型
        :return: 平台对应的工具名，如果没有则返回 None
        """
        if not os_type:
            return None
        return self.platform_aliases.get(os_type.lower())


@dataclass
class ToolExecutionRecord:
    record_id: str
    tool_id: str
    tool_name: str
    status: str
    input_params: Dict[str, Any] = field(default_factory=dict)
    output_result: Optional[str] = None
    error_message: Optional[str] = None
    start_time: str = ""
    end_time: str = ""
    duration: float = 0.0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.start_time:
            self.start_time = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolExecutionRecord':
        return cls(**data)


class ToolRegistry:
    _instance = None
    _tools: Dict[str, ToolDefinition] = {}
    _implementations: Dict[str, Callable] = {}

    @classmethod
    def get_instance(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = ToolRegistry()
        return cls._instance

    def register_tool(self, tool: ToolDefinition, implementation: Callable = None):
        # 根据当前平台自动设置工具激活状态
        tool.set_active_based_on_platform()
        print(f"🔧 [ToolRegistry] 注册工具: {tool.tool_name} (ID: {tool.tool_id}), 平台兼容性: {tool.supported_os}, 激活状态: {tool.is_active}")
        
        self._tools[tool.tool_id] = tool
        if tool.tool_name:
            self._tools[f"name:{tool.tool_name}"] = tool
        if implementation:
            self._implementations[tool.tool_id] = implementation

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_id) or self._tools.get(f"name:{tool_id}")

    def get_implementation(self, tool_id: str) -> Optional[Callable]:
        return self._implementations.get(tool_id)

    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        unique_tools = []
        seen_ids = set()
        for t in tools:
            if t.tool_id not in seen_ids and not t.tool_id.startswith('name:'):
                seen_ids.add(t.tool_id)
                unique_tools.append(t)
        return unique_tools

    def unregister_tool(self, tool_id: str):
        tool = self._tools.get(tool_id)
        if tool:
            self._tools.pop(tool_id, None)
            self._tools.pop(f"name:{tool.tool_name}", None)
            self._implementations.pop(tool_id, None)


class ToolManagementService:
    def __init__(self, persistence_service=None, event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.event_bus = event_bus or EventBus.get_instance()
        self.registry = ToolRegistry.get_instance()

    def _generate_id(self) -> str:
        return f"tool-{uuid.uuid4().hex[:12]}"

    def register_tool(self, tool_name: str, category: str, description: str,
                    parameters: Dict = None, tool_type: str = "native",
                    timeout: float = 30.0, is_async: bool = False,
                    is_task_group_tool: bool = False,
                    supported_os: List[str] = None,
                    supported_terminals: List[str] = None,
                    platform_aliases: Dict[str, str] = None,
                    implementation: Callable = None) -> ToolDefinition:
        tool = ToolDefinition(
            tool_id=self._generate_id(),
            tool_name=tool_name,
            category=category,
            description=description,
            parameters=parameters or {},
            tool_type=tool_type,
            timeout=timeout,
            is_async=is_async,
            is_task_group_tool=is_task_group_tool,
            supported_os=supported_os or [],
            supported_terminals=supported_terminals or [],
            platform_aliases=platform_aliases or {}
        )

        self.registry.register_tool(tool, implementation)
        self.persistence.save('tool_definitions', tool.to_dict())

        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_REGISTERED,
            payload={'tool_id': tool.tool_id, 'tool_name': tool.tool_name}
        ))

        return tool

    def is_task_group_tool(self, tool_id: str) -> bool:
        """
        判断工具是否为任务组工具
        
        Args:
            tool_id: 工具ID或工具名称
            
        Returns:
            bool: 如果是任务组工具返回True，否则返回False
        """
        tool = self.get_tool(tool_id)
        if tool:
            return tool.is_task_group_tool
        
        # 检查工具描述符文件（从JSON文件加载的工具）
        try:
            tool_desc = self._load_tool_from_descriptor(tool_id)
            if tool_desc:
                return tool_desc.get('is_task_group_tool', False)
        except Exception:
            pass
        
        return False

    def _load_tool_from_descriptor(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """
        从描述符文件加载工具定义
        
        Args:
            tool_id: 工具ID
            
        Returns:
            Dict: 工具描述符内容
        """
        # 尝试从工具描述目录加载
        desc_dirs = [
            Path(__file__).parent.parent.parent.parent / 'src' / 'tools' / 'descriptions' / 'en',
            Path(__file__).parent.parent.parent.parent / 'src' / 'tools' / 'descriptions' / 'zh'
        ]
        
        for desc_dir in desc_dirs:
            if not desc_dir.exists():
                continue
            
            # 尝试按tool_id查找
            desc_file = desc_dir / f"{tool_id}.json"
            if desc_file.exists():
                with open(desc_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 尝试按工具名称查找
            for json_file in desc_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('tool_id') == tool_id or data.get('name') == tool_id:
                            return data
                except Exception:
                    continue
        
        return None

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        tool = self.registry.get_tool(tool_id)
        if tool:
            return tool

        all_tools = self.persistence.list('tool_definitions')
        for t in all_tools:
            if t.get('tool_id') == tool_id:
                return ToolDefinition.from_dict(t)
        return None

    def get_tool_implementation(self, tool_id: str) -> Optional[Callable]:
        return self.registry.get_implementation(tool_id)

    def list_tools(self, category: str = None, os_type: str = None, terminal: str = None, active_only: bool = False) -> List[ToolDefinition]:
        """
        列出工具，支持平台筛选和激活状态筛选
        :param category: 工具分类（可选）
        :param os_type: 操作系统类型（windows/linux/macos，可选）
        :param terminal: 终端类型（powershell/bash/zsh，可选）
        :param active_only: 是否只返回激活的工具（提供给大模型时使用）
        :return: 工具列表
        """
        registered_tools = self.registry.list_tools(category=category)

        # 平台筛选
        if os_type or terminal:
            registered_tools = [
                t for t in registered_tools 
                if t.is_supported_on_platform(os_type, terminal)
            ]

        # 激活状态筛选
        if active_only:
            registered_tools = [
                t for t in registered_tools 
                if t.is_active
            ]

        if not registered_tools and category is None:
            all_tools = self.persistence.list('tool_definitions')
            tools = [ToolDefinition.from_dict(t) for t in all_tools]
            
            # 平台筛选
            if os_type or terminal:
                tools = [
                    t for t in tools 
                    if t.is_supported_on_platform(os_type, terminal)
                ]
            
            # 激活状态筛选
            if active_only:
                tools = [
                    t for t in tools 
                    if t.is_active
                ]
            
            return tools

        return registered_tools

    def list_active_tools(self, category: str = None) -> List[ToolDefinition]:
        """
        获取所有激活的工具（提供给大模型使用）
        :param category: 工具分类（可选）
        :return: 激活的工具列表
        """
        return self.list_tools(category=category, active_only=True)

    @staticmethod
    def get_current_platform() -> Dict[str, str]:
        """
        获取当前平台信息
        :return: 包含 os_type 和 terminal_type 的字典
        """
        os_type = ToolDefinition._get_current_os()
        
        # 检测终端类型
        terminal_type = 'powershell' if os_type == 'windows' else 'bash'
        
        return {
            'os_type': os_type,
            'terminal_type': terminal_type
        }

    def update_tool(self, tool_id: str, **kwargs) -> Optional[ToolDefinition]:
        all_tools = self.persistence.list('tool_definitions')
        for i, t in enumerate(all_tools):
            if t.get('tool_id') == tool_id:
                t.update(kwargs)
                t['updated_at'] = datetime.now().isoformat()
                all_tools[i] = t
                self.persistence.save('tool_definitions', t)

                tool_def = ToolDefinition.from_dict(t)
                self.registry.register_tool(tool_def)

                return tool_def
        return None

    def unregister_tool(self, tool_id: str) -> bool:
        tool = self.get_tool(tool_id)
        if not tool:
            return False

        self.registry.unregister_tool(tool_id)

        all_tools = self.persistence.list('tool_definitions')
        new_tools = [t for t in all_tools if t.get('tool_id') != tool_id]
        self.persistence._write_all('tool_definitions', new_tools)

        self.event_bus.publish(Event(
            event_type=EventTypes.TOOL_UNREGISTERED,
            payload={'tool_id': tool_id}
        ))

        return True

    def load_tools_from_descriptions(self, lang: str = 'en') -> int:
        """
        从工具描述目录批量加载工具定义
        
        Args:
            lang: 语言版本 ('en' 或 'zh')
            
        Returns:
            成功加载的工具数量
        """
        desc_dir = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'tools' / 'descriptions' / lang
        
        if not desc_dir.exists():
            print(f"[ToolManagement] 工具描述目录不存在: {desc_dir}")
            return 0
        
        # 获取已存在的工具ID列表
        existing_tool_ids = set()
        for t in self.list_tools():
            existing_tool_ids.add(t.tool_id)
        
        loaded_count = 0
        new_count = 0
        
        for json_file in desc_dir.glob('*.json'):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    tool_desc = json.load(f)
                
                tool_id = tool_desc.get('tool_id', '')
                
                # 检查工具是否已存在
                if tool_id in existing_tool_ids:
                    # 更新现有工具
                    self.update_tool(
                        tool_id=tool_id,
                        tool_name=tool_desc.get('name', ''),
                        category=tool_desc.get('category', 'General'),
                        description=tool_desc.get('description', ''),
                        parameters=tool_desc.get('parameters', {}),
                        supported_os=tool_desc.get('supported_os', []),
                        supported_terminals=tool_desc.get('supported_terminals', []),
                        platform_aliases=tool_desc.get('platform_aliases', {})
                    )
                    print(f"[ToolManagement] ↻ 更新工具: {tool_id} - {tool_desc.get('name', '')}")
                else:
                    # 注册新工具
                    tool = ToolDefinition(
                        tool_id=tool_id,
                        tool_name=tool_desc.get('name', ''),
                        category=tool_desc.get('category', 'General'),
                        description=tool_desc.get('description', ''),
                        parameters=tool_desc.get('parameters', {}),
                        supported_os=tool_desc.get('supported_os', ['windows', 'linux', 'macos']),
                        supported_terminals=tool_desc.get('supported_terminals', []),
                        platform_aliases=tool_desc.get('platform_aliases', {})
                    )
                    self.registry.register_tool(tool)
                    self.persistence.save('tool_definitions', tool.to_dict())
                    
                    self.event_bus.publish(Event(
                        event_type=EventTypes.TOOL_REGISTERED,
                        payload={'tool_id': tool.tool_id, 'tool_name': tool.tool_name}
                    ))
                    
                    new_count += 1
                    print(f"[ToolManagement] ✓ 新增工具: {tool_id} - {tool_desc.get('name', '')}")
                    existing_tool_ids.add(tool_id)  # 添加到已存在列表
                
                loaded_count += 1
                
            except Exception as e:
                print(f"[ToolManagement] ✗ 加载工具失败 {json_file.name}: {e}")
        
        print(f"[ToolManagement] 批量加载完成，共 {loaded_count} 个工具（新增 {new_count} 个）")
        return loaded_count

    def save_execution_record(self, record: ToolExecutionRecord):
        self.persistence.save('tool_execution_records', record.to_dict())

    def list_execution_records(self, tool_id: str = None, limit: int = 100) -> List[ToolExecutionRecord]:
        all_records = self.persistence.list('tool_execution_records')
        result = [ToolExecutionRecord.from_dict(r) for r in all_records]

        if tool_id:
            result = [r for r in result if r.tool_id == tool_id]

        result.sort(key=lambda x: x.created_at, reverse=True)
        return result[:limit]
