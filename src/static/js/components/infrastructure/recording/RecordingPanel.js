/**
 * RecordingPanel - 录制控制面板组件
 * 迭代二：ST-v0.2-01, ST-v0.2-02
 * 
 * 功能：
 * - 显示录制状态
 * - 开始/停止录制
 * - 显示录制统计信息
 */

const RecordingPanel = {
    name: 'RecordingPanel',
    
    data() {
        return {
            isRecording: false,
            currentRecording: null,
            chunkCount: 0,
            recordingId: null
        };
    },
    
    created() {
        this.fetchRecordingStatus();
        
        // 监听WebSocket事件
        if (window.socket) {
            window.socket.on('recording_started', (data) => {
                this.isRecording = true;
                this.recordingId = data.interaction_id;
                this.$emit('recording-started', data);
            });
            
            window.socket.on('recording_stopped', (data) => {
                this.isRecording = false;
                this.recordingId = data.recording_id;
                this.currentRecording = null;
                this.$emit('recording-stopped', data);
            });
        }
        
        // 监听事件总线
        this.$on('event:recording.started', this.handleRecordingStarted);
        this.$on('event:recording.stopped', this.handleRecordingStopped);
    },
    
    beforeDestroy() {
        this.$off('event:recording.started', this.handleRecordingStarted);
        this.$off('event:recording.stopped', this.handleRecordingStopped);
    },
    
    methods: {
        async fetchRecordingStatus() {
            try {
                const response = await fetch('/api/recording/status');
                const data = await response.json();
                
                this.isRecording = data.is_recording;
                this.currentRecording = data.current_recording;
                this.chunkCount = data.current_recording?.chunk_count || 0;
                this.recordingId = data.current_recording?.recording_id;
            } catch (e) {
                console.error('获取录制状态失败:', e);
            }
        },
        
        async startRecording() {
            try {
                const response = await fetch('/api/recording/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        interaction_id: 'interaction-' + Date.now(),
                        session_id: window.currentSessionId || ''
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.isRecording = true;
                    this.recordingId = data.interaction_id;
                    this.$emit('recording-started', data);
                }
            } catch (e) {
                console.error('开始录制失败:', e);
                this.$emit('error', { message: '开始录制失败' });
            }
        },
        
        async stopRecording() {
            try {
                const response = await fetch('/api/recording/stop', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.isRecording = false;
                    this.recordingId = data.recording_id;
                    this.currentRecording = null;
                    this.chunkCount = 0;
                    this.$emit('recording-stopped', data);
                }
            } catch (e) {
                console.error('停止录制失败:', e);
                this.$emit('error', { message: '停止录制失败' });
            }
        },
        
        handleRecordingStarted(data) {
            if (data.event_type === 'recording.started') {
                this.isRecording = true;
                this.recordingId = data.payload?.interaction_id;
            }
        },
        
        handleRecordingStopped(data) {
            if (data.event_type === 'recording.stopped') {
                this.isRecording = false;
                this.recordingId = data.payload?.recording_id;
                this.currentRecording = null;
            }
        }
    },
    
    template: `
        <div class="recording-panel">
            <div class="panel-header">
                <span class="panel-title">录制控制</span>
                <span class="recording-status" :class="{ active: isRecording }">
                    {{ isRecording ? '录制中' : '已停止' }}
                </span>
            </div>
            
            <div class="panel-content">
                <div class="recording-indicator" v-if="isRecording">
                    <span class="recording-dot"></span>
                    <span>正在录制...</span>
                </div>
                
                <div class="recording-stats" v-if="isRecording">
                    <div class="stat-item">
                        <span class="stat-label">录制ID</span>
                        <span class="stat-value">{{ recordingId ? recordingId.substring(0, 8) + '...' : '-' }}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">数据块</span>
                        <span class="stat-value">{{ chunkCount }}</span>
                    </div>
                </div>
                
                <div class="panel-actions">
                    <button 
                        class="btn" 
                        :class="isRecording ? 'btn-danger' : 'btn-primary'"
                        @click="isRecording ? stopRecording() : startRecording()">
                        {{ isRecording ? '⏹ 停止录制' : '🔴 开始录制' }}
                    </button>
                </div>
            </div>
        </div>
    `
};

// 注册为全局组件
if (window.Vue) {
    Vue.component('recording-panel', RecordingPanel);
}

export default RecordingPanel;
