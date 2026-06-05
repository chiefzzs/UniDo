/**
 * ThemeToggle - 主题切换组件
 */
import { StateManager } from '../infrastructure/StateManager.js';

export const ThemeToggle = {
    name: 'ThemeToggle',
    template: `
        <button class="theme-toggle-btn" @click="toggleTheme" :title="theme === 'dark' ? '切换到亮色模式' : '切换到暗色模式'">
            {{ theme === 'dark' ? '🌙' : '☀️' }}
        </button>
    `,
    data() {
        return {
            theme: StateManager.getState('theme')
        };
    },
    methods: {
        toggleTheme() {
            const newTheme = this.theme === 'dark' ? 'light' : 'dark';
            StateManager.setState('theme', newTheme);
            document.body.setAttribute('data-theme', newTheme);
            this.theme = newTheme;
        }
    },
    mounted() {
        this.unsubscribe = StateManager.subscribe('theme', (theme) => {
            this.theme = theme;
        });
    },
    destroyed() {
        if (this.unsubscribe) this.unsubscribe();
    }
};

window.ThemeToggle = ThemeToggle;
