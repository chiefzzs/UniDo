import json

# 读取websocket消息
with open('d:/learnning/260521/src/data/dev/websocket_messages.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

# 找到message_response消息
for msg in messages:
    if msg.get('message_type') == 'message_response':
        payload_str = msg['payload']
        payload = json.loads(payload_str)

        print("=" * 80)
        print("消息结构分析")
        print("=" * 80)
        print(f"type: {payload.get('type')}")
        print(f"status: {payload.get('status')}")
        print(f"session_id: {payload.get('session_id')}")
        print()

        data = payload.get('data', {})
        print("data:")
        print(f"  content: {data.get('content')[:100]}..." if len(data.get('content', '')) > 100 else f"  content: {data.get('content')}")
        print(f"  type: {data.get('type')}")
        print()

        tool_calls = data.get('tool_calls', [])
        print(f"tool_calls 数量: {len(tool_calls)}")
        for i, tc in enumerate(tool_calls):
            print(f"\n工具调用 {i+1}:")
            print(f"  tool_name: {tc.get('tool_name')}")
            print(f"  call_id: {tc.get('call_id')}")
            print(f"  arguments: {tc.get('arguments')}")
            print(f"  status: {tc.get('status')}")
            print(f"  result: {str(tc.get('result'))[:100]}..." if len(str(tc.get('result', ''))) > 100 else f"  result: {tc.get('result')}")
            print(f"  error: {tc.get('error')}")

        print("\n" + "=" * 80)
        print("✅ 消息结构检查")
        print("=" * 80)

        # 检查必需字段
        issues = []
        if not payload.get('type'):
            issues.append("❌ 缺少 type 字段")
        if not payload.get('status'):
            issues.append("❌ 缺少 status 字段")
        if not payload.get('session_id'):
            issues.append("❌ 缺少 session_id 字段")
        if 'data' not in payload:
            issues.append("❌ 缺少 data 字段")
        else:
            if not payload['data'].get('type'):
                issues.append("❌ data.type 字段缺失或为空")
            if not payload['data'].get('tool_calls'):
                issues.append("⚠️  data.tool_calls 字段为空")
            else:
                for i, tc in enumerate(payload['data']['tool_calls']):
                    if not tc.get('call_id'):
                        issues.append(f"❌ tool_calls[{i}].call_id 缺失")
                    if not tc.get('tool_name'):
                        issues.append(f"❌ tool_calls[{i}].tool_name 缺失")

        if issues:
            for issue in issues:
                print(issue)
        else:
            print("✅ 所有必需字段都存在")
            print("✅ call_id 字段存在且正确")
            print("✅ tool_calls 数据完整")

        break
