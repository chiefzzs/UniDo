/**
 * ReplayControls - 回放控制组件
 * 迭代二：ST-v0.2-07, ST-v0.2-08
 * 
 * 功能：
 * - 回放模式开关
 * - 回放速度选择
 * - 显示回放状态
 */

const ReplayControls = {
    name: 'ReplayControls',
    
    data() {
        return {
            replayEnabled: false,
            replayMode: 'off',
            replaySpeed: 'normal',
            availableRecordings: 0,
            totalRecordings: 0
        };
    },
    
    created() {
        this.fetchReplayStatus();
    },
    
    methods: {
        async fetchReplayStatus() {
            try {
                const response = await fetch('/api/replay/status');
                const data = await response.json();
                
                this.replayMode = data.replay_mode;
                this.replayEnabled = data.replay_mode !== 'off';
                this.totalRecordings = data.total_recordings;
                this.availableRecordings = data.available_recordings;
            } catch (e) {
                console.error('获取回放状态失败:', e);
            }
        },
        
        async toggleReplayMode() {
            try {
                const response = await fetch('/api/replay/enable', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        enabled: !this.replayEnabled,
                        mode: this.replayMode
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.replayEnabled = data.enabled;
                    this.replayMode = data.replay_mode;
                    window.isReplayMode = this.replayEnabled;
                    this.$emit('replay-mode-changed', { enabled: this.replayEnabled, mode: this.replayMode });
                }
            } catch (e) {
                console.error('切换回放模式失败:', e);
                this.$emit('error', { message: '切换回放模式失败' });
            }
        },
        
        async setReplaySpeed(speed) {
            try {
                const response = await fetch('/api/replay/speed', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ speed: speed })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.replaySpeed = data.speed;
                    this.$emit('replay-speed-changed', { speed: data.speed, description: data.description });
                }
            } catch (e) {
                console.error('设置回放速度失败:', e);
                this.$emit('error', { message: '设置回放速度失败' });
            }
        }
    },
    
    template: `
        <div class="replay-controls">
            <div class="panel-header">
                <span class="panel-title">回放控制</span>
                <span class="replay-badge" :class="{ active: replayEnabled }">
                    {{ replayEnabled ? '已启用' : '已禁用' }}
                </span>
            </div>
            
            <div class="panel-content">
                <div class="replay-status">
                    <span class="status-label">可用录制:</span>
                    <span class="status-value">{{ availableRecordings }} / {{ totalRecordings }}</span>
                </div>
                
                <div class="control-group">
                    <label class="control-label">回放模式</label>
                    <div class="mode-switch-wrapper">
                        <label class="switch">
                            <input type="checkbox" :checked="replayEnabled" @change="toggleReplayMode">
                            <span class="slider"></span>
                        </label>
                        <span class="switch-label">{{ replayEnabled ? '开启' : '关闭' }}</span>
                    </div>
                </div>
                
                <div class="control-group" v-if="replayEnabled">
                    <label class="control-label">回放速度</label>
                    <div class="speed-buttons">
                        <button 
                            class="speed-btn"
                            :class="{ active: replaySpeed === 'normal' }"
                            @click="setReplaySpeed('normal')">
                            正常
                        </button>
                        <button 
                            class="speed-btn"
                            :class="{ active: replaySpeed === 'fast' }"
                            @click="setReplaySpeed('fast')">
                            快速
                        </button>
                        <button 
                            class="speed-btn"
                            :class="{ active: replaySpeed === 'debug' }"
                            @click="setReplaySpeed('debug')">
                            详细
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `
};

// 注册为全局组件
if (window.Vue) {
    Vue.component('replay-controls', ReplayControls);
}

export default ReplayControls;
