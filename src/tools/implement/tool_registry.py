"""
工具注册器模块
支持配置驱动的跨平台工具加载
"""
from typing import Dict, List, Optional, Any
from .base_tool import BaseTool
from .config_driven_registry import ConfigDrivenToolRegistry


class ToolNotFoundError(Exception):
    """工具不存在异常"""
    pass


class ValidationError(Exception):
    """参数验证异常"""
    pass


class ToolRegistry:
    """
    工具注册器，用于管理所有可用工具
    支持配置驱动和手动注册两种模式
    """
    
    def __init__(self, use_config_driven: bool = True, config_path: Optional[str] = None):
        """
        初始化工具注册器
        
        Args:
            use_config_driven: 是否使用配置驱动模式
            config_path: 配置文件路径
        """
        self._manual_tools: Dict[str, BaseTool] = {}
        self._use_config_driven = use_config_driven
        
        if use_config_driven:
            try:
                self._config_registry = ConfigDrivenToolRegistry(config_path)
                print("[ToolRegistry] 使用配置驱动模式")
            except Exception as e:
                print(f"[ToolRegistry] 配置驱动模式加载失败: {e}")
                self._config_registry = None
                self._use_config_driven = False
        else:
            self._config_registry = None
    
    def register_tool(self, tool: BaseTool) -> None:
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        tool_id = str(tool.tool_id)
        self._manual_tools[tool_id] = tool
        
        # 同时注册名称映射
        if tool.name:
            self._manual_tools[tool.name.lower()] = tool
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            tool_id: 工具ID或名称
            
        Returns:
            工具实例，如果不存在则返回None
        """
        # 先检查手动注册的工具
        if tool_id in self._manual_tools:
            return self._manual_tools[tool_id]
        
        # 检查小写名称
        tool_id_lower = tool_id.lower()
        if tool_id_lower in self._manual_tools:
            return self._manual_tools[tool_id_lower]
        
        # 检查配置驱动的工具
        if self._config_registry:
            return self._config_registry.get_tool(tool_id)
        
        return None
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有工具列表
        
        Returns:
            工具实例列表
        """
        tools = list(self._manual_tools.values())
        
        if self._config_registry:
            tools.extend(self._config_registry.get_all_tools())
        
        # 去重
        seen_ids = set()
        unique_tools = []
        for tool in tools:
            tool_id = str(tool.tool_id)
            if tool_id not in seen_ids:
                seen_ids.add(tool_id)
                unique_tools.append(tool)
        
        return unique_tools
    
    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的描述信息
        
        Returns:
            工具描述列表
        """
        return [tool.get_description() for tool in self.get_all_tools()]
    
    def validate_tool_parameters(self, tool_id: str, parameters: Dict[str, Any]) -> bool:
        """
        验证工具参数合法性
        
        Args:
            tool_id: 工具ID
            parameters: 参数字典
            
        Returns:
            验证结果
            
        Raises:
            ToolNotFoundError: 工具不存在时抛出
            ValidationError: 参数验证失败时抛出
        """
        tool = self.get_tool(tool_id)
        if not tool:
            raise ToolNotFoundError(f"Tool with id {tool_id} not found")
        
        validation_error = tool.validate_params(parameters)
        if validation_error:
            raise ValidationError(f"Parameter validation failed: {validation_error}")
        
        return True
    
    def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行指定工具
        
        Args:
            tool_id: 工具ID
            params: 工具参数
            
        Returns:
            执行结果
        """
        tool = self.get_tool(tool_id)
        if not tool:
            return {
                "success": False,
                "error": f"工具 {tool_id} 不存在"
            }
        
        # 验证参数
        validation_error = tool.validate_params(params)
        if validation_error:
            return {
                "success": False,
                "error": validation_error
            }
        
        try:
            result = tool.execute(params)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        获取当前平台信息
        
        Returns:
            平台信息字典
        """
        if self._config_registry:
            return self._config_registry.get_platform_info()
        
        from .config_driven_registry import PlatformDetector
        return {
            'platform': PlatformDetector.detect_platform(),
            'platform_name': PlatformDetector.get_platform_name(),
            'tool_count': len(self.get_all_tools())
        }
    
    def reload_config(self) -> None:
        """重新加载配置"""
        if self._config_registry:
            self._config_registry.reload_config()
    
    def clear(self) -> None:
        """清空注册器"""
        self._manual_tools.clear()
        if self._config_registry:
            self._config_registry.clear()
