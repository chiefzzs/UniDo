/**
 * PageRouter - 页面路由
 * 通过 Vue 状态管理控制页面显示，支持 URL 持久化
 */
import { EventBus } from './EventBus.js';
import { StateManager } from './StateManager.js';

export const PageRouter = {
    // 路由映射表
    routeMap: {
        'chat': { component: 'ChatPageComponent', label: '对话' },
        'projects': { component: 'ProjectPageComponent', label: '项目管理' },
        'workspaces': { component: 'WorkspacePageComponent', label: '工作区管理' },
        'models': { component: 'ModelPageComponent', label: '模型配置' },
        'tools': { component: 'ToolPageComponent', label: '工具管理' },
        'prompts': { component: 'PromptPageComponent', label: '提示词管理' },
        'storage': { component: 'StoragePageComponent', label: '存储配置' }
    },

    // 初始化路由
    init() {
        // 从 URL 恢复当前页面
        const hash = window.location.hash.replace('#', '');
        const initialPage = hash || StateManager.getState('currentPage') || 'chat';
        StateManager.setState('currentPage', initialPage);

        // 监听菜单点击
        EventBus.on('menu:click', ({ menu }) => {
            this.navigateTo(menu.page);
        });

        // 监听浏览器前进后退
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.replace('#', '');
            if (hash && hash !== StateManager.getState('currentPage')) {
                StateManager.setState('currentPage', hash);
                EventBus.emit('page:change', { page: hash });
            }
        });

        console.log('[PageRouter] Initialized, current page:', initialPage);
    },

    // 导航到指定页面
    navigateTo(page) {
        if (!page || page === StateManager.getState('currentPage')) return;

        StateManager.setState('currentPage', page);
        window.location.hash = page;  // 更新 URL
        EventBus.emit('page:change', { page });
    },

    // 获取当前页面
    getCurrentPage() {
        return StateManager.getState('currentPage');
    },

    // 获取路由配置
    getRoute(page) {
        return this.routeMap[page];
    },

    // 检查页面是否激活
    isPageActive(page) {
        return StateManager.getState('currentPage') === page;
    }
};

window.PageRouter = PageRouter;
