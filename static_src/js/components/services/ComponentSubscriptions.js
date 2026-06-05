/**
 * ComponentSubscriptions - 组件订阅管理系统
 *
 * 按照文档中的消息订阅关系表工作：
 * - 创建类消息：父组件订阅，创建子组件
 * - 更新类消息：子组件订阅，实时更新
 * - 结束类消息：子组件订阅，处理完删除订阅
 */
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';

export const ComponentSubscriptions = {
    // 订阅管理状态
    subscriptions: new Map(), // componentId -> [subscriptionIds]
    componentRegistry: new Map(), // componentType -> componentData

    // 初始化
    init() {
        console.log(`%c[ComponentSubscriptions] ✅ 初始化组件订阅系统`, 'color: #4CAF50; font-weight: bold');
        
        // 调试：检查 EventBus 是否可用
        if (!window.EventBus) {
            console.error(`%c[ComponentSubscriptions] ❌ EventBus 不可用!`, 'color: #F44336; font-weight: bold');
            return;
        }
        console.log(`%c[ComponentSubscriptions] ✅ EventBus 可用`, 'color: #4CAF50');
        
        this.setupCreationSubscriptions();
        
        console.log(`%c[ComponentSubscriptions] ✅ 组件订阅系统初始化完成`, 'color: #4CAF50; font-weight: bold');
    },

    // ========== 创建类消息订阅（序号1-8） ==========
    // 这些由父组件订阅，创建子组件

    setupCreationSubscriptions() {
        console.log(`%c[ComponentSubscriptions] 📥 设置创建类消息订阅（序号1-8）`, 'color: #9C27B0');

        // 序号1: event.session.created -> ChatPanel -> SessionComponent
        // （ChatPanel 作为容器，实际在 ChatPageComponent 中处理）
        console.log(`%c[ComponentSubscriptions]   序号1: event.session.created → ChatPanel → SessionComponent`, 'color: #607D8B');

        // 序号2: event.client.message_received -> SessionComponent -> UserMessage
        console.log(`%c[ComponentSubscriptions]   序号2: event.client.message_received → SessionComponent → UserMessage`, 'color: #607D8B');
        EventBus.onConditional(
            'event.client.message_received',
            (data) => this.matchSession(data),
            (data) => this.handleUserMessageCreated(data),
            'ComponentSubscriptions(UserMessage)'
        );

        // 序号3: event.dialog.created -> UserMessage -> AssistantMessage
        console.log(`%c[ComponentSubscriptions]   序号3: event.dialog.created → UserMessage → AssistantMessage`, 'color: #607D8B');
        EventBus.onConditional(
            'event.dialog.created',
            (data) => this.matchSession(data),
            (data) => this.handleAssistantMessageCreated(data),
            'ComponentSubscriptions(AssistantMessage)'
        );

        // 序号4: event.llm.request_sent -> AssistantMessage -> ResponseBlock
        console.log(`%c[ComponentSubscriptions]   序号4: event.llm.request_sent → AssistantMessage → ResponseBlock`, 'color: #607D8B');
        EventBus.onConditional(
            'event.llm.request_sent',
            (data) => this.matchSession(data),
            (data) => this.handleResponseBlockCreated(data),
            'ComponentSubscriptions(ResponseBlock)'
        );

        // 序号5-7: 由 ResponseBlock 订阅，创建子组件（在 ResponseBlock 中处理）
        console.log(`%c[ComponentSubscriptions]   序号5-7: ResponseBlock 订阅创建 ThinkBlock/ReasonBlock/TextBlock`, 'color: #607D8B');

        // 序号8: event.tool.call_started -> ToolCallBlock -> ToolCard
        // （ToolCard 在 ResponseBlock 中处理）
        console.log(`%c[ComponentSubscriptions]   序号8: event.tool.call_started → ResponseBlock → ToolCard`, 'color: #607D8B');
    },

    // ========== 数据校验函数 ==========

    validateEventData(eventName, data) {
        const requiredFieldsMap = {
            'event.session.created': ['session_id'],
            'event.client.message_received': ['session_id', 'content'],
            'event.dialog.created': ['session_id', 'dialog_id'],
            'event.llm.request_sent': ['session_id', 'request_id', 'dialog_id'],
            'event.llm.call_thinking': ['request_id'],
            'event.llm.call_thinking_completed': ['request_id', 'thinking'],
            'event.llm.call_reasoning': ['request_id'],
            'event.llm.call_reasoning_completed': ['request_id', 'reasoning'],
            'event.llm.call_text': ['request_id', 'content'],
            'event.llm.call_text_completed': ['request_id', 'content'],
            'event.llm.call_completed': ['request_id'],
            'event.tool.call_started': ['call_id', 'tool_name'],  // request_id 和 parameters 改为可选
            'event.tool.execution_output': ['call_id', 'output'],
            'event.tool.execution_output_end': ['call_id'],
            'event.tool.call_completed': ['call_id']  // result 和 status 改为可选
        };

        const requiredFields = requiredFieldsMap[eventName];
        if (!requiredFields) return true;

        const missingFields = requiredFields.filter(field => {
            const value = data[field];
            return value === undefined || value === null || value === '';
        });

        if (missingFields.length > 0) {
            console.error(`%c[ComponentSubscriptions] ❌ [DATA_ERROR] 缺少必需字段: ${missingFields.join(', ')} in ${eventName}`, 'color: #F44336; font-weight: bold');
            console.error(`%c[ComponentSubscriptions] ❌ [DATA_ERROR_DETAIL]`, 'color: #F44336', {
                eventName: eventName,
                missingFields: missingFields,
                receivedData: data,
                timestamp: Date.now()
            });
            console.warn(`%c[ComponentSubscriptions] ⚠️ [FLOW_STOPPED] 数据校验失败，终止处理流程`, 'color: #FF9800; font-weight: bold');
            return false;
        }

        return true;
    },

    // ========== 参数匹配函数 ==========

    matchSession(data) {
        const currentSessionId = StateManager.getState('currentSessionId');
        const replayEnabled = StateManager.getState('replayEnabled');
        
        console.log(`%c[ComponentSubscriptions] 🔍 matchSession 检查:`, 'color: #FFC107');
        console.log(`%c[ComponentSubscriptions]   ├── currentSessionId: ${currentSessionId}`, 'color: #FFC107');
        console.log(`%c[ComponentSubscriptions]   ├── replayEnabled: ${replayEnabled}`, 'color: #FFC107');
        console.log(`%c[ComponentSubscriptions]   └── data.session_id: ${data.session_id}`, 'color: #FFC107');
        
        // 在回放模式下，允许接受任何会话的消息
        if (replayEnabled) {
            console.log(`%c[ComponentSubscriptions] ⚠️ 回放模式：允许所有会话消息 → 返回 true`, 'color: #FF9800');
            return true;
        }
        
        // 如果没有当前会话ID，在非回放模式下返回false
        if (!currentSessionId) {
            console.log(`%c[ComponentSubscriptions] ⏭️ 当前会话ID为空，跳过消息 → 返回 false`, 'color: #9E9E9E');
            return false;
        }
        
        // 如果数据中没有session_id，允许通过
        if (!data.session_id) {
            console.log(`%c[ComponentSubscriptions] ⚠️ 消息中没有session_id，允许通过 → 返回 true`, 'color: #FF9800');
            return true;
        }
        
        const matches = data.session_id === currentSessionId;
        if (!matches) {
            console.log(`%c[ComponentSubscriptions] ⏭️ 会话ID不匹配: expected=${currentSessionId}, actual=${data.session_id} → 返回 false`, 'color: #9E9E9E');
        } else {
            console.log(`%c[ComponentSubscriptions] ✅ 会话ID匹配: ${currentSessionId} → 返回 true`, 'color: #4CAF50');
        }
        return matches;
    },

    matchDialog(data) {
        const currentSessionId = StateManager.getState('currentSessionId');
        console.log(`%c[ComponentSubscriptions] matchDialog: currentSessionId=${currentSessionId}, data.session_id=${data.session_id}`, 'color: #FF9800');
        
        if (!currentSessionId) {
            console.log(`%c[ComponentSubscriptions] ⏭️ matchDialog失败: 当前会话ID为空`, 'color: #9E9E9E');
            return false;
        }
        if (data.session_id && data.session_id !== currentSessionId) {
            console.log(`%c[ComponentSubscriptions] ⏭️ matchDialog失败: 会话ID不匹配 expected=${currentSessionId}, actual=${data.session_id}`, 'color: #9E9E9E');
            return false;
        }
        return true;
    },

    matchRequest(data, requestId) {
        if (!this.matchDialog(data)) return false;
        
        // 如果有 request_id，优先使用 request_id 匹配
        if (data.request_id) {
            if (data.request_id !== requestId) {
                console.log(`%c[ComponentSubscriptions] ⏭️ 请求ID不匹配: expected=${requestId}, actual=${data.request_id}`, 'color: #9E9E9E');
                return false;
            }
            return true;
        }
        
        // 如果没有 request_id，使用 dialog_id 进行匹配（兼容后台数据格式）
        const currentDialogId = StateManager.getState('currentDialogId');
        if (data.dialog_id && data.dialog_id === currentDialogId) {
            console.log(`%c[ComponentSubscriptions] ⚠️ 使用 dialog_id 匹配替代 request_id: dialog_id=${data.dialog_id}`, 'color: #FF9800');
            return true;
        }
        
        console.log(`%c[ComponentSubscriptions] ⏭️ 无法匹配: request_id=${data.request_id}, dialog_id=${data.dialog_id}, expected_requestId=${requestId}`, 'color: #9E9E9E');
        return false;
    },

    matchToolCall(data, toolCallId) {
        if (!this.matchDialog(data)) return false;
        if (!data.call_id || data.call_id !== toolCallId) {
            console.log(`%c[ComponentSubscriptions] ⏭️ 工具调用ID不匹配: expected=${toolCallId}, actual=${data.call_id}`, 'color: #9E9E9E');
            return false;
        }
        return true;
    },

    // ========== 组件创建处理函数 ==========

    handleUserMessageCreated(data) {
        console.log(`%c[ComponentSubscriptions] 🔄 进入 handleUserMessageCreated`, 'color: #00BCD4; font-weight: bold');
        console.log(`%c[ComponentSubscriptions] 📤 收到数据:`, 'color: #00BCD4', JSON.stringify(data, null, 2));
        
        // client.message_received 的内容在 data.data 中
        const actualData = data.data || data;
        console.log(`%c[ComponentSubscriptions] 📥 实际数据:`, 'color: #00BCD4', JSON.stringify(actualData, null, 2));
        
        // 数据校验（使用实际数据）
        if (!this.validateEventData('event.client.message_received', actualData)) {
            console.log(`%c[ComponentSubscriptions] ❌ 数据校验失败，退出`, 'color: #F44336');
            return;
        }
        console.log(`%c[ComponentSubscriptions] ✅ 数据校验通过`, 'color: #4CAF50');

        // 只处理 client.message_received 类型
        // 根据文档设计：event.client.message_received 应由 SessionComponent 订阅创建 UserMessage
        // 用户发送消息时，后端会推送 client.message_received 事件
        // 会话切换时，后端也会推送历史消息的 client.message_received 事件
        // 注意：ChatManager 转发后事件名称变成 event.client.message_received
        if (data.action !== 'client.message_received' && data.action !== 'event.client.message_received') {
            console.log(`%c[ComponentSubscriptions] ⏭️ 跳过非 client.message_received 消息: ${data.action}`, 'color: #9E9E9E');
            return;
        }
        console.log(`%c[ComponentSubscriptions] ✅ 通过 action 检查`, 'color: #4CAF50');

        // 获取消息内容
        const content = actualData.content || '';
        if (!content.trim()) {
            console.log(`%c[ComponentSubscriptions] ⏭️ 跳过空消息`, 'color: #9E9E9E');
            return;
        }

        const currentSessionId = StateManager.getState('currentSessionId');
        const messages = StateManager.getState('messages') || [];

        // 检查是否已有此用户消息（防止重复）
        const existing = messages.find(m =>
            m.role === 'user' && (m.content === content || m.messageId === actualData.message_id)
        );
        if (existing) {
            console.log(`%c[ComponentSubscriptions] ⏭️ 用户消息已存在，跳过`, 'color: #9E9E9E');
            return;
        }

        const userMessage = {
            id: 'user-' + Date.now(),
            role: 'user',
            content: content,
            sessionId: currentSessionId,
            dialogId: actualData.dialog_id || null,
            messageId: actualData.message_id || null,
            timestamp: Date.now()
        };

        messages.push(userMessage);
        StateManager.setState('messages', messages);
        
        console.log(`%c[ComponentSubscriptions] 👶 创建 UserMessage (${userMessage.id})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('SessionComponent', 'UserMessage', { 
            messageId: userMessage.id, 
            content: content.substring(0, 50) + (content.length > 50 ? '...' : '') 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                userMessage.id, 
                'UserMessage', 
                { 
                    sessionId: userMessage.sessionId,
                    dialogId: userMessage.dialogId,
                    messageId: userMessage.messageId 
                }
            );
        }
        
        EventBus.emit('component:user-message-created', { message: userMessage });
    },

    handleAssistantMessageCreated(data) {
        // 数据校验
        if (!this.validateEventData('event.dialog.created', data)) {
            return;
        }

        const currentSessionId = StateManager.getState('currentSessionId');
        const messages = StateManager.getState('messages') || [];

        // 检查是否已有此助手消息
        const existing = messages.find(m =>
            m.role === 'assistant' && m.dialogId === data.dialog_id
        );
        if (existing) {
            StateManager.setState('currentAssistantMessageId', existing.id);
            console.log(`%c[ComponentSubscriptions] ⏭️ 助手消息已存在，跳过: ${existing.id}`, 'color: #9E9E9E');
            return;
        }

        const assistantMessage = {
            id: 'assistant-' + Date.now(),
            role: 'assistant',
            content: '',
            sessionId: currentSessionId,
            dialogId: data.dialog_id,
            responseBlocks: [],
            status: 'streaming',
            timestamp: Date.now()
        };

        messages.push(assistantMessage);
        StateManager.setState('messages', messages);
        StateManager.setState('currentDialogId', data.dialog_id);
        StateManager.setState('currentAssistantMessageId', assistantMessage.id);

        console.log(`%c[ComponentSubscriptions] 👶 创建 AssistantMessage (${assistantMessage.id})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('UserMessage', 'AssistantMessage', { 
            messageId: assistantMessage.id, 
            dialogId: data.dialog_id 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                assistantMessage.id, 
                'AssistantMessage', 
                { 
                    sessionId: assistantMessage.sessionId,
                    dialogId: assistantMessage.dialogId 
                }
            );
        }
        
        EventBus.emit('component:assistant-message-created', { message: assistantMessage });
    },

    handleResponseBlockCreated(data) {
        // 数据校验
        if (!this.validateEventData('event.llm.request_sent', data)) {
            return;
        }

        const currentSessionId = StateManager.getState('currentSessionId');
        const responseId = 'resp-' + (data.request_id || Date.now());

        // 如果还没有 responseBlocks，初始化
        if (!StateManager.state.responseBlocks) {
            StateManager.state.responseBlocks = new Map();
        }

        // 检查是否已存在相同的 responseBlock，防止重复创建
        if (StateManager.state.responseBlocks.has(responseId)) {
            console.warn(`%c[ComponentSubscriptions] ⚠️ 重复创建 ResponseBlock 被阻止: ${responseId}`, 'color: #FF9800');
            return;
        }

        // 创建 Vue 响应式对象，确保属性变化能被 Vue 检测到
        const responseBlock = Vue.observable({
            responseId,
            requestId: data.request_id || null,
            sessionId: currentSessionId,
            dialogId: data.dialog_id || null,
            thinkContent: '',
            reasonContent: '',
            textContent: '',
            toolCalls: [],
            status: 'streaming',
            timestamp: Date.now(),
            __subscriptions: [] // 存储此组件的订阅ID
        });

        StateManager.state.responseBlocks.set(responseId, responseBlock);
        StateManager.setState('currentResponseBlockId', responseId);

        // 将响应块关联到当前助手消息
        const currentAssistantMessageId = StateManager.getState('currentAssistantMessageId');
        if (currentAssistantMessageId) {
            const messages = StateManager.getState('messages') || [];
            const assistantMessage = messages.find(m => m.id === currentAssistantMessageId);
            if (assistantMessage) {
                assistantMessage.responseBlocks = assistantMessage.responseBlocks || [];
                assistantMessage.responseBlocks.push(responseId);
                StateManager.setState('messages', [...messages]);
            }
        }

        console.log(`%c[ComponentSubscriptions] 👶 创建 ResponseBlock (${responseId})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('AssistantMessage', 'ResponseBlock', { 
            responseId, 
            requestId: data.request_id 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                responseId, 
                'ResponseBlock', 
                { 
                    responseId: responseId,
                    dialogId: data.dialog_id,
                    messageId: currentAssistantMessageId 
                }
            );
        }
        
        EventBus.emit('component:response-block-created', { responseId, block: responseBlock });

        // 订阅子组件的创建事件
        this.setupResponseBlockSubscriptions(responseId, data.request_id);
    },

    // 设置 ResponseBlock 的子组件订阅
    setupResponseBlockSubscriptions(responseId, requestId) {
        console.log(`%c[ComponentSubscriptions] 📥 为 ResponseBlock (${responseId}) 设置子组件订阅`, 'color: #9C27B0');

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        // 序号5: event.llm.call_thinking_completed -> 创建 ThinkBlock
        console.log(`%c[ComponentSubscriptions]   序号5: event.llm.call_thinking_completed → ResponseBlock → ThinkBlock`, 'color: #607D8B');
        const thinkSubId = EventBus.onceConditional(
            'event.llm.call_thinking_completed',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleThinkBlockCreated(responseId, data),
            `ComponentSubscriptions(ThinkBlock_${responseId})`
        );
        block.__subscriptions.push({ type: 'think_creation', id: thinkSubId });

        // 序号6: event.llm.call_reasoning_completed -> 创建 ReasonBlock
        console.log(`%c[ComponentSubscriptions]   序号6: event.llm.call_reasoning_completed → ResponseBlock → ReasonBlock`, 'color: #607D8B');
        const reasonSubId = EventBus.onceConditional(
            'event.llm.call_reasoning_completed',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleReasonBlockCreated(responseId, data),
            `ComponentSubscriptions(ReasonBlock_${responseId})`
        );
        block.__subscriptions.push({ type: 'reason_creation', id: reasonSubId });

        // 序号7: event.llm.call_text_completed -> 创建 TextBlock
        console.log(`%c[ComponentSubscriptions]   序号7: event.llm.call_text_completed → ResponseBlock → TextBlock`, 'color: #607D8B');
        const textSubId = EventBus.onceConditional(
            'event.llm.call_text_completed',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleTextBlockCreated(responseId, data),
            `ComponentSubscriptions(TextBlock_${responseId})`
        );
        block.__subscriptions.push({ type: 'text_creation', id: textSubId });

        // 序号8: event.tool.call_started -> 创建 ToolCard
        console.log(`%c[ComponentSubscriptions]   序号8: event.tool.call_started → ResponseBlock → ToolCard`, 'color: #607D8B');
        const toolSubId = EventBus.onConditional(
            'event.tool.call_started',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleToolCardCreated(responseId, data),
            `ComponentSubscriptions(ToolCard_${responseId})`
        );
        block.__subscriptions.push({ type: 'tool_creation', id: toolSubId });

        // 订阅更新类消息（序号9-12）
        this.setupUpdateSubscriptions(responseId, requestId);

        // 订阅结束类消息（序号13-18）
        this.setupEndSubscriptions(responseId, requestId);
    },

    // ========== 子组件创建处理函数 ==========

    handleThinkBlockCreated(responseId, data) {
        // 数据校验
        if (!this.validateEventData('event.llm.call_thinking_completed', data)) {
            return;
        }

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ThinkBlock 创建失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const thinking = data.thinking || data.content || '';
        if (thinking) {
            block.thinkContent = thinking;
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
        }

        console.log(`%c[ComponentSubscriptions] 👶 创建 ThinkBlock (${responseId})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('ResponseBlock', 'ThinkBlock', { 
            responseId, 
            contentLength: thinking.length 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                `think-${responseId}`, 
                'ThinkBlock', 
                { responseId }
            );
        }

        // 订阅思考的更新和结束消息
        const requestId = block.requestId;
        this.setupThinkBlockSubscriptions(responseId, requestId);
    },

    handleReasonBlockCreated(responseId, data) {
        // 数据校验
        if (!this.validateEventData('event.llm.call_reasoning_completed', data)) {
            return;
        }

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ReasonBlock 创建失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const reasoning = data.reasoning || data.content || '';
        if (reasoning) {
            block.reasonContent = reasoning;
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
        }

        console.log(`%c[ComponentSubscriptions] 👶 创建 ReasonBlock (${responseId})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('ResponseBlock', 'ReasonBlock', { 
            responseId, 
            contentLength: reasoning.length 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                `reason-${responseId}`, 
                'ReasonBlock', 
                { responseId }
            );
        }

        // 订阅推理的更新和结束消息
        const requestId = block.requestId;
        this.setupReasonBlockSubscriptions(responseId, requestId);
    },

    handleTextBlockCreated(responseId, data) {
        // 数据校验
        if (!this.validateEventData('event.llm.call_text_completed', data)) {
            return;
        }

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ TextBlock 创建失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const content = data.content || '';
        if (content) {
            block.textContent = content;
            // 重新设置 responseBlocks 以触发 Vue 响应式更新
            StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
        }

        console.log(`%c[ComponentSubscriptions] 👶 创建 TextBlock (${responseId})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('ResponseBlock', 'TextBlock', { 
            responseId, 
            contentLength: content.length 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                `text-${responseId}`, 
                'TextBlock', 
                { responseId }
            );
        }

        // 订阅文本的更新和结束消息
        const requestId = block.requestId;
        this.setupTextBlockSubscriptions(responseId, requestId);
    },

    handleToolCardCreated(responseId, data) {
        console.log(`%c[ComponentSubscriptions] 🛠️ 收到工具调用开始事件，准备创建 ToolCard: responseId=${responseId}`, 'color: #00BCD4');
        // 数据校验
        if (!this.validateEventData('event.tool.call_started', data)) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ToolCard 创建失败：数据校验失败`, 'color: #FF9800');
            return;
        }

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ToolCard 创建失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const toolCallId = data.call_id || 'tool-' + Date.now();
        const toolCard = {
            callId: toolCallId,
            toolName: data.tool_name || 'unknown',
            args: data.parameters || data.params || data.args || {},  // 优先使用 parameters，兼容 params 和 args
            output: '',
            status: 'streaming',
            __subscriptions: []
        };

        block.toolCalls.push(toolCard);
        // 重新创建数组以触发 Vue 响应式更新
        block.toolCalls = [...block.toolCalls];
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);

        console.log(`%c[ComponentSubscriptions] 👶 创建 ToolCard (${toolCallId})`, 'color: #00BCD4; font-weight: bold');
        EventBus.trackComponentCreation('ResponseBlock', 'ToolCard', { 
            responseId, 
            toolCallId, 
            toolName: data.tool_name 
        });
        
        // 记录组件位置到 ComponentLocationManager
        if (window.ComponentLocationManager) {
            window.ComponentLocationManager.recordCreation(
                toolCallId, 
                'ToolCard', 
                { 
                    responseId,
                    callId: toolCallId 
                }
            );
        }

        // 订阅工具的更新和结束消息
        this.setupToolCardSubscriptions(responseId, toolCallId);
    },

    // ========== 更新类消息订阅（序号9-12） ==========

    setupUpdateSubscriptions(responseId, requestId) {
        console.log(`%c[ComponentSubscriptions] 📥 设置更新类消息订阅（序号9-12）`, 'color: #8BC34A');

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        // 序号9: event.llm.call_text_streaming -> TextBlock
        console.log(`%c[ComponentSubscriptions]   序号9: event.llm.call_text_streaming → TextBlock`, 'color: #607D8B');
        const textUpdateSubId = EventBus.onConditional(
            'event.llm.call_text_streaming',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleTextBlockUpdate(responseId, data),
            `ComponentSubscriptions(TextUpdate_${responseId})`
        );
        block.__subscriptions.push({ type: 'text_update', id: textUpdateSubId });

        // 序号10: event.llm.call_thinking_streaming -> ThinkBlock
        console.log(`%c[ComponentSubscriptions]   序号10: event.llm.call_thinking_streaming → ThinkBlock`, 'color: #607D8B');
        const thinkUpdateSubId = EventBus.onConditional(
            'event.llm.call_thinking_streaming',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleThinkBlockUpdate(responseId, data),
            `ComponentSubscriptions(ThinkUpdate_${responseId})`
        );
        block.__subscriptions.push({ type: 'think_update', id: thinkUpdateSubId });

        // 序号11: event.llm.call_reasoning_streaming -> ReasonBlock
        console.log(`%c[ComponentSubscriptions]   序号11: event.llm.call_reasoning_streaming → ReasonBlock`, 'color: #607D8B');
        const reasonUpdateSubId = EventBus.onConditional(
            'event.llm.call_reasoning_streaming',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleReasonBlockUpdate(responseId, data),
            `ComponentSubscriptions(ReasonUpdate_${responseId})`
        );
        block.__subscriptions.push({ type: 'reason_update', id: reasonUpdateSubId });

        // 序号12: event.tool.execution_output -> ToolCard (在 ToolCard 中处理)
        console.log(`%c[ComponentSubscriptions]   序号12: event.tool.execution_output → ToolCard (在 ToolCard 创建时设置)`, 'color: #607D8B');
    },

    setupThinkBlockSubscriptions(responseId, requestId) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        // 序号10: 更新类消息已在 setupUpdateSubscriptions 中设置

        // 序号14: event.llm.call_thinking_completed_end -> ThinkBlock（结束）
        console.log(`%c[ComponentSubscriptions]   序号14: event.llm.call_thinking_completed_end → ThinkBlock`, 'color: #607D8B');
        const thinkEndSubId = EventBus.onceConditional(
            'event.llm.call_thinking_completed_end',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleThinkBlockEnd(responseId, data),
            `ComponentSubscriptions(ThinkEnd_${responseId})`
        );
        block.__subscriptions.push({ type: 'think_end', id: thinkEndSubId });
    },

    setupReasonBlockSubscriptions(responseId, requestId) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        // 序号11: 更新类消息已在 setupUpdateSubscriptions 中设置

        // 序号15: event.llm.call_reasoning_completed_end -> ReasonBlock（结束）
        console.log(`%c[ComponentSubscriptions]   序号15: event.llm.call_reasoning_completed_end → ReasonBlock`, 'color: #607D8B');
        const reasonEndSubId = EventBus.onceConditional(
            'event.llm.call_reasoning_completed_end',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleReasonBlockEnd(responseId, data),
            `ComponentSubscriptions(ReasonEnd_${responseId})`
        );
        block.__subscriptions.push({ type: 'reason_end', id: reasonEndSubId });
    },

    setupTextBlockSubscriptions(responseId, requestId) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        // 序号9: 更新类消息已在 setupUpdateSubscriptions 中设置

        // 序号13: event.llm.call_text_completed_end -> TextBlock（结束）
        console.log(`%c[ComponentSubscriptions]   序号13: event.llm.call_text_completed_end → TextBlock`, 'color: #607D8B');
        const textEndSubId = EventBus.onceConditional(
            'event.llm.call_text_completed_end',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleTextBlockEnd(responseId, data),
            `ComponentSubscriptions(TextEnd_${responseId})`
        );
        block.__subscriptions.push({ type: 'text_end', id: textEndSubId });
    },

    setupToolCardSubscriptions(responseId, toolCallId) {
        console.log(`%c[ComponentSubscriptions] 📥 尝试为 ToolCard 设置订阅: responseId=${responseId}, toolCallId=${toolCallId}`, 'color: #9C27B0');
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ setupToolCardSubscriptions: ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const toolCard = block.toolCalls.find(tc => tc.callId === toolCallId);
        if (!toolCard) {
            console.log(`%c[ComponentSubscriptions] ⚠️ setupToolCardSubscriptions: ToolCard 不存在: ${toolCallId}`, 'color: #FF9800');
            return;
        }

        console.log(`%c[ComponentSubscriptions] 📥 为 ToolCard (${toolCallId}) 设置订阅`, 'color: #9C27B0');

        // 序号12: event.tool.execution_output -> ToolCard（更新）
        console.log(`%c[ComponentSubscriptions]   序号12: event.tool.execution_output → ToolCard`, 'color: #607D8B');
        const toolUpdateSubId = EventBus.onConditional(
            'event.tool.execution_output',
            (data) => this.matchToolCall(data, toolCallId),
            (data) => this.handleToolCardUpdate(responseId, toolCallId, data),
            `ComponentSubscriptions(ToolUpdate_${toolCallId})`
        );
        toolCard.__subscriptions.push({ type: 'tool_update', id: toolUpdateSubId });

        // 序号17: event.tool.execution_output_end -> ToolCard（输出结束）
        console.log(`%c[ComponentSubscriptions]   序号17: event.tool.execution_output_end → ToolCard`, 'color: #607D8B');
        const toolOutputEndSubId = EventBus.onceConditional(
            'event.tool.execution_output_end',
            (data) => this.matchToolCall(data, toolCallId),
            (data) => this.handleToolCardOutputEnd(responseId, toolCallId, data),
            `ComponentSubscriptions(ToolOutputEnd_${toolCallId})`
        );
        toolCard.__subscriptions.push({ type: 'tool_output_end', id: toolOutputEndSubId });

        // 序号18: event.tool.call_completed -> ToolCard（调用结束）
        console.log(`%c[ComponentSubscriptions]   序号18: event.tool.call_completed → ToolCard`, 'color: #607D8B');
        const toolEndSubId = EventBus.onceConditional(
            'event.tool.call_completed',
            (data) => this.matchToolCall(data, toolCallId),
            (data) => this.handleToolCardEnd(responseId, toolCallId, data),
            `ComponentSubscriptions(ToolEnd_${toolCallId})`
        );
        toolCard.__subscriptions.push({ type: 'tool_end', id: toolEndSubId });
    },

    // ========== 结束类消息订阅（序号13-18） ==========

    setupEndSubscriptions(responseId, requestId) {
        console.log(`%c[ComponentSubscriptions] 📥 设置结束类消息订阅（序号13-18）`, 'color: #E91E63');

        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        // 序号16: event.llm.call_completed_end -> ResponseBlock（结束）
        console.log(`%c[ComponentSubscriptions]   序号16: event.llm.call_completed_end → ResponseBlock`, 'color: #607D8B');
        const callEndSubId = EventBus.onceConditional(
            'event.llm.call_completed_end',
            (data) => this.matchRequest(data, requestId),
            (data) => this.handleResponseBlockEnd(responseId, data),
            `ComponentSubscriptions(CallEnd_${responseId})`
        );
        block.__subscriptions.push({ type: 'call_end', id: callEndSubId });
    },

    // ========== 更新处理函数 ==========

    handleTextBlockUpdate(responseId, data) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ TextBlock 更新失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const content = data.content || data.thinking || '';
        if (content) {
            block.textContent += content;
            // 重新设置 responseBlocks 以触发 Vue 响应式更新
            StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
            
            console.log(`%c[ComponentSubscriptions] 🔄 更新 TextBlock (${responseId})`, 'color: #8BC34A');
            EventBus.trackComponentUpdate('TextBlock', 'streaming', { 
                responseId, 
                addedLength: content.length,
                totalLength: block.textContent.length 
            });
        }
    },

    handleThinkBlockUpdate(responseId, data) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ThinkBlock 更新失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const content = data.thinking || data.content || '';
        if (content) {
            block.thinkContent += content;
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
            
            console.log(`%c[ComponentSubscriptions] 🔄 更新 ThinkBlock (${responseId})`, 'color: #8BC34A');
            EventBus.trackComponentUpdate('ThinkBlock', 'streaming', { 
                responseId, 
                addedLength: content.length,
                totalLength: block.thinkContent.length 
            });
        }
    },

    handleReasonBlockUpdate(responseId, data) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ReasonBlock 更新失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const content = data.reasoning || data.content || '';
        if (content) {
            block.reasonContent += content;
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
            
            console.log(`%c[ComponentSubscriptions] 🔄 更新 ReasonBlock (${responseId})`, 'color: #8BC34A');
            EventBus.trackComponentUpdate('ReasonBlock', 'streaming', { 
                responseId, 
                addedLength: content.length,
                totalLength: block.reasonContent.length 
            });
        }
    },

    handleToolCardUpdate(responseId, toolCallId, data) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ToolCard 更新失败：ResponseBlock 不存在: ${responseId}`, 'color: #FF9800');
            return;
        }

        const toolCard = block.toolCalls.find(tc => tc.callId === toolCallId);
        if (!toolCard) {
            console.log(`%c[ComponentSubscriptions] ⚠️ ToolCard 更新失败：ToolCard 不存在: ${toolCallId}`, 'color: #FF9800');
            return;
        }

        const output = data.output || '';
        if (output) {
            toolCard.output += output;
            StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
            
            console.log(`%c[ComponentSubscriptions] 🔄 更新 ToolCard (${toolCallId})`, 'color: #8BC34A');
            EventBus.trackComponentUpdate('ToolCard', 'execution', { 
                toolCallId, 
                addedLength: output.length,
                totalLength: toolCard.output.length 
            });
        }
    },

    // ========== 结束处理函数 ==========

    handleTextBlockEnd(responseId, data) {
        console.log('[ComponentSubscriptions] TextBlock 结束:', responseId, data);
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        const content = data.content || '';
        if (content) {
            block.textContent = content;
            // 重新设置 responseBlocks 以触发 Vue 响应式更新
            StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
        }
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);

        // 清理 TextBlock 的订阅（已自动清理，因为用了 onceConditional）
    },

    handleThinkBlockEnd(responseId, data) {
        console.log('[ComponentSubscriptions] ThinkBlock 结束:', responseId, data);
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        const thinking = data.thinking || data.content || '';
        if (thinking) {
            block.thinkContent = thinking;
        }
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
    },

    handleReasonBlockEnd(responseId, data) {
        console.log('[ComponentSubscriptions] ReasonBlock 结束:', responseId, data);
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        const reasoning = data.reasoning || data.content || '';
        if (reasoning) {
            block.reasonContent = reasoning;
        }
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
    },

    handleToolCardOutputEnd(responseId, toolCallId, data) {
        console.log('[ComponentSubscriptions] ToolCard 输出结束:', responseId, toolCallId);
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        const toolCard = block.toolCalls.find(tc => tc.callId === toolCallId);
        if (!toolCard) return;

        toolCard.outputEnded = true;
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);
    },

    handleToolCardEnd(responseId, toolCallId, data) {
        console.log('[ComponentSubscriptions] ToolCard 调用结束:', responseId, toolCallId, 'success:', data.success);
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        const toolCard = block.toolCalls.find(tc => tc.callId === toolCallId);
        if (!toolCard) return;

        // 根据 success 字段设置状态
        const isSuccess = data.success !== false;
        toolCard.status = isSuccess ? 'completed' : 'failed';
        toolCard.success = isSuccess;
        
        // 设置结果或错误信息
        if (isSuccess) {
            toolCard.result = data.result || null;
            toolCard.error = null;
        } else {
            // 失败时，result 包含完整返回，error 包含错误信息
            toolCard.result = data.result || null;
            toolCard.error = data.error || 'Unknown error';
        }
        
        console.log('[ComponentSubscriptions] ToolCard 状态更新:', toolCard.status, 'error:', toolCard.error);
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);

        // 清理 ToolCard 的订阅
        this.cleanupToolCardSubscriptions(responseId, toolCallId);
    },

    handleResponseBlockEnd(responseId, data) {
        console.log('[ComponentSubscriptions] ResponseBlock 结束:', responseId, data);
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        block.status = 'completed';

        // 处理结束时的内容更新
        if (data.content) block.textContent = data.content;
        if (data.thinking) block.thinkContent = data.thinking;
        if (data.reasoning) block.reasonContent = data.reasoning;

        // 重新设置 responseBlocks 以触发 Vue 响应式更新
        StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
        StateManager.setState('messages', [...(StateManager.getState('messages') || [])]);

        // 清理 ResponseBlock 的订阅
        this.cleanupResponseBlockSubscriptions(responseId);
    },

    // ========== 订阅清理 ==========

    cleanupResponseBlockSubscriptions(responseId) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        console.log('[ComponentSubscriptions] 清理 ResponseBlock 订阅:', responseId);

        // 取消所有订阅
        block.__subscriptions.forEach(sub => {
            EventBus.offConditional('event.llm.call_text_streaming', sub.id);
            EventBus.offConditional('event.llm.call_thinking_streaming', sub.id);
            EventBus.offConditional('event.llm.call_reasoning_streaming', sub.id);
            EventBus.offConditional('event.tool.call_started', sub.id);
            // 其他 onceConditional 订阅已自动清理
        });

        // 清理子组件的订阅
        block.toolCalls.forEach(toolCard => {
            this.cleanupToolCardSubscriptions(responseId, toolCard.callId);
        });

        block.__subscriptions = [];
    },

    cleanupToolCardSubscriptions(responseId, toolCallId) {
        const block = StateManager.state.responseBlocks.get(responseId);
        if (!block) return;

        const toolCard = block.toolCalls.find(tc => tc.callId === toolCallId);
        if (!toolCard) return;

        console.log('[ComponentSubscriptions] 清理 ToolCard 订阅:', toolCallId);

        toolCard.__subscriptions.forEach(sub => {
            EventBus.offConditional('event.tool.execution_output', sub.id);
            // 其他 onceConditional 订阅已自动清理
        });

        toolCard.__subscriptions = [];
    },

    // ========== 清理所有订阅 ==========

    clearAll() {
        console.log(`%c[ComponentSubscriptions] 🧹 清理所有组件订阅`, 'color: #FF9800');
        if (StateManager.state.responseBlocks) {
            StateManager.state.responseBlocks.forEach((block, responseId) => {
                this.cleanupResponseBlockSubscriptions(responseId);
            });
        }
        // 注意：不调用 EventBus.clear()，因为会清空其他组件（如 ChatManager）的订阅
        // 只清理 ComponentSubscriptions 创建的条件订阅
        this.subscriptions.forEach((subIds, componentId) => {
            subIds.forEach(subId => {
                EventBus.offConditional('event.client.message_received', subId);
                EventBus.offConditional('event.dialog.created', subId);
                EventBus.offConditional('event.llm.request_sent', subId);
            });
        });
        this.subscriptions.clear();
    }
};

window.ComponentSubscriptions = ComponentSubscriptions;
