/**
 * ChatManager - 对话管理器
 * 负责处理WebSocket消息和事件转发
 */
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ChatManager = {
    initialized: false,
    messageLog: [],  // 记录消息处理历史，用于测试调试

    // ========== 初始化方法 ==========

    init() {
        if (this.initialized) return;
        console.log(`%c[ChatManager] 🚀 初始化 ChatManager`, 'color: #2196F3; font-weight: bold');
        
        // 调试：检查 EventBus 是否可用
        if (!EventBus) {
            console.error(`%c[ChatManager] ❌ EventBus 不可用!`, 'color: #F44336; font-weight: bold');
            return;
        }
        console.log(`%c[ChatManager] ✅ EventBus 可用`, 'color: #4CAF50');
        
        // 监听 WebSocket 消息
        EventBus.on('ws:message', (data) => {
            console.log(`%c[ChatManager] 📥 收到 ws:message 事件`, 'color: #2196F3');
            this.handleWebSocketMessage(data);
        });
        
        this.initialized = true;
        console.log(`%c[ChatManager] ✅ ChatManager 初始化完成`, 'color: #4CAF50; font-weight: bold');
    },

    // ========== 消息处理方法 ==========

    // 数据校验函数
    validateEventData(action, data) {
        const requiredFieldsMap = {
            'session.created': ['session_id'],
            'client.message_received': ['session_id', 'content'],
            'dialog.created': ['session_id', 'dialog_id'],
            'llm.request_sent': ['session_id', 'request_id', 'dialog_id'],
            'llm.call_thinking': ['request_id'],
            'llm.call_thinking_completed': ['request_id', 'thinking'],
            'llm.call_reasoning': ['request_id'],
            'llm.call_reasoning_completed': ['request_id', 'reasoning'],
            'llm.call_text': ['request_id', 'content'],
            'llm.call_text_completed': ['request_id', 'content'],
            'llm.call_completed': ['request_id'],
            'tool.call_started': ['call_id', 'tool_name'],  // request_id 和 parameters 改为可选（后台数据格式）
            'tool.execution_output': ['call_id', 'output'],
            'tool.execution_output_end': ['call_id'],
            'tool.call_completed': ['call_id']  // result 和 status 改为可选（后台数据格式）
        };

        const requiredFields = requiredFieldsMap[action];
        if (!requiredFields) return true; // 没有定义必需字段的事件，跳过校验

        const missingFields = requiredFields.filter(field => {
            // 先检查外层 data，再检查内层 data.data
            let value = data[field];
            if (value === undefined || value === null || value === '') {
                value = data.data?.[field];
            }
            return value === undefined || value === null || value === '';
        });

        if (missingFields.length > 0) {
            console.error(`%c[ChatManager] ❌ [DATA_ERROR] 缺少必需字段: ${missingFields.join(', ')} in ${action}`, 'color: #F44336; font-weight: bold');
            console.error(`%c[ChatManager] ❌ [DATA_ERROR_DETAIL]`, 'color: #F44336', {
                action: action,
                missingFields: missingFields,
                receivedData: data,
                timestamp: Date.now()
            });
            console.warn(`%c[ChatManager] ⚠️ [FLOW_STOPPED] 数据校验失败，终止处理流程`, 'color: #FF9800; font-weight: bold');
            return false;
        }

        return true;
    },

    // 处理 WebSocket 消息
    handleWebSocketMessage(data) {
        const action = data.action || data.type;
        const sessionId = StateManager.getState('currentSessionId');
        
        // 记录消息日志
        this.messageLog.push({
            action,
            timestamp: Date.now(),
            data: { ...data }
        });
        
        console.log(`%c[ChatManager] 📤 [EVENT_RECEIVED] ${action}`, 'color: #2196F3');
        console.log(`%c[ChatManager] 📤 [EVENT_DATA]`, 'color: #2196F3', JSON.stringify(data, null, 2));
        
        if (!action) {
            console.error(`%c[ChatManager] ❌ [DATA_ERROR] 事件名称格式错误: ${action}`, 'color: #F44336; font-weight: bold');
            return;
        }

        // 数据校验
        if (!this.validateEventData(action, data)) {
            return;
        }

        // 判断是否为当前会话的消息
        const msgSessionId = data.session_id || data.sessionId;
        if (msgSessionId && sessionId && msgSessionId !== sessionId) {
            console.log(`%c[ChatManager] ⏭️ 跳过非当前会话消息: ${msgSessionId}`, 'color: #9E9E9E');
            return;
        }

        // 处理消息
        let wasHandled = false;
        
        // 转发创建类消息
        wasHandled = this.emitCreationMessage(action, data, sessionId) || wasHandled;
        
        // 转发更新类消息
        wasHandled = this.emitUpdateMessage(action, data, sessionId) || wasHandled;
        
        // 转发失败类消息
        wasHandled = this.emitFailedMessage(action, data, sessionId) || wasHandled;
        
        // 转发结束类消息
        wasHandled = this.emitEndMessage(action, data, sessionId) || wasHandled;

        if (!wasHandled) {
            console.log(`%c[ChatManager] 📭 未处理的消息: ${action}`, 'color: #795548');
        }
    },

    // ========== 消息转发方法 ==========

    // 转发创建类消息
    emitCreationMessage(action, data, currentSessionId) {
        const creationMap = {
            'session.created': 'event.session.created',
            'client.message_received': 'event.client.message_received',
            'dialog.created': 'event.dialog.created',
            'llm.request_sent': 'event.llm.request_sent',
            'tool.call_started': 'event.tool.call_started'
        };

        const eventName = creationMap[action];
        if (eventName) {
            // 合并外层和内层data，使字段都在顶层
            const mergedData = {
                ...data,
                ...data.data,  // 合并内层data
                __currentSessionId: currentSessionId
            };
            
            console.log(`%c[ChatManager] 👶 转发创建类消息: ${action} → ${eventName}`, 'color: #00BCD4');
            console.log(`%c[ChatManager]   └── 数据摘要: session_id=${mergedData.session_id}, dialog_id=${mergedData.dialog_id}, request_id=${mergedData.request_id}`, 'color: #00BCD4');
            EventBus.emit(eventName, mergedData);
            return true;
        }
        return false;
    },
    
    // 转发失败类消息
    emitFailedMessage(action, data, currentSessionId) {
        const failedMap = {
            'llm.call_failed': 'event.llm.call_failed',
            'llm.response_classified': 'event.llm.response_classified'
        };

        const eventName = failedMap[action];
        if (eventName) {
            // 合并外层和内层data，使字段都在顶层
            const mergedData = {
                ...data,
                ...data.data,
                __currentSessionId: currentSessionId
            };
            console.log(`%c[ChatManager] ❌ 转发失败类消息: ${action} → ${eventName}`, 'color: #F44336');
            EventBus.emit(eventName, mergedData);
            return true;
        }
        return false;
    },

    // 转发更新类消息
    emitUpdateMessage(action, data, currentSessionId) {
        const updateMap = {
            'llm.call_thinking': 'event.llm.call_thinking',
            'llm.call_reasoning': 'event.llm.call_reasoning',
            'llm.call_text': 'event.llm.call_text',
            'tool.execution_output': 'event.tool.execution_output',
            'event.tool.execution_output': 'event.tool.execution_output'
        };

        const eventName = updateMap[action];
        if (eventName) {
            // 合并外层和内层data，使字段都在顶层
            const mergedData = {
                ...data,
                ...data.data,
                __currentSessionId: currentSessionId
            };
            console.log(`%c[ChatManager] 🔄 转发更新类消息: ${action} → ${eventName}`, 'color: #8BC34A');
            EventBus.emit(eventName, mergedData);
            return true;
        }
        return false;
    },

    // 转发结束类消息
    emitEndMessage(action, data, currentSessionId) {
        const endMap = {
            'llm.call_thinking_completed': 'event.llm.call_thinking_completed',
            'llm.call_reasoning_completed': 'event.llm.call_reasoning_completed',
            'llm.call_text_completed': 'event.llm.call_text_completed',
            'llm.call_completed': 'event.llm.call_completed',
            'tool.execution_output_end': 'event.tool.execution_output_end',
            'event.tool.execution_output_end': 'event.tool.execution_output_end',
            'tool.call_completed': 'event.tool.call_completed',
            'dialog.completed': 'event.dialog.completed'
        };

        const eventName = endMap[action];
        if (eventName) {
            // 合并外层和内层data，使字段都在顶层
            const mergedData = {
                ...data,
                ...data.data,
                __currentSessionId: currentSessionId
            };
            console.log(`%c[ChatManager] 🏁 转发结束类消息: ${action} → ${eventName}`, 'color: #FF5722');
            EventBus.emit(eventName, mergedData);
            return true;
        }
        return false;
    },

    // ========== 消息发送方法 ==========

    // 发送消息到后端
    sendMessage(content) {
        const sessionId = StateManager.getState('currentSessionId');
        console.log(`%c[ChatManager] 📤 发送消息到后端`, 'color: #2196F3; font-weight: bold');
        console.log(`%c[ChatManager]   内容: "${content.substring(0, 50)}${content.length > 50 ? '...' : ''}"`, 'color: #607D8B');
        console.log(`%c[ChatManager]   sessionId: ${sessionId || 'NULL'}`, 'color: #607D8B');
        
        if (!sessionId) {
            console.error(`%c[ChatManager] ❌ 发送失败: sessionId为空`, 'color: #F44336; font-weight: bold');
            return false;
        }
        
        const result = WSClient.sendMessage(sessionId, content);
        console.log(`%c[ChatManager] 📊 发送结果: ${result ? '成功' : '失败'}`, 'color: result ? "#4CAF50" : "#F44336"');
        return result;
    },

    // ========== 辅助方法（兼容性保持） ==========

    // 重置状态（会话切换时调用）
    resetState(newSessionId) {
        console.log(`%c[ChatManager] 🧹 重置状态: ${newSessionId}`, 'color: #9E9E9E');
        StateManager.setState('currentResponseBlockId', null);
        StateManager.setState('currentDialogId', null);
        StateManager.setState('currentRoundNumber', null);
        StateManager.setState('currentAssistantMessageId', null);
        // 清空 responseBlocks，避免会话切换时工具执行输出累加
        StateManager.state.responseBlocks = new Map();
        // 清空工具调用状态映射
        StateManager.state.toolCallIdMap = new Map();
        StateManager.state.pendingToolCalls = new Map();
    },
    
    // 终止对话
    stopDialog() {
        const sessionId = StateManager.getState('currentSessionId');
        const dialogId = StateManager.getState('currentDialogId');
        console.log(`%c[ChatManager] ⏹️ 发送终止对话请求`, 'color: #FF5722; font-weight: bold');
        console.log(`%c[ChatManager]   sessionId: ${sessionId}`, 'color: #607D8B');
        console.log(`%c[ChatManager]   dialogId: ${dialogId}`, 'color: #607D8B');
        
        if (!sessionId) {
            console.error(`%c[ChatManager] ❌ 终止失败: sessionId为空`, 'color: #F44336; font-weight: bold');
            return false;
        }
        
        // 发送终止请求到后端
        const payload = {
            action: 'dialog.stop',
            session_id: sessionId,
            dialog_id: dialogId
        };
        
        const result = WSClient.sendCustomMessage(payload);
        console.log(`%c[ChatManager] 📊 终止请求发送结果: ${result ? '成功' : '失败'}`, 'color: result ? "#4CAF50" : "#F44336"');
        return result;
    }
};

window.ChatManager = ChatManager;