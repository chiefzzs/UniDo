/**
 * ChatPageComponent - 对话页面组件
 */
import { ChatSidebarComponent } from './ChatSidebarComponent.js';
import { UserMessageComponent } from './UserMessageComponent.js';
import { AssistantMessageComponent } from './AssistantMessageComponent.js';
import { ResponseBlockComponent } from './ResponseBlockComponent.js';
import { ThinkBlockComponent } from './ThinkBlockComponent.js';
import { ReasonBlockComponent } from './ReasonBlockComponent.js';
import { TextBlockComponent } from './TextBlockComponent.js';
import { ToolCardComponent } from './ToolCardComponent.js';
import { ChatInputComponent } from './ChatInputComponent.js';
import { ChatManager } from '../services/ChatManager.js';
import { ComponentSubscriptions } from '../services/ComponentSubscriptions.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ChatPageComponent = {
    name: 'ChatPageComponent',
    components: {
        ChatSidebarComponent,
        UserMessageComponent,
        AssistantMessageComponent,
        ResponseBlockComponent,
        ThinkBlockComponent,
        ReasonBlockComponent,
        TextBlockComponent,
        ToolCardComponent,
        ChatInputComponent
    },
    template: `
        <div class="chat-page">
            <div class="chat-layout">
                <chat-sidebar-component
                    :projectId="currentProjectId"
                    :sessions="sessions"
                    :currentSessionId="currentSessionId">
                </chat-sidebar-component>
                <main class="chat-main">
                    <div class="messages-container" ref="messagesContainer">
                        <div v-if="!messages.length" class="empty-state">
                            <div class="empty-icon">💬</div>
                            <div class="empty-text">选择或创建一个会话开始对话</div>
                        </div>
                        <template v-for="msg in messages">
                            <user-message-component v-if="msg.role === 'user'" :key="msg.id" :message="msg"></user-message-component>
                            <assistant-message-component v-else :key="msg.id" :message="msg"></assistant-message-component>
                        </template>
                    </div>
                    <chat-input-component></chat-input-component>
                </main>
            </div>
        </div>
    `,
    data() {
        return {
            messages: [],
            sessions: StateManager.getState('sessions') || []
        };
    },
    computed: {
        currentProjectId() { return StateManager.getState('currentProjectId'); },
        currentSessionId() { return StateManager.getState('currentSessionId'); }
    },
    mounted() {
        console.log('[ChatPage] Mounted, initial sessions:', this.sessions);
        console.log('[ChatPage] Initial projectId:', this.currentProjectId);

        // 初始化 ChatManager
        ChatManager.init();

        // 初始化组件订阅系统
        ComponentSubscriptions.init();

        // 监听会话加载
        EventBus.on('session:loaded', ({ sessions }) => {
            console.log('[ChatPage] Sessions loaded:', sessions);
            this.sessions = sessions;
        });

        // 监听会话切换
        EventBus.on('session:switching', ({ sessionId }) => {
            console.log('[ChatPage] Session switching to:', sessionId);
            this.messages = [];
            ChatManager.resetState(sessionId);
            // 清理旧会话的订阅
            ComponentSubscriptions.clearAll();
        });

        // 监听消息更新（来自 StateManager）
        EventBus.on('state:updated', ({ key, value }) => {
            if (key === 'messages') {
                this.messages = value;
            }
        });
    }
};

window.ChatPageComponent = ChatPageComponent;
