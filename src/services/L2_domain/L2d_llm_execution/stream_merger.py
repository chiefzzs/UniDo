"""
L2d LLM Execution Service - Stream Merger

流式响应合并器，负责合并流式响应的多个chunk。

支持三类流式数据：
- reasoning_content: 思考过程（仅实时展示，不存储）
- content: 文本内容（完整保留）
- tool_calls: 工具调用（完整保留）
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class StreamMerger:
    """
    流式响应合并器
    
    负责合并流式输出的三类数据：
    - reasoning_content: 思考过程（仅实时展示，不存储）
    - content: 文本内容（完整保留）
    - tool_calls: 工具调用（完整保留）
    """
    content: str = ""
    reasoning_content: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    finish_reason: str = None
    
    def process_chunk(self, chunk: Dict) -> Optional[Dict]:
        """
        处理单个流式chunk
        
        Args:
            chunk: 流式响应的单个chunk
            
        Returns:
            需要实时转发的数据（思考内容或文本内容）
        """
        delta = chunk.get('delta', {})
        if not delta:
            # 尝试从顶层获取delta（旧格式兼容）
            delta = chunk.get('delta', '')
            if isinstance(delta, str):
                self.content += delta
                return {"type": "content", "content": delta}
            return None
        
        # 处理 reasoning_content（思考数据）
        if 'reasoning_content' in delta and delta['reasoning_content']:
            self.reasoning_content += delta['reasoning_content']
            return {"type": "thinking", "content": delta['reasoning_content']}
        
        # 处理 content（文本数据）
        if 'content' in delta and delta['content']:
            self.content += delta['content']
            return {"type": "content", "content": delta['content']}
        
        # 处理 tool_calls（工具数据）
        if 'tool_calls' in delta:
            self._merge_tool_calls(delta['tool_calls'])
        
        # 处理 finish_reason
        if 'finish_reason' in delta:
            self.finish_reason = delta['finish_reason']
        
        return None
    
    def _merge_tool_calls(self, tool_calls: List[Dict]):
        """
        合并tool_calls，特别是arguments的流式输出
        
        Args:
            tool_calls: 工具调用列表
        """
        for tool_call in tool_calls:
            # 查找是否已存在相同index的tool_call
            existing = next((tc for tc in self.tool_calls 
                           if tc.get('index') == tool_call.get('index')), None)
            
            if existing:
                # 累积arguments
                if 'function' in tool_call and 'arguments' in tool_call['function']:
                    existing['function']['arguments'] += tool_call['function']['arguments']
            else:
                # 新增tool_call
                self.tool_calls.append(tool_call)
    
    def get_final_message(self) -> Dict:
        """
        获取合并后的最终assistant消息
        
        Returns:
            完整的assistant消息字典
        """
        return {
            "role": "assistant",
            "content": self.content,
            "tool_calls": self.tool_calls if self.tool_calls else None,
            "finish_reason": self.finish_reason
        }
    
    def reset(self):
        """重置状态"""
        self.content = ""
        self.reasoning_content = ""
        self.tool_calls = []
        self.finish_reason = None
