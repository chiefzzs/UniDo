/**
 * ReplayToggle - 录制/回放切换组件
 */
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { ApiClient } from '../infrastructure/ApiClient.js';

export const ReplayToggle = {
    name: 'ReplayToggle',
    data() {
        return {
            replayEnabled: StateManager.getState('replayEnabled') !== undefined ? StateManager.getState('replayEnabled') : true,
            replayMode: StateManager.getState('replayMode') || 'record'
        };
    },
    async mounted() {
        // 从后端获取当前模式，确保前端与后端同步
        try {
            const response = await ApiClient.request('GET', '/llm/mode');
            console.log('[ReplayToggle] Fetched mode from backend:', response);
            
            if (response && response.mode) {
                this.replayMode = response.mode;
                this.replayEnabled = response.mode === 'record';
                StateManager.setState('replayMode', response.mode);
                StateManager.setState('replayEnabled', response.mode === 'record');
            }
        } catch (error) {
            console.error('[ReplayToggle] Failed to fetch mode from backend:', error);
            // 如果获取失败，使用本地默认值（录制模式）
            this.replayMode = 'record';
            this.replayEnabled = true;
        }
    },
    template: `
        <div class="replay-toggle" :class="{ active: replayEnabled }" :title="replayEnabled ? '录制模式' : '回放模式'" @click="toggleReplay">
            <span class="toggle-icon">{{ replayEnabled ? '📹' : '🔄' }}</span>
            <span class="toggle-label">{{ replayEnabled ? '录制' : '回放' }}</span>
        </div>
    `,
    methods: {
        async toggleReplay() {
            // 切换状态
            const enabled = !this.replayEnabled;
            // 后端 API 只接受 'record' 或 'loopback'
            const newMode = enabled ? 'record' : 'loopback';
            
            console.log('[ReplayToggle] Toggling replay mode:', enabled ? 'ON (record)' : 'OFF (loopback)');
            
            try {
                // 调用后端 API 设置模式（注意：ApiClient.baseUrl 已经是 /api，所以直接用 /llm/mode）
                const response = await ApiClient.request('POST', '/llm/mode', {
                    mode: newMode
                });
                
                console.log('[ReplayToggle] Backend response:', response);
                
                // 更新前端状态
                this.replayEnabled = enabled;
                this.replayMode = newMode;
                StateManager.setState('replayEnabled', enabled);
                StateManager.setState('replayMode', newMode);
                EventBus.emit('replay:mode-changed', {
                    enabled: enabled,
                    mode: newMode
                });
                
                console.log('[ReplayToggle] Mode changed:', this.replayEnabled);
            } catch (error) {
                console.error('[ReplayToggle] Failed to set mode:', error);
                // 如果后端调用失败，仍然更新前端状态（降级处理）
                this.replayEnabled = enabled;
                this.replayMode = newMode;
                StateManager.setState('replayEnabled', enabled);
                StateManager.setState('replayMode', newMode);
                EventBus.emit('replay:mode-changed', {
                    enabled: enabled,
                    mode: newMode
                });
            }
        }
    }
};

window.ReplayToggle = ReplayToggle;
