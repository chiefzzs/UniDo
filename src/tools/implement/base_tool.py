"""
工具基类模块
"""
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseTool(ABC):
    """
    所有工具的基类
    """
    
    def __init__(self):
        self.tool_id: str = ""
        self.name: str = ""
        self.category: str = ""
        self.description: str = ""
        self.description_zh: str = ""
        self.parameters: Dict[str, Any] = {}
        self.default_params: Dict[str, Any] = {}
        self.examples: list = []
        self.examples_zh: list = []
    
    def _decode_output(self, output: bytes) -> str:
        """
        智能解码输出，支持多种编码格式，确保不乱码
        
        Args:
            output: 原始字节输出
            
        Returns:
            解码后的字符串
        """
        if isinstance(output, str):
            return output
        
        # 按优先级尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'cp1252', 'utf-16']
        
        for encoding in encodings:
            try:
                return output.decode(encoding)
            except (UnicodeDecodeError, TypeError):
                continue
        
        # 如果所有编码都失败，使用 'replace' 模式处理
        try:
            return output.decode('utf-8', errors='replace')
        except:
            return str(output)
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具
        
        Args:
            params: 工具参数
            
        Returns:
            执行结果字典，包含 'success' 和 'result' 或 'error' 字段
        """
        pass
    
    def get_description(self) -> Dict[str, Any]:
        """
        获取工具描述信息
        
        Returns:
            工具描述字典
        """
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "category": self.category,
            "parameters": self.parameters,
            "description": self.description,
            "description_zh": self.description_zh,
            "default_params": self.default_params,
            "examples": self.examples,
            "examples_zh": self.examples_zh
        }
    
    def load_description(self, lang: str = "en") -> None:
        """
        从JSON文件加载工具描述
        
        Args:
            lang: 语言代码 ("en" 或 "zh")
        """
        desc_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "descriptions",
            lang
        )
        file_path = os.path.join(desc_dir, f"{self.tool_id}.json")
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.name = data.get("name", self.name)
                self.category = data.get("category", self.category)
                self.parameters = data.get("parameters", self.parameters)
                self.description = data.get("description", self.description)
                self.description_zh = data.get("description_zh", self.description_zh)
                self.default_params = data.get("default_params", self.default_params)
                self.examples = data.get("examples", self.examples)
                self.examples_zh = data.get("examples_zh", self.examples_zh)
    
    def get_default_params(self) -> Dict[str, Any]:
        """
        获取默认参数，用于调试模式
        
        Returns:
            默认参数字典
        """
        return self.default_params.copy()
    
    def validate_params(self, params: Dict[str, Any]) -> Optional[str]:
        """
        验证参数
        
        Args:
            params: 待验证的参数
            
        Returns:
            错误信息，如果验证通过则返回None
        """
        for param_name, param_spec in self.parameters.items():
            if param_spec.get("required", False) and param_name not in params:
                return f"缺少必需参数: {param_name}"
            if param_name in params:
                value = params[param_name]
                expected_type = param_spec.get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return f"参数 {param_name} 应为字符串类型"
                elif expected_type == "integer" and not isinstance(value, int):
                    return f"参数 {param_name} 应为整数类型"
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return f"参数 {param_name} 应为布尔类型"
                elif expected_type == "array" and not isinstance(value, list):
                    return f"参数 {param_name} 应为数组类型"
        return None
