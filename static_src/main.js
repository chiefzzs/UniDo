/**
 * Main Entry - 应用入口
 */
import './js/components/infrastructure/EventBus.js';
import './js/components/infrastructure/StateManager.js';
import './js/components/infrastructure/ApiClient.js';
import './js/components/infrastructure/WSClient.js';
import './js/components/infrastructure/PageRouter.js';

import './js/components/services/ProjectManager.js';
import './js/components/services/SessionManager.js';
import './js/components/services/ComponentLocationManager.js';
import './js/components/services/ChatManager.js';
import './js/components/services/ComponentSubscriptions.js';
import './js/components/services/WorkspaceManager.js';
import './js/components/services/ModelManager.js';
import './js/components/services/ToolManager.js';
import './js/components/services/StorageManager.js';
import './js/components/services/PromptManager.js';

import './js/components/nav/NavBarComponent.js';
import './js/components/nav/NavMenuComponent.js';
import './js/components/nav/ThemeToggle.js';
import './js/components/nav/ConnectionBadge.js';
import './js/components/nav/ReplayToggle.js';

import './js/components/chat/ChatPageComponent.js';
import './js/components/chat/ChatSidebarComponent.js';
import './js/components/chat/ChatInputComponent.js';
import './js/components/chat/UserMessageComponent.js';
import './js/components/chat/AssistantMessageComponent.js';
import './js/components/chat/ThinkBlockComponent.js';
import './js/components/chat/TextBlockComponent.js';
import './js/components/chat/ToolCardComponent.js';

import './js/components/workspace/FileTreeComponent.js';

import './js/components/admin/ProjectPageComponent.js';
import './js/components/admin/WorkspacePageComponent.js';
import './js/components/admin/ModelPageComponent.js';
import './js/components/admin/ToolPageComponent.js';
import './js/components/admin/StoragePageComponent.js';
import './js/components/admin/PromptPageComponent.js';

// Vue2 全局注册组件
const components = {
    // Nav
    NavBarComponent: window.NavBarComponent,
    NavMenuComponent: window.NavMenuComponent,
    ThemeToggle: window.ThemeToggle,
    ConnectionBadge: window.ConnectionBadge,
    ReplayToggle: window.ReplayToggle,
    // Chat
    ChatPageComponent: window.ChatPageComponent,
    ChatSidebarComponent: window.ChatSidebarComponent,
    ChatInputComponent: window.ChatInputComponent,
    UserMessageComponent: window.UserMessageComponent,
    AssistantMessageComponent: window.AssistantMessageComponent,
    ThinkBlockComponent: window.ThinkBlockComponent,
    TextBlockComponent: window.TextBlockComponent,
    ToolCardComponent: window.ToolCardComponent,
    // Workspace
    FileTreeComponent: window.FileTreeComponent,
    // Admin
    ProjectPageComponent: window.ProjectPageComponent,
    WorkspacePageComponent: window.WorkspacePageComponent,
    ModelPageComponent: window.ModelPageComponent,
    ToolPageComponent: window.ToolPageComponent,
    StoragePageComponent: window.StoragePageComponent,
    PromptPageComponent: window.PromptPageComponent
};

// 服务初始化
function initServices() {
    console.log('[App] Initializing services...');
    
    // 初始化ChatManager（延迟初始化，等待WebSocket连接）
    window.ChatManager.init();
    
    // 初始化ComponentSubscriptions（组件订阅管理系统）
    window.ComponentSubscriptions.init();
    
    console.log('[App] Services initialized');
}

// 应用初始化
async function initApp() {
    console.log('[App] Initializing...');
    console.log('[App] Components to register:', Object.keys(components));

    // 注册全局组件
    Object.entries(components).forEach(([name, component]) => {
        if (component && component.name) {
            Vue.component(component.name, component);
            console.log(`[App] Registered: ${component.name}`);
        } else {
            console.warn(`[App] Component ${name} is invalid!`);
        }
    });

    // 初始化服务
    initServices();

    // 创建 Vue 实例
    new Vue({
        el: '#app',
        components,
        data() {
            return {
                currentPage: window.StateManager.getState('currentPage') || 'chat'
            };
        },
        template: `
            <div id="app">
                <nav-bar-component></nav-bar-component>
                <div class="page-content">
                    <chat-page-component v-if="currentPage === 'chat'"></chat-page-component>
                    <project-page-component v-if="currentPage === 'projects'"></project-page-component>
                    <workspace-page-component v-if="currentPage === 'workspaces'"></workspace-page-component>
                    <model-page-component v-if="currentPage === 'models'"></model-page-component>
                    <tool-page-component v-if="currentPage === 'tools'"></tool-page-component>
                    <prompt-page-component v-if="currentPage === 'prompts'"></prompt-page-component>
                    <storage-page-component v-if="currentPage === 'storage'"></storage-page-component>
                </div>
            </div>
        `,
        mounted() {
            console.log('[App] Mounted');
            console.log('[App] Initial currentPage:', this.currentPage);
            console.log('[App] StateManager currentPage:', window.StateManager.getState('currentPage'));
            console.log('[App] Vue version:', Vue.version);
            
            // 立即初始化页面路由
            window.PageRouter.init();

            // 监听页面变化
            window.EventBus.on('page:change', ({ page }) => {
                console.log('[App] Page changed to:', page);
                this.currentPage = page;
            });

            // 尝试连接 WebSocket
            this.connectWebSocket();
        },
        methods: {
            async connectWebSocket() {
                try {
                    await window.WSClient.connect();
                    console.log('[App] WebSocket connected');
                    
                    // WebSocket连接成功后，确保ChatManager已初始化
                    if (!window.ChatManager.initialized) {
                        window.ChatManager.init();
                    }
                } catch (e) {
                    console.warn('[App] WebSocket connection failed:', e.message);
                }
            }
        }
    });
}

// 启动应用
document.addEventListener('DOMContentLoaded', initApp);
