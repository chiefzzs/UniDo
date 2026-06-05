/**
 * ToolCardComponent - 工具卡片组件
 */
export const ToolCardComponent = {
    name: 'ToolCardComponent',
    props: {
        toolCall: { type: Object, required: true }
    },
    template: `
        <div class="tool-execution-card" 
             :class="'status-' + toolCall.status"
             :data-tool-call-id="toolCall.callId"
             :data-tool-name="toolCall.toolName">
            <div class="tool-card-header">
                <span class="tool-icon">🔧</span>
                <span class="tool-name">{{ toolCall.toolName }}</span>
                <span class="tool-status-badge" :class="toolCall.status">
                    {{ statusLabel }}
                </span>
            </div>
            <div class="tool-section">
                <div class="section-header">调用参数</div>
                <pre class="section-content">{{ formatArgs(toolCall.args) }}</pre>
            </div>
            <div class="tool-section" v-if="toolCall.output">
                <div class="section-header">执行输出</div>
                <pre class="section-content">{{ toolCall.output }}</pre>
            </div>
            <div class="tool-section" v-if="toolCall.error">
                <div class="section-header error-header">❌ 错误信息</div>
                <pre class="section-content error-content">{{ toolCall.error }}</pre>
            </div>
            <div class="tool-section" v-if="toolCall.result && !toolCall.error">
                <div class="section-header">执行结果</div>
                <pre class="section-content">{{ formatResult(toolCall.result) }}</pre>
            </div>
        </div>
    `,
    computed: {
        statusLabel() {
            const labels = {
                pending: '⏳ 执行中',
                running: '⏳ 执行中',
                completed: '✅ 完成',
                failed: '❌ 失败'
            };
            return labels[this.toolCall.status] || '⏳ 执行中';
        }
    },
    methods: {
        formatArgs(args) {
            try {
                return typeof args === 'string' ? args : JSON.stringify(args, null, 2);
            } catch (e) { return String(args); }
        },
        formatResult(result) {
            try {
                return typeof result === 'string' ? result : JSON.stringify(result, null, 2);
            } catch (e) { return String(result); }
        }
    }
};

window.ToolCardComponent = ToolCardComponent;
