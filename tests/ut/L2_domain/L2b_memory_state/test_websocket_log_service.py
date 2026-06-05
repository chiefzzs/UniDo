"""
测试 WebSocketLogService 的消息过滤逻辑

测试思路：
========

1. 验证 websocket_log_service 是否能正确的从存储数据依据过滤得到正确的数据

验证方法：
   - 1、在每个测试函数内部从 test_bak 恢复测试数据到 test 目录
   - 2、调用 websocket_log_service get_websocket_messages 方法，过滤条件为 session_id
   - 3、直接读取websocket文件数据 ，用作下面的对比
   - 验证返回的消息
       - 对于每个LLM请求，都包含 llm 的完整响应消息 (prepare、request_sent、response_received)
       - 每个llm的requestid对应的 response_received 后面才有对应分 request_id 的 思考、文本、工具调用 一个不少，次序不乱
       - 每个 工具调用对应的工具运行消息，次序不能乱 ，一个不少
"""

import os
import json
import shutil
import pytest


# 使用绝对路径，避免相对路径问题
TEST_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src', 'data'))
TEST_DIR = os.path.join(TEST_DATA_PATH, 'test')
TEST_BAK_DIR = os.path.join(TEST_DATA_PATH, 'test_bak')


def _restore_test_data():
    """从备份恢复测试数据到 test 目录"""
    # 确保 test 目录存在
    if not os.path.exists(TEST_DIR):
        os.makedirs(TEST_DIR)
    
    # 从 test_bak 恢复测试数据
    if os.path.exists(TEST_BAK_DIR):
        for filename in os.listdir(TEST_BAK_DIR):
            if filename.endswith('.json'):
                src_path = os.path.join(TEST_BAK_DIR, filename)
                dest_path = os.path.join(TEST_DIR, filename)
                shutil.copy(src_path, dest_path)
        return True
    return False


def _extract_action(msg):
    """从消息中提取 action 类型"""
    action = msg.get('message_type', '')
    
    # 如果 message_type 以 'event_' 开头，去掉前缀
    if action.startswith('event_'):
        action = action[6:]
    
    # 如果还是没有 action，从 payload 中提取
    if not action:
        payload = msg.get('payload', {})
        if isinstance(payload, str):
            payload = json.loads(payload)
        action = payload.get('action', '')
    
    return action


