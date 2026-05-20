"""
Grep工具实现
"""
import re
import os
from typing import Dict, Any, List
from .base_tool import BaseTool


class GrepTool(BaseTool):
    """
    基于正则表达式的文本搜索工具
    """
    
    def __init__(self):
        super().__init__()
        self.tool_id = "T05"
        self.name = "Grep"
        self.category = "Search"
        self.load_description()
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行文本搜索
        
        Args:
            params: 工具参数，包含 pattern, path, glob, output_mode, type, -i, -n, -C, head_limit 字段
            
        Returns:
            搜索结果
        """
        pattern = params.get("pattern", "")
        path = params.get("path", "") or "."
        output_mode = params.get("output_mode", "content")
        case_insensitive = params.get("-i", False)
        show_line_numbers = params.get("-n", False)
        context_lines = params.get("-C", 0)
        head_limit = params.get("head_limit", 100)
        
        if not pattern:
            return {"error": "搜索模式不能为空"}
        
        try:
            flags = re.IGNORECASE if case_insensitive else 0
            regex = re.compile(pattern, flags)
            
            results = []
            file_count = 0
            match_count = 0
            
            # 遍历目录
            for root, dirs, files in os.walk(path):
                for filename in files:
                    # 简单的类型过滤
                    if output_mode == "files_with_matches":
                        file_path = os.path.join(root, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if regex.search(content):
                                    file_count += 1
                                    results.append(file_path)
                        except Exception:
                            continue
                    else:
                        file_path = os.path.join(root, filename)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                lines = f.readlines()
                                for i, line in enumerate(lines, 1):
                                    if regex.search(line):
                                        match_count += 1
                                        result = {
                                            "file": file_path,
                                            "line": i,
                                            "content": line.strip()
                                        }
                                        # 添加上下文
                                        if context_lines > 0:
                                            context = []
                                            start = max(1, i - context_lines)
                                            end = min(len(lines), i + context_lines)
                                            for j in range(start - 1, end):
                                                prefix = ">" if j + 1 == i else " "
                                                context.append({
                                                    "line": j + 1,
                                                    "content": lines[j].strip(),
                                                    "is_match": j + 1 == i
                                                })
                                            result["context"] = context
                                        results.append(result)
                        except Exception:
                            continue
                    
                    # 限制结果数量
                    if head_limit and len(results) >= head_limit:
                        break
                if head_limit and len(results) >= head_limit:
                    break
            
            if output_mode == "count":
                return {
                    "pattern": pattern,
                    "path": path,
                    "match_count": match_count,
                    "file_count": file_count
                }
            
            return {
                "pattern": pattern,
                "path": path,
                "results": results[:head_limit] if head_limit else results,
                "total_matches": match_count,
                "total_files": file_count
            }
        except Exception as e:
            return {"error": str(e)}
