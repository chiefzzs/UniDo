"""
L2f Tool Management Service

L2f 工具管理服务负责管理工具的定义、注册、配置和查询。

职责：
- 工具注册：注册新的工具及其实现
- 工具配置：管理工具的参数配置和元数据
- 工具查询：按类别、名称等条件查询工具
- 工具调度：判断工具类型并调度执行

依赖 L1 层：
- L1b 持久化服务：用于存储工具配置
- L1d 事件系统：发布工具注册事件
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field, asdict

import sys
from pathlib import Path
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
        return cls(**data)


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
            is_task_group_tool=is_task_group_tool
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
        import json
        from pathlib import Path
        
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

    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        registered_tools = self.registry.list_tools(category=category)

        if not registered_tools and category is None:
            all_tools = self.persistence.list('tool_definitions')
            return [ToolDefinition.from_dict(t) for t in all_tools]

        return registered_tools

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
        import json
        from pathlib import Path
        
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
                        parameters=tool_desc.get('parameters', {})
                    )
                    print(f"[ToolManagement] ↻ 更新工具: {tool_id} - {tool_desc.get('name', '')}")
                else:
                    # 注册新工具
                    tool = ToolDefinition(
                        tool_id=tool_id,
                        tool_name=tool_desc.get('name', ''),
                        category=tool_desc.get('category', 'General'),
                        description=tool_desc.get('description', ''),
                        parameters=tool_desc.get('parameters', {})
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


def get_tool_management_service() -> ToolManagementService:
    return ToolManagementService()


def get_tool_registry() -> ToolRegistry:
    return ToolRegistry.get_instance()
