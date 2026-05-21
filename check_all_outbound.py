import json

# 读取websocket消息
with open('d:/learnning/260521/src/data/dev/websocket_messages.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

print("=" * 80)
print("所有发送出去的消息（outbound）")
print("=" * 80)

outbound_count = 0
for msg in messages:
    if msg.get('direction') == 'outbound':
        outbound_count += 1
        payload_str = msg.get('payload', '')
        print(f"\n[{outbound_count}] 时间: {msg.get('created_at')}")
        print(f"消息类型: {msg.get('message_type')}")
        print(f"内容预览:")
        try:
            payload = json.loads(payload_str)
            print(json.dumps(payload, ensure_ascii=False, indent=2)[:800])
        except:
            print(payload_str[:500])
        print("-" * 80)

print(f"\n总共发送了 {outbound_count} 条消息")
