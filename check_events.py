import json

# 读取websocket消息
with open('d:/learnning/260521/src/data/dev/websocket_messages.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

print("=" * 80)
print("查找所有工具执行相关的事件")
print("=" * 80)

for msg in messages:
    if msg.get('direction') == 'outbound':
        payload_str = msg.get('payload', '')
        if payload_str:
            try:
                payload = json.loads(payload_str)
                event_type = payload.get('type') or payload.get('event_type')

                # 检查是否是工具执行相关的事件
                if event_type and ('tool' in str(event_type).lower() or 'execution' in str(event_type).lower()):
                    print(f"\n时间: {msg.get('created_at')}")
                    print(f"事件类型: {event_type}")
                    print(f"消息内容预览:")
                    print(json.dumps(payload, ensure_ascii=False, indent=2)[:500])
                    print("...")
            except:
                pass

print("\n" + "=" * 80)
print("检查完成")
print("=" * 80)
