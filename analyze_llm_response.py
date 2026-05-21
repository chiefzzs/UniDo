import json

# 分析 LLM 响应中的工具调用
with open('d:/learnning/260521/src/data/dev/llm_calls.json', encoding='utf-8') as f:
    data = json.load(f)

print('=== LLM响应分析 ===')
for i, call in enumerate(data):
    response = call.get('response', {})
    tool_calls = response.get('tool_calls', [])
    finish_reason = response.get('finish_reason', '')
    content = response.get('content', '')
    
    print(f'\n调用 {i+1}:')
    print(f'  finish_reason: {finish_reason}')
    print(f'  content 长度: {len(str(content))}')
    print(f'  tool_calls 数量: {len(tool_calls)}')
    
    if tool_calls:
        for tc in tool_calls:
            # 尝试多种格式获取工具名
            name = tc.get('name', '')
            if not name:
                func = tc.get('function', {})
                name = func.get('name', '未知')
            
            # 尝试多种格式获取参数
            args = tc.get('arguments', '')
            if not args:
                func = tc.get('function', {})
                args = func.get('arguments', '')
            
            print(f'    - 工具名: {name}')
            print(f'      参数: {args[:50]}...')

# 清理临时文件
import os
if os.path.exists('d:/learnning/260521/analyze_data.py'):
    os.remove('d:/learnning/260521/analyze_data.py')