"""
事件存储配置服务

用于配置哪些事件类型应该被存储到项目时间。
支持按项目隔离，每个项目可以有自己的事件存储配置。
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 默认事件存储配置 - 所有事件类型默认存储
DEFAULT_EVENT_STORAGE_CONFIG = [
    # 项目事件
    {"event_type": "project.created", "persist": True, "description": "项目创建"},
    {"event_type": "project.updated", "persist": True, "description": "项目更新"},
    {"event_type": "project.deleted", "persist": True, "description": "项目删除"},
    
    # 会话事件
    {"event_type": "session.created", "persist": True, "description": "会话创建"},
    {"event_type": "session.updated", "persist": True, "description": "会话更新"},
    {"event_type": "session.deleted", "persist": True, "description": "会话删除"},
    
    # 对话事件
    {"event_type": "dialog.created", "persist": True, "description": "对话创建"},
    {"event_type": "dialog.updated", "persist": True, "description": "对话更新"},
    {"event_type": "dialog.deleted", "persist": True, "description": "对话删除"},
    {"event_type": "dialog.completed", "persist": True, "description": "对话完成"},
    
    # 消息事件
    {"event_type": "message.created", "persist": True, "description": "消息创建"},
    {"event_type": "message.updated", "persist": True, "description": "消息更新"},
    {"event_type": "message.deleted", "persist": True, "description": "消息删除"},
    
    # LLM调用事件
    {"event_type": "llm.request_sent", "persist": True, "description": "LLM请求发送"},
    {"event_type": "llm.response_received", "persist": True, "description": "LLM响应接收"},
    {"event_type": "llm.stream_chunk", "persist": False, "description": "LLM流式片段（通常不存储以节省空间）"},
    {"event_type": "llm.thinking", "persist": False, "description": "LLM思考过程（通常不存储）"},
    {"event_type": "llm.call_completed", "persist": True, "description": "LLM调用完成"},
    {"event_type": "llm.call_text_completed", "persist": True, "description": "LLM文本聚合完成"},
    {"event_type": "llm.call_thinking_completed", "persist": True, "description": "LLM思考聚合完成"},
    {"event_type": "llm.tool_call_completed", "persist": True, "description": "LLM工具调用完成"},
    {"event_type": "llm.error", "persist": True, "description": "LLM错误"},
    {"event_type": "llm.call_failed", "persist": True, "description": "LLM调用失败"},
    {"event_type": "llm.response_classified", "persist": True, "description": "LLM响应分类完成"},
    
    # 工具事件
    {"event_type": "tool.registered", "persist": False, "description": "工具注册（不持久化）"},
    {"event_type": "tool.unregistered", "persist": False, "description": "工具注销（不持久化）"},
    {"event_type": "tool.execution_started", "persist": True, "description": "工具执行开始"},
    {"event_type": "tool.execution_completed", "persist": True, "description": "工具执行完成"},
    {"event_type": "tool.execution_failed", "persist": True, "description": "工具执行失败"},
    {"event_type": "tool.call_started", "persist": True, "description": "工具调用开始"},
    {"event_type": "tool.call_completed", "persist": True, "description": "工具调用完成"},
    {"event_type": "tool.call_failed", "persist": True, "description": "工具调用失败"},
    {"event_type": "tool.call_cancelled", "persist": True, "description": "工具调用取消"},
    {"event_type": "tool.execution_output", "persist": False, "description": "工具执行输出（流式）"},
    {"event_type": "tool.execution_output_end", "persist": False, "description": "工具执行输出结束"},
    {"event_type": "tool.execution_result", "persist": True, "description": "工具执行结果"},
    
    # 技能事件
    {"event_type": "skill.registered", "persist": True, "description": "技能注册"},
    {"event_type": "skill.unregistered", "persist": True, "description": "技能注销"},
    
    # 任务事件
    {"event_type": "task.started", "persist": True, "description": "任务开始"},
    {"event_type": "task.completed", "persist": True, "description": "任务完成"},
    {"event_type": "task.updated", "persist": True, "description": "任务更新"},
    {"event_type": "task.failed", "persist": True, "description": "任务失败"},
    {"event_type": "task_group.created", "persist": True, "description": "任务组创建"},
    {"event_type": "task_group.updated", "persist": True, "description": "任务组更新"},
    {"event_type": "task_group.deleted", "persist": True, "description": "任务组删除"},
    {"event_type": "task_group.completed", "persist": True, "description": "任务组完成"},
    
    # 轮次事件
    {"event_type": "round.started", "persist": True, "description": "轮次开始"},
    {"event_type": "round.completed", "persist": True, "description": "轮次完成"},
    
    # 客户端消息事件（仅通过WebSocket传输，不持久化）
    {"event_type": "client.message_received", "persist": False, "description": "客户端消息接收（不持久化）"},
    {"event_type": "client.message_sent", "persist": False, "description": "客户端消息发送（不持久化）"},
    
    # 系统状态事件
    {"event_type": "system.status_changed", "persist": True, "description": "系统状态变更"},
    
    # 会话切换与历史回放事件
    {"event_type": "session.switched", "persist": True, "description": "会话切换"},
    {"event_type": "history.replay.started", "persist": True, "description": "历史回放开始"},
    {"event_type": "history.replay.complete", "persist": True, "description": "历史回放完成"},
]


class EventStorageConfigService:
    """
    事件存储配置服务 - 管理事件类型的持久化配置
    
    功能：
    1. 配置哪些事件类型应该被存储到项目时间
    2. 支持按项目隔离（通过 project_id）
    3. 提供CRUD操作接口
    4. 支持批量更新配置
    """
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认配置路径
            base_dir = Path(__file__).parent.parent.parent.parent
            self.config_path = base_dir / "data" / "dev" / "event_storage_config.json"
        else:
            self.config_path = Path(config_path)
        
        # 确保配置目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载或初始化配置
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载事件存储配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._get_default_config()
        else:
            # 如果配置文件不存在，创建默认配置
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config
    
    def _get_default_config(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取默认配置"""
        return {"default": DEFAULT_EVENT_STORAGE_CONFIG}
    
    def _save_config(self, config: Dict[str, List[Dict[str, Any]]]) -> None:
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def should_persist_event(self, event_type: str, project_id: str = None) -> bool:
        """
        判断指定事件类型是否应该持久化
        
        Args:
            event_type: 事件类型
            project_id: 项目ID（可选，用于项目级配置）
        
        Returns:
            是否应该持久化
        """
        # 首先检查项目级配置
        if project_id and project_id in self._config:
            for item in self._config[project_id]:
                if item['event_type'] == event_type:
                    return item.get('persist', True)
        
        # 如果没有项目级配置或项目配置中没有该事件，使用默认配置
        if "default" in self._config:
            for item in self._config["default"]:
                if item['event_type'] == event_type:
                    return item.get('persist', True)
        
        # 如果事件类型不存在于配置中，自动添加并返回True
        self._add_event_type(event_type)
        return True
    
    def _add_event_type(self, event_type: str) -> None:
        """添加新的事件类型到默认配置"""
        if "default" not in self._config:
            self._config["default"] = []
        
        # 检查是否已存在
        for item in self._config["default"]:
            if item['event_type'] == event_type:
                return
        
        # 添加新类型
        new_event = {
            "event_type": event_type,
            "persist": True,
            "description": f"自动发现的事件类型: {event_type}",
            "auto_discovered": True,
            "discovered_at": datetime.now().isoformat()
        }
        self._config["default"].append(new_event)
        self._save_config(self._config)
    
    def get_config(self, event_type: str, project_id: str = None) -> Optional[Dict[str, Any]]:
        """获取指定事件类型的配置"""
        # 首先检查项目级配置
        if project_id and project_id in self._config:
            for item in self._config[project_id]:
                if item['event_type'] == event_type:
                    return item
        
        # 使用默认配置
        if "default" in self._config:
            for item in self._config["default"]:
                if item['event_type'] == event_type:
                    return item
        
        return None
    
    def list_configs(self, project_id: str = None) -> List[Dict[str, Any]]:
        """
        获取所有事件存储配置
        
        Args:
            project_id: 项目ID（可选，如果不提供则返回默认配置）
        
        Returns:
            配置列表
        """
        if project_id and project_id in self._config:
            return self._config[project_id].copy()
        
        return self._config.get("default", DEFAULT_EVENT_STORAGE_CONFIG).copy()
    
    def update_config(self, event_type: str, persist: bool, project_id: str = None, description: str = None) -> bool:
        """
        更新指定事件类型的配置
        
        Args:
            event_type: 事件类型
            persist: 是否持久化
            project_id: 项目ID（可选，如果不提供则更新默认配置）
            description: 描述（可选）
        
        Returns:
            是否更新成功
        """
        # 确定使用哪个配置
        config_key = project_id if project_id else "default"
        
        if config_key not in self._config:
            self._config[config_key] = DEFAULT_EVENT_STORAGE_CONFIG.copy()
        
        # 查找并更新
        for item in self._config[config_key]:
            if item['event_type'] == event_type:
                item['persist'] = persist
                if description is not None:
                    item['description'] = description
                item['updated_at'] = datetime.now().isoformat()
                self._save_config(self._config)
                return True
        
        # 如果不存在，添加新配置
        new_event = {
            "event_type": event_type,
            "persist": persist,
            "description": description or f"手动配置: {event_type}",
            "updated_at": datetime.now().isoformat()
        }
        self._config[config_key].append(new_event)
        self._save_config(self._config)
        return True
    
    def batch_update_configs(self, updates: List[Dict[str, Any]], project_id: str = None) -> bool:
        """
        批量更新事件存储配置
        
        Args:
            updates: 更新列表，每个元素包含 event_type 和 persist
            project_id: 项目ID（可选）
        
        Returns:
            是否更新成功
        """
        try:
            config_key = project_id if project_id else "default"
            
            if config_key not in self._config:
                self._config[config_key] = DEFAULT_EVENT_STORAGE_CONFIG.copy()
            
            # 创建事件类型到索引的映射
            event_type_index = {}
            for i, item in enumerate(self._config[config_key]):
                event_type_index[item['event_type']] = i
            
            # 应用更新
            for update in updates:
                event_type = update.get('event_type')
                persist = update.get('persist')
                description = update.get('description')
                
                if event_type is None or persist is None:
                    continue
                
                if event_type in event_type_index:
                    # 更新现有配置
                    idx = event_type_index[event_type]
                    self._config[config_key][idx]['persist'] = persist
                    if description is not None:
                        self._config[config_key][idx]['description'] = description
                    self._config[config_key][idx]['updated_at'] = datetime.now().isoformat()
                else:
                    # 添加新配置
                    new_event = {
                        "event_type": event_type,
                        "persist": persist,
                        "description": description or f"批量配置: {event_type}",
                        "updated_at": datetime.now().isoformat()
                    }
                    self._config[config_key].append(new_event)
                    event_type_index[event_type] = len(self._config[config_key]) - 1
            
            self._save_config(self._config)
            return True
        except Exception as e:
            print(f"批量更新配置失败: {e}")
            return False
    
    def delete_project_config(self, project_id: str) -> bool:
        """
        删除项目的配置，恢复使用默认配置
        
        Args:
            project_id: 项目ID
        
        Returns:
            是否删除成功
        """
        if project_id in self._config:
            del self._config[project_id]
            self._save_config(self._config)
            return True
        return False


# 全局单例实例
_event_storage_config_service: Optional[EventStorageConfigService] = None


def get_event_storage_config_service() -> EventStorageConfigService:
    """获取事件存储配置服务的单例实例"""
    global _event_storage_config_service
    if _event_storage_config_service is None:
        _event_storage_config_service = EventStorageConfigService()
    return _event_storage_config_service
