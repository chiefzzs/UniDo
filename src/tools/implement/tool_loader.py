"""
工具动态加载器
根据配置动态加载工具模块和类
"""
import importlib
import importlib.util
import os
import sys
from typing import Dict, Type, Optional, Any
from src.tools.implement.base_tool import BaseTool

class ToolLoaderError(Exception):
    """工具加载错误"""
    pass

class ToolLoader:
    """工具动态加载器"""
    
    def __init__(self, tools_package: str = "src.tools.implement"):
        """
        初始化工具加载器
        
        Args:
            tools_package: 工具包路径
        """
        self._tools_package = tools_package
        self._module_cache: Dict[str, Any] = {}
        self._class_cache: Dict[str, Type[BaseTool]] = {}
        
        # 确保项目根目录在路径中
        self._ensure_project_in_path()
    
    def _ensure_project_in_path(self):
        """确保项目根目录在sys.path中"""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
    
    def load_tool_class(self, class_name: str, module_name: Optional[str] = None) -> Type[BaseTool]:
        """
        加载工具类
        
        Args:
            class_name: 工具类名
            module_name: 模块名（如果为None则根据class_name推断）
            
        Returns:
            工具类
            
        Raises:
            ToolLoaderError: 加载失败
        """
        # 检查缓存
        cache_key = f"{class_name}:{module_name or 'auto'}"
        if cache_key in self._class_cache:
            return self._class_cache[cache_key]
        
        try:
            # 确定模块名
            if module_name is None:
                module_name = self._infer_module_name(class_name)
            
            # 完整模块路径
            full_module_name = f"{self._tools_package}.{module_name}"
            
            # 加载模块
            if full_module_name in self._module_cache:
                module = self._module_cache[full_module_name]
            else:
                module = importlib.import_module(full_module_name)
                self._module_cache[full_module_name] = module
            
            # 获取类
            tool_class = getattr(module, class_name)
            
            # 验证类
            if not isinstance(tool_class, type) or not issubclass(tool_class, BaseTool):
                raise ToolLoaderError(f"{class_name} 不是有效的BaseTool子类")
            
            # 缓存
            self._class_cache[cache_key] = tool_class
            
            return tool_class
            
        except ImportError as e:
            raise ToolLoaderError(f"无法导入模块 {module_name}: {e}")
        except AttributeError as e:
            raise ToolLoaderError(f"模块 {module_name} 中找不到类 {class_name}: {e}")
        except Exception as e:
            raise ToolLoaderError(f"加载工具 {class_name} 失败: {e}")
    
    def _infer_module_name(self, class_name: str) -> str:
        """
        根据类名推断模块名
        
        Args:
            class_name: 类名（如 WindowsLsTool）
            
        Returns:
            模块名（如 windows_ls_tool）
        """
        # 转换为 snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
        # 去掉 _tool 后缀
        if snake_case.endswith('_tool'):
            snake_case = snake_case[:-5]
        
        return snake_case + '_tool'
    
    def create_tool_instance(self, class_name: str, module_name: Optional[str] = None) -> BaseTool:
        """
        创建工具实例
        
        Args:
            class_name: 工具类名
            module_name: 模块名
            
        Returns:
            工具实例
        """
        tool_class = self.load_tool_class(class_name, module_name)
        return tool_class()
    
    def load_tool_from_file(self, file_path: str, class_name: str) -> Type[BaseTool]:
        """
        从文件直接加载工具类
        
        Args:
            file_path: Python文件路径
            class_name: 类名
            
        Returns:
            工具类
        """
        try:
            spec = importlib.util.spec_from_file_location(class_name, file_path)
            if spec is None or spec.loader is None:
                raise ToolLoaderError(f"无法创建模块spec: {file_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            tool_class = getattr(module, class_name)
            
            if not isinstance(tool_class, type) or not issubclass(tool_class, BaseTool):
                raise ToolLoaderError(f"{class_name} 不是有效的BaseTool子类")
            
            return tool_class
            
        except Exception as e:
            raise ToolLoaderError(f"从文件加载工具失败 {file_path}: {e}")
    
    def clear_cache(self):
        """清空缓存"""
        self._module_cache.clear()
        self._class_cache.clear()
    
    def get_loaded_modules(self) -> list:
        """获取已加载的模块列表"""
        return list(self._module_cache.keys())
    
    def get_loaded_classes(self) -> list:
        """获取已加载的类列表"""
        return list(self._class_cache.keys())