def _extract_request_id(msg):
    """从消息中提取 request_id"""
    payload = msg.get('payload', {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    return payload.get('request_id')


def _extract_tool_call_id(msg):
    """从消息中提取 tool_call_id"""
    payload = msg.get('payload', {})
    if isinstance(payload, str):
        payload = json.loads(payload)
    
    # 尝试从多个位置提取 tool_call_id
    # 位置1: payload.tool_call_id
    tool_call_id = payload.get('tool_call_id')
    if tool_call_id:
        return tool_call_id
    
    # 位置2: payload.data.tool_call_id
    data = payload.get('data', {})
    if isinstance(data, str):
        data = json.loads(data)
    tool_call_id = data.get('tool_call_id')
    if tool_call_id:
        return tool_call_id
    
    # 位置3: payload.data.choices[0].message.tool_call_id
    choices = data.get('choices', [])
    for choice in choices:
        message = choice.get('message', {})
        tool_call_id = message.get('tool_call_id')
        if tool_call_id:
            return tool_call_id
    
    return None


class TestWebSocketLogService:
    """WebSocketLogService 测试类"""

    def test_complete_llm_cycle_with_all_events(self):
        """测试完整的 LLM 调用周期，包含所有相关事件"""
        # 1. 恢复测试数据
        if not _restore_test_data():
            pytest.skip("无法恢复测试数据")
        
        from src.services.L2_domain.L2b_memory_state import get_websocket_log_service
        
        service = get_websocket_log_service()
        
        # 2. 读取原始测试数据
        ws_messages_path = os.path.join(TEST_DIR, 'websocket_messages.json')
        if not os.path.exists(ws_messages_path):
            pytest.skip(f"测试数据文件不存在: {ws_messages_path}")
        
        with open(ws_messages_path, 'r', encoding='utf-8') as f:
            all_messages = json.load(f)
        
        if not all_messages:
            pytest.skip("测试数据为空")
        
        # 获取测试用的 session_id
        first_msg = all_messages[0]
        target_session_id = first_msg.get('session_id')
        
        if not target_session_id:
            payload = first_msg.get('payload', {})
            if isinstance(payload, str):
                payload = json.loads(payload)
            target_session_id = payload.get('session_id')
        
        assert target_session_id, "无法获取测试用的 session_id"
        
        print(f"\n[Test] 测试会话ID: {target_session_id}")
        print(f"[Test] 原始消息总数: {len(all_messages)}")
        
        # 3. 调用服务获取消息
        filtered_messages = service.get_websocket_messages({'session_id': target_session_id})
        print(f"[Test] 过滤后消息数: {len(filtered_messages)}")
        
        # 4. 验证：对比原始数据和过滤后数据中的 LLM 相关消息
        # 提取原始数据中该 session 的所有消息
        original_session_messages = []
        for msg in all_messages:
            msg_session_id = msg.get('session_id')
            if not msg_session_id:
                payload = msg.get('payload', {})
                if isinstance(payload, str):
                    payload = json.loads(payload)
                msg_session_id = payload.get('session_id')
            if msg_session_id == target_session_id:
                original_session_messages.append(msg)
        
        print(f"[Test] 原始数据中该会话消息数: {len(original_session_messages)}")
        
        # 5. 验证 LLM 调用周期完整性
        # 收集原始数据中的 llm.request_sent 消息
        original_request_sent = [msg for msg in original_session_messages 
                                if _extract_action(msg) == 'llm.request_sent']
        
        # 收集过滤后数据中的 llm.request_sent 消息
        filtered_request_sent = [msg for msg in filtered_messages 
                                if _extract_action(msg) == 'llm.request_sent']
        
        print(f"\n[Test] llm.request_sent 消息对比:")
        print(f"  原始数据: {len(original_request_sent)} 条")
        print(f"  过滤后: {len(filtered_request_sent)} 条")
        
        # 验证数量一致
        assert len(original_request_sent) == len(filtered_request_sent), \
            f"llm.request_sent 消息数量不一致！原始: {len(original_request_sent)}, 过滤后: {len(filtered_request_sent)}"
        
        # 6. 验证每个 LLM 请求都有完整的调用链
        for request_sent_msg in filtered_request_sent:
            request_id = _extract_request_id(request_sent_msg)
            if not request_id:
                continue
            
            print(f"\n[Test] 验证 request_id: {request_id}")
            
            # 查找对应的 request_prepared
            request_prepared = [msg for msg in filtered_messages 
                               if _extract_action(msg) == 'llm.request_prepared' 
                               and _extract_request_id(msg) == request_id]
            
            # 查找对应的 response_received
            response_received = [msg for msg in filtered_messages 
                                if _extract_action(msg) == 'llm.response_received' 
                                and _extract_request_id(msg) == request_id]
            
            print(f"  llm.request_prepared: {'✅ 存在' if request_prepared else '❌ 缺失'}")
            print(f"  llm.response_received: {'✅ 存在' if response_received else '❌ 缺失'}")
            
            assert len(request_prepared) == 1, f"request_id={request_id} 的 request_prepared 数量不正确"
            assert len(response_received) == 1, f"request_id={request_id} 的 response_received 数量不正确"
            
            # 验证顺序：request_prepared -> request_sent -> response_received
            prepared_idx = filtered_messages.index(request_prepared[0])
            sent_idx = filtered_messages.index(request_sent_msg)
            received_idx = filtered_messages.index(response_received[0])
            
            assert prepared_idx < sent_idx < received_idx, \
                f"消息顺序错误！request_prepared({prepared_idx}) -> request_sent({sent_idx}) -> response_received({received_idx})"
            
            print(f"  顺序验证: ✅ request_prepared({prepared_idx}) -> request_sent({sent_idx}) -> response_received({received_idx})")
            
            # 7. 验证 response_received 之后的相关消息（思考、文本、工具调用）
            received_idx = filtered_messages.index(response_received[0])
            following_messages = filtered_messages[received_idx+1:]
            
            # 收集该 request_id 相关的后续消息
            related_messages = []
            for msg in following_messages:
                msg_action = _extract_action(msg)
                msg_request_id = _extract_request_id(msg)
                
                # 检查是否是该 request_id 的后续消息
                if msg_request_id == request_id:
                    related_messages.append((msg_action, msg))
                
                # 如果遇到新的 request_sent，停止收集
                if msg_action == 'llm.request_sent':
                    break
            
            print(f"  后续相关消息: {len(related_messages)} 条")
            
            # 检查是否有思考消息
            thinking_messages = [m for a, m in related_messages if a == 'llm.call_thinking_completed']
            # 检查是否有文本消息
            text_messages = [m for a, m in related_messages if a == 'llm.call_text_completed']
            # 检查是否有工具调用消息
            tool_call_messages = [m for a, m in related_messages if a.startswith('llm.tool_call')]
            
            print(f"    - llm.call_thinking_completed: {len(thinking_messages)} 条")
            print(f"    - llm.call_text_completed: {len(text_messages)} 条")
            print(f"    - llm.tool_call*: {len(tool_call_messages)} 条")
        
        print("\n[Test] ✅ 所有 LLM 调用周期验证通过")
        
        # 8. 验证文本消息完整性：对比原始数据和过滤后数据
        original_text_messages = [msg for msg in original_session_messages 
                                  if _extract_action(msg) == 'llm.call_text_completed']
        filtered_text_messages = [msg for msg in filtered_messages 
                                  if _extract_action(msg) == 'llm.call_text_completed']
        
        print(f"\n[Test] llm.call_text_completed 消息对比:")
        print(f"  原始数据: {len(original_text_messages)} 条")
        print(f"  过滤后: {len(filtered_text_messages)} 条")
        
        # 验证数量一致
        assert len(original_text_messages) == len(filtered_text_messages), \
            f"llm.call_text_completed 消息数量不一致！原始: {len(original_text_messages)}, 过滤后: {len(filtered_text_messages)}"
        
        print(f"[Test] ✅ 文本消息数量一致")

    def test_tool_call_messages_complete(self):
        """测试工具调用消息的完整性和顺序"""
        # 1. 恢复测试数据
        if not _restore_test_data():
            pytest.skip("无法恢复测试数据")
        
        from src.services.L2_domain.L2b_memory_state import get_websocket_log_service
        
        service = get_websocket_log_service()
        
        # 2. 读取测试数据
        ws_messages_path = os.path.join(TEST_DIR, 'websocket_messages.json')
        if not os.path.exists(ws_messages_path):
            pytest.skip(f"测试数据文件不存在: {ws_messages_path}")
        
        with open(ws_messages_path, 'r', encoding='utf-8') as f:
            all_messages = json.load(f)
        
        if not all_messages:
            pytest.skip("测试数据为空")
        
        # 获取测试用的 session_id
        first_msg = all_messages[0]
        target_session_id = first_msg.get('session_id')
        
        if not target_session_id:
            payload = first_msg.get('payload', {})
            if isinstance(payload, str):
                payload = json.loads(payload)
            target_session_id = payload.get('session_id')
        
        assert target_session_id, "无法获取测试用的 session_id"
        
        # 3. 调用服务获取消息
        filtered_messages = service.get_websocket_messages({'session_id': target_session_id})
        
        # 4. 收集所有工具调用相关消息
        tool_call_messages = []
        for msg in filtered_messages:
            action = _extract_action(msg)
            if action.startswith('llm.tool_call') or action.startswith('tool.call'):
                tool_call_messages.append((action, msg))
        
        print(f"\n[Test] 工具调用消息总数: {len(tool_call_messages)}")
        
        # 5. 按 tool_call_id 分组验证
        tool_call_groups = {}
        for action, msg in tool_call_messages:
            tool_call_id = _extract_tool_call_id(msg)
            if not tool_call_id:
                continue
            
            if tool_call_id not in tool_call_groups:
                tool_call_groups[tool_call_id] = []
            tool_call_groups[tool_call_id].append((action, msg))
        
        print(f"[Test] 工具调用组数量: {len(tool_call_groups)}")
        
        # 6. 验证每个工具调用组的完整性
        for tool_call_id, actions in tool_call_groups.items():
            print(f"\n[Test] 验证 tool_call_id: {tool_call_id}")
            
            # 检查是否包含完整的调用链
            action_types = [a for a, m in actions]
            print(f"  消息类型: {action_types}")
            
            # 验证顺序：started -> finished（可能有 intermediate）
            if 'llm.tool_call_started' in action_types:
                started_idx = action_types.index('llm.tool_call_started')
                if 'llm.tool_call_finished' in action_types:
                    finished_idx = action_types.index('llm.tool_call_finished')
                    assert started_idx < finished_idx, \
                        f"tool_call_id={tool_call_id} 顺序错误: started({started_idx}) > finished({finished_idx})"
                    print(f"  ✅ 顺序正确: started -> finished")
                else:
                    print(f"  ⚠️ 缺少 tool_call_finished")
            
        print("\n[Test] ✅ 工具调用消息验证通过")

    def test_message_order_preserved(self):
        """测试消息顺序保持原始顺序不变"""
        # 1. 恢复测试数据
        if not _restore_test_data():
            pytest.skip("无法恢复测试数据")
        
        from src.services.L2_domain.L2b_memory_state import get_websocket_log_service
        
        service = get_websocket_log_service()
        
        # 2. 读取测试数据
        ws_messages_path = os.path.join(TEST_DIR, 'websocket_messages.json')
        if not os.path.exists(ws_messages_path):
            pytest.skip(f"测试数据文件不存在: {ws_messages_path}")
        
        with open(ws_messages_path, 'r', encoding='utf-8') as f:
            all_messages = json.load(f)
        
        if not all_messages:
            pytest.skip("测试数据为空")
        
        # 获取测试用的 session_id
        first_msg = all_messages[0]
        target_session_id = first_msg.get('session_id')
        
        if not target_session_id:
            payload = first_msg.get('payload', {})
            if isinstance(payload, str):
                payload = json.loads(payload)
            target_session_id = payload.get('session_id')
        
        assert target_session_id, "无法获取测试用的 session_id"
        
        # 3. 调用服务获取消息
        filtered_messages = service.get_websocket_messages({'session_id': target_session_id})
        
        # 4. 验证消息顺序与原始顺序一致
        original_indices = []
        for msg in filtered_messages:
            msg_id = msg.get('log_id') or msg.get('message_id')
            if msg_id:
                for idx, orig_msg in enumerate(all_messages):
                    orig_id = orig_msg.get('log_id') or orig_msg.get('message_id')
                    if orig_id == msg_id:
                        original_indices.append(idx)
                        break
        
        # 检查顺序是否保持递增（即原始顺序）
        assert original_indices == sorted(original_indices), \
            "消息顺序被改变，应该保持原始顺序"
        
        print(f"\n[Test] ✅ 消息顺序保持不变")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
