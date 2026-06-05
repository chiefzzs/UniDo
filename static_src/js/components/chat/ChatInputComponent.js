/**
 * ChatInputComponent - 对话输入组件
 */
import { ChatManager } from '../services/ChatManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ChatInputComponent = {
    name: 'ChatInputComponent',
    template: `
        <div class="chat-input-area">
            <div class="chat-input-wrapper">
                <textarea
                    ref="textarea"
                    v-model="inputText"
                    :placeholder="placeholder"
                    rows="1"
                    @keydown="handleKeydown"
                    @input="autoResize"
                    :disabled="isGenerating">
                </textarea>
                <button class="send-btn" @click="handleSend" :disabled="!canSend">
                    <span v-if="isGenerating" class="spinner">⏳</span>
                    <span v-else>➤</span>
                </button>
                <!-- 终止对话按钮 -->
                <button v-if="isGenerating" class="stop-btn" @click="handleStop">
                    ✕
                </button>
            </div>
            <!-- 错误提示 -->
            <div v-if="errorMessage" class="error-message">
                ❌ {{ errorMessage }}
            </div>
        </div>
    `,
    data() {
        return {
            inputText: '',
            placeholder: '输入消息... (Enter 发送，Shift+Enter 换行)',
            isGenerating: false,
            errorMessage: ''
        };
    },
    mounted() {
        console.log('[ChatInput] Mounted');
        
        // 初始化时同步状态（关键：确保初始状态正确）
        this.isGenerating = StateManager.getState('isGenerating');
        
        // 订阅isGenerating状态变化
        this.generatingSubscription = StateManager.subscribe('isGenerating', (value) => {
            console.log('[ChatInput] isGenerating changed:', value);
            this.isGenerating = value;
        });
        
        // 订阅错误信息
        this.errorSubscription = StateManager.subscribe('lastError', (value) => {
            if (value) {
                this.errorMessage = value.message || '未知错误';
                // 3秒后自动清除错误
                setTimeout(() => {
                    this.errorMessage = '';
                }, 3000);
            }
        });
        
        // 订阅消息发送事件
        EventBus.on('message:added', () => {
            this.isGenerating = true;
        });
        
        // 订阅LLM调用完成结束事件
        EventBus.on('event.llm.call_completed_end', () => {
            this.isGenerating = false;
        });
        
        // 订阅对话完成事件（注意：实际事件名使用下划线格式）
        EventBus.on('event_dialog.completed', () => {
            this.isGenerating = false;
            StateManager.setState('isGenerating', false);
            console.log('[ChatInput] 收到对话完成事件');
        });
        
        // 订阅工具调用结束事件
        EventBus.on('event.tool.call_completed', () => {
            // 工具调用结束可能还需要继续，所以不直接设置为false
            // 等待call_completed事件
        });
        
        // 订阅LLM调用失败事件（注意：实际事件名使用下划线格式）
        EventBus.on('event_llm.call_failed', (payload) => {
            console.log('[ChatInput] 收到 LLM调用失败事件:', payload);
            this.isGenerating = false;
            StateManager.setState('isGenerating', false);
        });
        
        // 订阅LLM响应分类事件（处理异常情况）
        EventBus.on('event_llm.response_classified', (payload) => {
            console.log('[ChatInput] 收到 LLM响应分类事件:', payload);
            
            // 正确处理嵌套数据结构
            // payload 可能包含 data 字段，而 data 中又包含实际的 data
            const eventData = payload.data || payload;
            const data = eventData.data || eventData;
            
            console.log('[ChatInput] 解析后的数据:', data);
            console.log('[ChatInput] finish_reason:', data?.finish_reason);
            console.log('[ChatInput] success:', data?.success);
            console.log('[ChatInput] content:', data?.content);
            
            // 如果是错误情况，创建错误消息作为助手回复
            if (data && (data.finish_reason === 'error' || data.success === false)) {
                console.log('[ChatInput] 检测到错误，创建错误响应');
                const errorContent = data.content || data.error || 'LLM调用失败，请稍后重试';
                this.createErrorResponse(errorContent);
            } else {
                console.log('[ChatInput] 非错误情况，不创建错误响应');
            }
            
            // 更新生成状态
            this.isGenerating = false;
            StateManager.setState('isGenerating', false);
        });
    },
    beforeDestroy() {
        // 清理订阅
        if (this.generatingSubscription) {
            this.generatingSubscription();
        }
        if (this.errorSubscription) {
            this.errorSubscription();
        }
    },
    computed: {
        canSend() {
            return this.inputText.trim() && StateManager.getState('currentSessionId') && !this.isGenerating;
        }
    },
    methods: {
        handleKeydown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSend();
            }
        },
        handleSend() {
            if (!this.canSend) return;
            
            // 清除之前的错误信息
            this.errorMessage = '';
            
            const content = this.inputText.trim();
            const sessionId = StateManager.getState('currentSessionId');
            
            // 前端直接添加用户消息，不依赖后台
            const userMessage = {
                id: 'user-' + Date.now(),
                role: 'user',
                content: content,
                sessionId: sessionId,
                timestamp: Date.now()
            };
            
            const messages = [...(StateManager.getState('messages') || []), userMessage];
            StateManager.setState('messages', messages);
            
            // 设置生成状态
            StateManager.setState('isGenerating', true);
            
            EventBus.emit('message:added', { message: userMessage, messages });
            
            // 发送消息到后端
            ChatManager.sendMessage(content);
            
            this.inputText = '';
            this.resetTextarea();
        },
        autoResize() {
            const textarea = this.$refs.textarea;
            if (textarea) {
                textarea.style.height = 'auto';
                textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
            }
        },
        resetTextarea() {
            const textarea = this.$refs.textarea;
            if (textarea) {
                textarea.style.height = 'auto';
            }
        },
        handleStop() {
            if (!this.isGenerating) return;
            
            console.log('[ChatInput] 用户请求终止对话');
            
            // 设置生成状态为false
            this.isGenerating = false;
            StateManager.setState('isGenerating', false);
            
            // 创建用户终止消息
            const sessionId = StateManager.getState('currentSessionId');
            const stopMessage = {
                id: 'user-' + Date.now(),
                role: 'user',
                content: '用户终止了当前对话',
                sessionId: sessionId,
                timestamp: Date.now(),
                isSystem: true
            };
            
            // 添加到消息列表
            const messages = [...(StateManager.getState('messages') || []), stopMessage];
            StateManager.setState('messages', messages);
            
            // 发送终止事件
            EventBus.emit('dialog:stopped', { message: stopMessage });
            
            // 发送终止请求到后端
            ChatManager.stopDialog();
        },
        createErrorResponse(errorContent) {
            console.log('[ChatInput] 创建错误响应:', errorContent);
            
            const sessionId = StateManager.getState('currentSessionId');
            const assistantMessageId = StateManager.getState('currentAssistantMessageId');
            const dialogId = StateManager.getState('currentDialogId');
            
            // 生成唯一ID
            const timestamp = Date.now();
            const responseId = 'error-resp-' + timestamp;
            
            // 创建 ResponseBlock（符合 ResponseBlockComponent 期望的结构）
            const responseBlock = {
                responseId: responseId,
                dialogId: dialogId,
                requestId: 'error-req-' + timestamp,
                timestamp: timestamp,
                status: 'completed',  // 已完成状态
                isError: true,
                textContent: errorContent,  // 直接设置 textContent，供 TextBlockComponent 使用
                thinkContent: '',
                reasonContent: '',
                toolCalls: [],
                __subscriptions: []
            };
            
            // 保存到 StateManager
            StateManager.state.responseBlocks.set(responseId, responseBlock);
            
            // 创建或更新助手消息
            let messages = StateManager.getState('messages') || [];
            let assistantMessage = messages.find(m => m.id === assistantMessageId && m.role === 'assistant');
            
            if (assistantMessage) {
                // 更新现有助手消息
                assistantMessage.responseBlocks = assistantMessage.responseBlocks || [];
                assistantMessage.responseBlocks.push(responseId);
                console.log('[ChatInput] 更新现有助手消息，添加 ResponseBlock:', responseId);
            } else {
                // 创建新的助手消息
                assistantMessage = {
                    id: assistantMessageId || 'assistant-' + timestamp,
                    role: 'assistant',
                    content: errorContent,
                    sessionId: sessionId,
                    dialogId: dialogId,
                    timestamp: timestamp,
                    isError: true,
                    responseBlocks: [responseId]
                };
                messages = [...messages, assistantMessage];
                console.log('[ChatInput] 创建新的助手消息:', assistantMessage.id);
            }
            
            // 更新 StateManager
            StateManager.setState('messages', messages);
            StateManager.setState('currentResponseBlockId', responseId);
            
            // 发布事件
            EventBus.emit('component:response-block-created', { responseId, block: responseBlock });
            EventBus.emit('message:added', { message: assistantMessage, messages });
            
            console.log('[ChatInput] 错误响应创建完成');
        }
    }
};

window.ChatInputComponent = ChatInputComponent;
