/**
 * StateManager - 状态管理
 * 统一管理应用状态
 */
export const StateManager = {
    state: {
        // 连接状态
        wsConnected: false,
        clientId: null,

        // 菜单状态
        menus: [
            { id: 'chat', label: '对话', icon: '💬', page: 'chat', sortOrder: 0 },
            { id: 'projects', label: '项目', icon: '📁', page: 'projects', sortOrder: 1 },
            { id: 'workspaces', label: '工作区', icon: '📂', page: 'workspaces', sortOrder: 2 },
            { id: 'models', label: '模型', icon: '🤖', page: 'models', sortOrder: 3 },
            { id: 'tools', label: '工具', icon: '🔧', page: 'tools', sortOrder: 4 },
            { id: 'prompts', label: '提示词', icon: '📝', page: 'prompts', sortOrder: 5 },
            { id: 'storage', label: '存储配置', icon: '💾', page: 'storage', sortOrder: 6 }
        ],
        activeMenuId: 'chat',

        // UI 状态
        currentPage: 'chat',
        theme: 'dark',
        replayEnabled: false,
        replayMode: 'off',
        replaySpeed: 'normal',

        // 项目状态
        projects: [],
        currentProjectId: null,
        projectsLoading: false,

        // 会话状态
        sessions: [],
        currentSessionId: null,
        sessionsLoading: false,

        // 消息状态
        messages: [],

        // 响应块状态
        responseBlocks: new Map(),
        currentResponseBlockId: null,

        // 工具调用状态
        pendingToolCalls: new Map(),
        toolCallIdMap: new Map(),
        
        // 生成状态（用于控制发送按钮）
        isGenerating: false,
        // 错误信息
        lastError: null
    },

    listeners: new Map(),

    // 获取状态
    getState(key) {
        return key ? this.state[key] : this.state;
    },

    // 设置状态
    setState(key, value) {
        const oldValue = this.state[key];
        this.state[key] = value;
        console.log(`[State] ${key}:`, oldValue, '→', value);
        this.notify(key, value, oldValue);
        
        // 触发全局事件总线通知
        if (typeof window !== 'undefined' && window.EventBus) {
            window.EventBus.emit('state:updated', { key, value, oldValue });
        }
    },

    // 批量设置状态
    setStates(states) {
        Object.entries(states).forEach(([key, value]) => {
            this.setState(key, value);
        });
    },

    // 订阅状态变更
    subscribe(key, listener) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(listener);
        return () => this.listeners.get(key).delete(listener);
    },

    // 通知状态变更
    notify(key, newValue, oldValue) {
        if (this.listeners.has(key)) {
            this.listeners.get(key).forEach(listener => {
                try {
                    listener(newValue, oldValue);
                } catch (e) {
                    console.error(`[State] Subscriber error (${key}):`, e);
                }
            });
        }
    }
};

window.StateManager = StateManager;
