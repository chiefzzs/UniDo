/**
 * NavBarComponent - 导航栏组件
 */
import { NavMenuComponent } from './NavMenuComponent.js';
import { ThemeToggle } from './ThemeToggle.js';
import { ConnectionBadge } from './ConnectionBadge.js';
import { ReplayToggle } from './ReplayToggle.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const NavBarComponent = {
    name: 'NavBarComponent',
    components: {
        NavMenuComponent,
        ThemeToggle,
        ConnectionBadge,
        ReplayToggle
    },
    data() {
        return {
            menus: StateManager.getState('menus'),
            activePage: StateManager.getState('currentPage') || 'chat'
        };
    },
    template: `
        <nav class="top-nav">
            <div class="logo">
                <span class="logo-icon">🤖</span>
                <span class="logo-text">AI 助手</span>
            </div>
            <nav-menu-component
                :menus="menus"
                :activePage="activePage">
            </nav-menu-component>
            <div class="right-section">
                <replay-toggle></replay-toggle>
                <theme-toggle></theme-toggle>
                <connection-badge></connection-badge>
            </div>
        </nav>
    `,
    mounted() {
        console.log('[NavBar] Mounted with menus:', this.menus);
        console.log('[NavBar] Initial activePage:', this.activePage);
        
        // 监听状态变化
        StateManager.subscribe('currentPage', (newPage) => {
            console.log('[NavBar] Page changed to:', newPage);
            this.activePage = newPage;
        });
        
        // 监听菜单点击
        EventBus.on('menu:click', ({ menu }) => {
            console.log('[NavBar] Menu clicked:', menu);
        });
    }
};

window.NavBarComponent = NavBarComponent;
