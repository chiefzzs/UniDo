"""
配置驱动的工具注册器
根据平台配置自动加载和注册对应的工具
"""
import json
import os
import sys
from typing import Dict, Optional, List, Any
from src.tools.implement.base_tool import BaseTool
from src.tools.implement.tool_loader import ToolLoader, ToolLoaderError

class PlatformDetector:
    """平台检测器"""
    
    @staticmethod
    def detect_platform() -> str:
        """
        检测当前操作系统
        
        Returns:
            'windows', 'linux', 'macos', 或 fallback
        """
        platform = sys.platform
        if platform.startswith('win'):
            return 'windows'
        elif platform == 'darwin':
            return 'macos'
        elif platform.startswith('linux'):
            return 'linux'
        return 'linux'  # fallback to linux
    
    @staticmethod
    def get_platform_name() -> str:
        """获取友好的平台名称"""
        platform = PlatformDetector.detect_platform()
        names = {
            'windows': 'Windows',
            'linux': 'Linux',
            'macos': 'macOS'
        }
        return names.get(platform, 'Unknown')

class ConfigDrivenToolRegistry:
    """配置驱动的工具注册器"""
    
    def __init__(self, config_path: Optional[str] = None, force_platform: Optional[str] = None):
        """
        初始化配置驱动的工具注册器
        
        Args:
            config_path: 配置文件路径
            force_platform: 强制指定平台（用于测试）
        """
        self._config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()
        self._force_platform = force_platform
        
        self._tool_loader = ToolLoader()
        self._tools: Dict[str, BaseTool] = {}
        self._platform = self._determine_platform()
        self._platform_config = self._get_platform_config()
        
        self._registered = False
    
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        return os.path.join(project_root, 'config', 'platform_tools.json')
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self._config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件JSON解析错误: {e}")
    
    def _determine_platform(self) -> str:
        """确定使用的平台"""
        if self._force_platform:
            return self._force_platform
        
        if self._config.get('auto_detect', {}).get('enabled', True):
            detected = PlatformDetector.detect_platform()
            if detected in self._config['platforms']:
                return detected
        
        default = self._config.get('default_platform')
        if default == 'auto' or default not in self._config['platforms']:
            return self._config['auto_detect'].get('fallback_platform', 'linux')
        
        return default
    
    def _get_platform_config(self) -> dict:
        """获取当前平台的配置"""
        return self._config['platforms'].get(self._platform, {})
    
    def register_all_tools(self) -> None:
        """
        注册所有工具
        
        根据配置自动加载平台特定工具和通用工具，同时自动扫描工具目录
        """
        if self._registered:
            return
        
        print(f"[ConfigDrivenRegistry] 使用平台: {self._platform} ({self._platform_config.get('name', 'Unknown')})")
        
        # 获取模块映射
        module_mapping = self._config.get('module_mapping', {})
        
        # 注册平台特定工具
        tool_mapping = self._platform_config.get('tool_mapping', {})
        for tool_key, class_name in tool_mapping.items():
            self._register_tool(class_name, module_mapping.get(class_name))
        
        # 注册通用工具
        common_tools = self._platform_config.get('common_tools', [])
        for class_name in common_tools:
            self._register_tool(class_name, module_mapping.get(class_name))
        
        # 自动扫描工具目录中的所有工具类
        self._scan_and_register_tools()
        
        self._registered = True
        print(f"[ConfigDrivenRegistry] 注册完成，共 {len(self._tools)} 个工具")
    
    def _scan_and_register_tools(self) -> None:
        """
        自动扫描工具目录，注册所有BaseTool子类
        
        扫描 src/tools/implement 目录中的所有模块，自动发现并注册工具类
        """
        import inspect
        
        # 获取工具实现目录路径
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 遍历目录中的所有Python文件
        for filename in os.listdir(tools_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                module_name = filename[:-3]  # 去掉 .py
                full_module_path = f"src.tools.implement.{module_name}"
                
                try:
                    # 导入模块
                    module = __import__(full_module_path, fromlist=[''])
                    
                    # 遍历模块中的所有成员
                    for name, obj in inspect.getmembers(module):
                        # 检查是否是BaseTool的子类且不是抽象类
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseTool) and 
                            obj != BaseTool and
                            not inspect.isabstract(obj)):
                            # 尝试注册工具
                            try:
                                tool_instance = obj()
                                tool_id = str(tool_instance.tool_id)
                                
                                # 只有在工具ID或名称不存在时才注册
                                if tool_id not in self._tools and tool_instance.name.lower() not in self._tools:
                                    self._tools[tool_id] = tool_instance
                                    self._tools[tool_instance.name.lower()] = tool_instance
                                    print(f"[ConfigDrivenRegistry] ✓ 自动扫描注册: {name} (ID: {tool_id})")
                            except Exception as e:
                                print(f"[ConfigDrivenRegistry] ✗ 自动扫描注册失败 {name}: {e}")
                                
                except ImportError as e:
                    print(f"[ConfigDrivenRegistry] ✗ 导入模块失败 {module_name}: {e}")
                except Exception as e:
                    print(f"[ConfigDrivenRegistry] ✗ 扫描模块异常 {module_name}: {e}")
    
    def _register_tool(self, class_name: str, module_name: Optional[str] = None) -> bool:
        """
        注册单个工具
        
        Args:
            class_name: 类名
            module_name: 模块名
            
        Returns:
            是否成功
        """
        try:
            tool_instance = self._tool_loader.create_tool_instance(class_name, module_name)
            
            # 确保工具ID是字符串
            tool_id = str(tool_instance.tool_id)
            self._tools[tool_id] = tool_instance
            
            # 同时注册工具名称映射
            if tool_instance.name:
                self._tools[tool_instance.name.lower()] = tool_instance
            
            print(f"[ConfigDrivenRegistry] ✓ 注册工具: {class_name} (ID: {tool_id})")
            return True
            
        except ToolLoaderError as e:
            print(f"[ConfigDrivenRegistry] ✗ 注册失败 {class_name}: {e}")
            return False
        except Exception as e:
            print(f"[ConfigDrivenRegistry] ✗ 注册异常 {class_name}: {e}")
            return False
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """
        获取工具实例
        
        Args:
            tool_id: 工具ID或名称
            
        Returns:
            工具实例或None
        """
        if not self._registered:
            self.register_all_tools()
        
        # 尝试直接查找
        if tool_id in self._tools:
            return self._tools[tool_id]
        
        # 尝试小写查找
        tool_id_lower = tool_id.lower()
        if tool_id_lower in self._tools:
            return self._tools[tool_id_lower]
        
        # 尝试通过工具注册表查找
        tool_registry = self._config.get('tool_registry', {})
        if tool_id in tool_registry:
            mapped_id = tool_registry[tool_id]
            if mapped_id in self._tools:
                return self._tools[mapped_id]
        
        return None
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """通过名称获取工具"""
        return self.get_tool(name)
    
    def get_all_tools(self) -> List[BaseTool]:
        """获取所有工具"""
        if not self._registered:
            self.register_all_tools()
        
        # 去重
        seen_ids = set()
        tools = []
        for tool in self._tools.values():
            tool_id = str(tool.tool_id)
            if tool_id not in seen_ids:
                seen_ids.add(tool_id)
                tools.append(tool)
        
        return tools
    
    def get_tool_ids(self) -> List[str]:
        """获取所有工具ID"""
        tools = self.get_all_tools()
        return [str(tool.tool_id) for tool in tools]
    
    def get_platform(self) -> str:
        """获取当前平台"""
        return self._platform
    
    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息"""
        return {
            'platform': self._platform,
            'platform_name': self._platform_config.get('name', ''),
            'command_shell': self._platform_config.get('command_shell', []),
            'path_separator': self._platform_config.get('path_separator', '/'),
            'tool_count': len(self.get_all_tools())
        }
    
    def get_config(self) -> dict:
        """获取配置"""
        return self._config.copy()
    
    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()
        self._platform_config = self._get_platform_config()
        self._registered = False
        self._tools.clear()
        self._tool_loader.clear_cache()
    
    def clear(self) -> None:
        """清空注册器"""
        self._tools.clear()
        self._registered = False
    
    def has_tool(self, tool_id: str) -> bool:
        """检查工具是否存在"""
        return self.get_tool(tool_id) is not None
