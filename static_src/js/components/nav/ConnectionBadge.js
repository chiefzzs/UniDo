/**
 * ConnectionBadge - 连接状态组件
 */
import { StateManager } from '../infrastructure/StateManager.js';

export const ConnectionBadge = {
    name: 'ConnectionBadge',
    template: `
        <div class="connection-badge" :class="statusClass">
            <span class="connection-dot"></span>
            <span class="connection-text">{{ statusText }}</span>
        </div>
    `,
    data() {
        return {
            wsConnected: StateManager.getState('wsConnected')
        };
    },
    computed: {
        statusClass() {
            return this.wsConnected ? 'connected' : 'disconnected';
        },
        statusText() {
            return this.wsConnected ? '已连接' : '未连接';
        }
    },
    mounted() {
        this.unsubscribe = StateManager.subscribe('wsConnected', (connected) => {
            this.wsConnected = connected;
        });
    },
    destroyed() {
        if (this.unsubscribe) this.unsubscribe();
    }
};

window.ConnectionBadge = ConnectionBadge;
