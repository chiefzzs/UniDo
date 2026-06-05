/**
 * NavMenuComponent - 导航菜单组件
 */
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const NavMenuComponent = {
    name: 'NavMenuComponent',
    props: {
        menus: { type: Array, default: () => [] },
        activePage: { type: String, default: 'chat' }
    },
    template: `
        <div class="menu-tabs">
            <button
                v-for="menu in sortedMenus"
                :key="menu.id"
                class="menu-tab"
                :class="{ active: activePage === menu.page }"
                @click="handleClick(menu)">
                <span class="menu-icon">{{ menu.icon }}</span>
                <span class="menu-label">{{ menu.label }}</span>
            </button>
        </div>
    `,
    computed: {
        sortedMenus() {
            return this.menus.sort((a, b) => a.sortOrder - b.sortOrder);
        }
    },
    methods: {
        handleClick(menu) {
            EventBus.emit('menu:click', { menu });
        }
    }
};

window.NavMenuComponent = NavMenuComponent;
