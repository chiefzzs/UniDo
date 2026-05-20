/**
 * Vue 2.0 组件化架构
 * 基于设计文档: Ui相关的概念.md 第十一章
 * 
 * 组件层级:
 * L0: SessionContainer (根组件)
 * L1: RoundContainer, TaskGroupPanel
 * L2: IntentCard, MessageBlock, LLMInteraction, TaskCard
 * L3: LLMInputBlock, LLMOutputBlock, ToolExchange
 * L4: ThinkBlock, TextBlock, ToolCallBlock, ToolInputBlock, ToolOutputBlock
 */

import Vue from 'vue';

// ==================== L4: 底层输出组件 ====================

/**
 * ThinkBlock (思考块)
 * 对应服务: S21 LLM调用服务
 */
export const ThinkBlock = {
    name: 'ThinkBlock',
    props: {
        content: { type: String, default: '' },
        isStreaming: { type: Boolean, default: false },
        isExpanded: { type: Boolean, default: false }
    },
    template: `
        <details class="think-block" :class="{ streaming: isStreaming }">
            <summary>
                <span class="think-icon">🧠</span>
                <span>思考过程</span>
                <span v-if="isStreaming" class="streaming-indicator">分析中...</span>
            </summary>
            <div class="think-content" v-html="renderedContent"></div>
        </details>
    `,
    computed: {
        renderedContent() {
            return this.content || '思考中...';
        }
    }
};

/**
 * TextBlock (文本块)
 * 对应服务: S21 LLM调用服务
 */
export const TextBlock = {
    name: 'TextBlock',
    props: {
        content: { type: String, default: '' },
        isStreaming: { type: Boolean, default: false }
    },
    template: `
        <div class="text-block" :class="{ streaming: isStreaming }" v-html="renderedContent"></div>
    `,
    computed: {
        renderedContent() {
            return this.markdownRender(this.content);
        }
    },
    methods: {
        markdownRender(text) {
            if (!text) return '';
            return text
                .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
        }
    }
};

/**
 * ToolCallBlock (工具调用块)
 * 对应服务: S17 执行服务, S19 工具注册服务
 */
export const ToolCallBlock = {
    name: 'ToolCallBlock',
    props: {
        toolCalls: { type: Array, default: () => [] },
        state: { type: String, default: 'pending' }
    },
    template: `
        <div class="tool-call-block" :class="'state-' + state">
            <div class="tool-call-list">
                <span 
                    v-for="(call, index) in toolCalls" 
                    :key="index"
                    class="tool-badge"
                    :class="{ executing: state === 'running' }">
                    <span class="tool-icon">🔧</span>
                    <span class="tool-name">{{ call.tool_name || call.name }}</span>
                </span>
            </div>
            <div v-if="state === 'running'" class="tool-call-status">
                <span class="spinner">🔄</span> 执行中...
            </div>
        </div>
    `
};

/**
 * ToolInputBlock (工具输入块)
 * 对应服务: S20 工具实现服务
 */
export const ToolInputBlock = {
    name: 'ToolInputBlock',
    props: {
        toolName: { type: String, required: true },
        arguments: { type: Object, default: () => {} },
        timestamp: { type: String, default: '' }
    },
    template: `
        <div class="tool-input-block">
            <div class="tool-avatar">🔧</div>
            <div class="tool-content">
                <div class="tool-header">
                    <span class="tool-name">{{ toolName }}</span>
                    <span v-if="timestamp" class="tool-timestamp">{{ timestamp }}</span>
                </div>
                <pre class="tool-args">{{ formatArgs(arguments) }}</pre>
            </div>
        </div>
    `,
    methods: {
        formatArgs(args) {
            try {
                return JSON.stringify(args, null, 2);
            } catch {
                return String(args);
            }
        }
    }
};

/**
 * ToolOutputBlock (工具输出块)
 * 对应服务: S20 工具实现服务
 */
export const ToolOutputBlock = {
    name: 'ToolOutputBlock',
    props: {
        toolName: { type: String, required: true },
        result: { type: [String, Object], default: null },
        status: { type: String, default: 'success' },
        errorMessage: { type: String, default: '' },
        durationMs: { type: Number, default: 0 }
    },
    template: `
        <div class="tool-output-block" :class="'status-' + status">
            <div class="tool-avatar">{{ status === 'success' ? '✅' : '❌' }}</div>
            <div class="tool-content">
                <div class="tool-header">
                    <span class="tool-name">{{ toolName }}</span>
                    <span v-if="durationMs > 0" class="tool-duration">{{ durationMs }}ms</span>
                </div>
                <pre v-if="result" class="tool-result">{{ formatResult(result) }}</pre>
                <div v-if="errorMessage" class="tool-error">{{ errorMessage }}</div>
            </div>
        </div>
    `,
    methods: {
        formatResult(result) {
            if (typeof result === 'string') return result;
            try {
                return JSON.stringify(result, null, 2);
            } catch {
                return String(result);
            }
        }
    }
};

// ==================== L3: 交互层级组件 ====================

/**
 * LLMInputBlock (LLM输入块)
 * 对应服务: S21 LLM调用服务
 */
export const LLMInputBlock = {
    name: 'LLMInputBlock',
    props: {
        model: { type: String, default: '' },
        messages: { type: Array, default: () => [] },
        tools: { type: Array, default: () => [] },
        temperature: { type: Number, default: 0.7 },
        maxTokens: { type: Number, default: 4096 },
        displayMode: { type: String, default: 'collapsed' }
    },
    template: `
        <details class="llm-input-block" :class="'mode-' + displayMode">
            <summary>
                <span class="summary-icon">📥</span>
                <span>LLM Input</span>
                <span class="model-badge">{{ model }}</span>
            </summary>
            <div class="llm-input-content">
                <div class="input-section">
                    <label>Model:</label>
                    <span>{{ model }}</span>
                </div>
                <div class="input-section">
                    <label>Messages ({{ messages.length }}):</label>
                    <pre>{{ JSON.stringify(messages, null, 2) }}</pre>
                </div>
                <div v-if="tools.length" class="input-section">
                    <label>Tools ({{ tools.length }}):</label>
                    <pre>{{ JSON.stringify(tools, null, 2) }}</pre>
                </div>
                <div class="input-section">
                    <label>Config:</label>
                    <span>temperature: {{ temperature }}, max_tokens: {{ maxTokens }}</span>
                </div>
            </div>
        </details>
    `
};

/**
 * LLMOutputBlock (LLM输出块)
 * 对应服务: S21 LLM调用服务
 */
export const LLMOutputBlock = {
    name: 'LLMOutputBlock',
    components: { ThinkBlock, TextBlock, ToolCallBlock },
    props: {
        thinkContent: { type: String, default: '' },
        textContent: { type: String, default: '' },
        toolCalls: { type: Array, default: () => [] },
        isStreaming: { type: Boolean, default: false },
        thinkExpanded: { type: Boolean, default: false },
        toolCallState: { type: String, default: 'pending' }
    },
    template: `
        <div class="llm-output-block" :class="{ streaming: isStreaming }">
            <ThinkBlock 
                v-if="thinkContent"
                :content="thinkContent"
                :isStreaming="isStreaming"
                :isExpanded="thinkExpanded" />
            <TextBlock 
                :content="textContent"
                :isStreaming="isStreaming" />
            <ToolCallBlock 
                v-if="toolCalls.length"
                :toolCalls="toolCalls"
                :state="toolCallState" />
        </div>
    `
};

/**
 * ToolExchange (工具交互)
 * 对应服务: S17 执行服务, S20 工具实现服务
 */
export const ToolExchange = {
    name: 'ToolExchange',
    components: { ToolInputBlock, ToolOutputBlock },
    props: {
        exchangeId: { type: String, required: true },
        toolName: { type: String, required: true },
        toolInput: { type: Object, default: () => ({}) },
        toolOutput: { type: Object, default: () => ({}) },
        state: { type: String, default: 'pending' }
    },
    template: `
        <div class="tool-exchange" :class="'state-' + state" :data-exchange-id="exchangeId">
            <ToolInputBlock 
                v-if="state !== 'pending'"
                :toolName="toolName"
                :arguments="toolInput.arguments || {}"
                :timestamp="toolInput.timestamp" />
            <ToolOutputBlock 
                v-if="toolOutput.result !== undefined"
                :toolName="toolName"
                :result="toolOutput.result"
                :status="toolOutput.status || 'success'"
                :errorMessage="toolOutput.error_message || ''"
                :durationMs="toolOutput.duration_ms || 0" />
        </div>
    `
};

/**
 * LLMInteraction (大模型交互)
 * 对应服务: S21 LLM调用服务
 */
export const LLMInteraction = {
    name: 'LLMInteraction',
    components: { LLMInputBlock, LLMOutputBlock, ToolExchange },
    props: {
        interactionId: { type: String, required: true },
        parentRoundId: { type: String, required: true },
        model: { type: String, default: '' },
        messages: { type: Array, default: () => [] },
        tools: { type: Array, default: () => [] },
        state: { type: String, default: 'idle' },
        thinkContent: { type: String, default: '' },
        textContent: { type: String, default: '' },
        toolCalls: { type: Array, default: () => [] },
        toolCallState: { type: String, default: 'pending' },
        exchanges: { type: Array, default: () => [] }
    },
    template: `
        <div class="llm-interaction" :class="'state-' + state" :data-interaction-id="interactionId">
            <LLMInputBlock 
                :model="model"
                :messages="messages"
                :tools="tools"
                :displayMode="'collapsed'" />
            <LLMOutputBlock 
                :thinkContent="thinkContent"
                :textContent="textContent"
                :toolCalls="toolCalls"
                :isStreaming="state === 'streaming'"
                :toolCallState="toolCallState" />
            <div v-if="exchanges.length" class="tool-exchanges">
                <ToolExchange 
                    v-for="exchange in exchanges"
                    :key="exchange.exchange_id"
                    v-bind="exchange" />
            </div>
        </div>
    `
};

// ==================== L2: 轮次层级组件 ====================

/**
 * IntentCard (意图卡片)
 * 对应服务: S07 意图理解服务
 */
export const IntentCard = {
    name: 'IntentCard',
    props: {
        intentId: { type: String, default: '' },
        intentType: { type: String, default: 'simple' },
        intentDescription: { type: String, default: '' },
        taskGroupId: { type: String, default: '' },
        parameters: { type: Object, default: () => ({}) },
        state: { type: String, default: 'pending' }
    },
    template: `
        <div class="intent-card" :class="'state-' + state" :data-intent-id="intentId">
            <div class="intent-header">
                <span class="intent-type-badge" :class="'type-' + intentType">
                    {{ intentTypeLabel }}
                </span>
                <span class="intent-description">{{ intentDescription }}</span>
            </div>
            <div v-if="Object.keys(parameters).length" class="intent-params">
                <span v-for="(value, key) in parameters" :key="key" class="param-item">
                    <span class="param-key">{{ key }}:</span>
                    <span class="param-value">{{ value }}</span>
                </span>
            </div>
        </div>
    `,
    computed: {
        intentTypeLabel() {
            const labels = {
                simple: '简单意图',
                complex: '复杂意图',
                nested: '嵌套意图'
            };
            return labels[this.intentType] || this.intentType;
        }
    }
};

/**
 * MessageBlock (消息块)
 * 对应服务: S06 会话管理服务
 */
export const MessageBlock = {
    name: 'MessageBlock',
    props: {
        messageId: { type: String, required: true },
        role: { type: String, required: true },
        content: { type: String, default: '' },
        timestamp: { type: String, default: '' },
        attachments: { type: Array, default: () => [] }
    },
    template: `
        <div class="message-block" :class="[role + '-message', 'message-' + role]">
            <div class="message-avatar">{{ role === 'user' ? '👤' : '🤖' }}</div>
            <div class="message-content-wrapper">
                <div class="message-header">
                    <span class="message-role">{{ role === 'user' ? '用户' : '助手' }}</span>
                    <span v-if="timestamp" class="message-timestamp">{{ timestamp }}</span>
                </div>
                <div class="message-content" v-html="renderedContent"></div>
                <div v-if="attachments.length" class="message-attachments">
                    <div v-for="(attachment, index) in attachments" :key="index" class="attachment">
                        {{ attachment }}
                    </div>
                </div>
            </div>
        </div>
    `,
    methods: {
        markdownRender(text) {
            if (!text) return '';
            return text
                .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>');
        }
    },
    computed: {
        renderedContent() {
            return this.markdownRender(this.content);
        }
    }
};

/**
 * TaskCard (任务卡片)
 * 对应服务: S13 任务管理服务
 */
export const TaskCard = {
    name: 'TaskCard',
    props: {
        taskId: { type: String, required: true },
        groupId: { type: String, default: '' },
        name: { type: String, default: '' },
        description: { type: String, default: '' },
        status: { type: String, default: 'pending' },
        dependencies: { type: Array, default: () => [] },
        toolCalls: { type: Array, default: () => [] },
        result: { type: Object, default: () => ({}) }
    },
    template: `
        <div class="task-card" :class="'status-' + status" :data-task-id="taskId">
            <div class="task-status-icon">{{ statusIcon }}</div>
            <div class="task-content">
                <div class="task-header">
                    <span class="task-name">{{ name }}</span>
                    <span class="task-status-badge">{{ statusLabel }}</span>
                </div>
                <div v-if="description" class="task-description">{{ description }}</div>
                <div v-if="dependencies.length" class="task-dependencies">
                    <span class="dep-label">依赖:</span>
                    <span v-for="dep in dependencies" :key="dep" class="dep-item">{{ dep }}</span>
                </div>
                <div v-if="result.summary" class="task-result">
                    <span class="result-summary">{{ result.summary }}</span>
                </div>
            </div>
        </div>
    `,
    computed: {
        statusIcon() {
            const icons = {
                pending: '⬜',
                in_progress: '🔄',
                completed: '✅',
                failed: '❌',
                blocked: '⏸️'
            };
            return icons[this.status] || '⬜';
        },
        statusLabel() {
            const labels = {
                pending: '待处理',
                in_progress: '进行中',
                completed: '已完成',
                failed: '失败',
                blocked: '阻塞'
            };
            return labels[this.status] || this.status;
        }
    }
};

/**
 * RoundContainer (轮次容器)
 * 对应服务: S06 会话管理服务
 */
export const RoundContainer = {
    name: 'RoundContainer',
    components: { IntentCard, MessageBlock, LLMInteraction },
    props: {
        roundId: { type: String, required: true },
        roundIndex: { type: Number, default: 0 },
        intent: { type: Object, default: null },
        messages: { type: Array, default: () => [] },
        interactions: { type: Array, default: () => [] }
    },
    template: `
        <div class="round-container" :data-round-id="roundId">
            <div class="round-header">
                <span class="round-index">#{{ roundIndex + 1 }}</span>
            </div>
            <IntentCard v-if="intent" v-bind="intent" />
            <MessageBlock 
                v-for="msg in messages" 
                :key="msg.message_id"
                v-bind="msg" />
            <LLMInteraction 
                v-for="interaction in interactions"
                :key="interaction.interaction_id"
                v-bind="interaction" />
        </div>
    `
};

// ==================== L1: 会话层级组件 ====================

/**
 * TaskGroupPanel (任务组面板)
 * 对应服务: S12 任务组管理服务, S13 任务管理服务
 */
export const TaskGroupPanel = {
    name: 'TaskGroupPanel',
    components: { TaskCard },
    props: {
        groupId: { type: String, default: '' },
        name: { type: String, default: '任务组' },
        description: { type: String, default: '' },
        status: { type: String, default: 'pending' },
        tasks: { type: Array, default: () => [] }
    },
    template: `
        <div class="task-group-panel" :class="'status-' + status" :data-group-id="groupId">
            <div class="task-group-header">
                <span class="group-name">{{ name }}</span>
                <span class="group-status">{{ statusLabel }}</span>
            </div>
            <div class="task-list">
                <TaskCard 
                    v-for="task in tasks"
                    :key="task.task_id"
                    v-bind="task" />
            </div>
        </div>
    `,
    computed: {
        statusLabel() {
            const labels = {
                pending: '待处理',
                in_progress: '进行中',
                completed: '已完成',
                failed: '失败'
            };
            return labels[this.status] || this.status;
        }
    }
};

/**
 * SessionContainer (根组件)
 * 对应服务: S06 会话管理服务
 */
export const SessionContainer = {
    name: 'SessionContainer',
    components: { RoundContainer, TaskGroupPanel },
    props: {
        sessionId: { type: String, required: true },
        state: { type: String, default: 'ready' },
        rounds: { type: Array, default: () => [] },
        currentTaskGroup: { type: Object, default: null }
    },
    template: `
        <div class="session-container" :class="'state-' + state" :data-session-id="sessionId">
            <div class="rounds-container">
                <RoundContainer 
                    v-for="(round, index) in rounds"
                    :key="round.round_id"
                    v-bind="round"
                    :roundIndex="index" />
            </div>
            <TaskGroupPanel 
                v-if="currentTaskGroup"
                v-bind="currentTaskGroup" />
        </div>
    `
};

// ==================== 全局注册 ====================

export function registerComponents(Vue) {
    Vue.component('ThinkBlock', ThinkBlock);
    Vue.component('TextBlock', TextBlock);
    Vue.component('ToolCallBlock', ToolCallBlock);
    Vue.component('ToolInputBlock', ToolInputBlock);
    Vue.component('ToolOutputBlock', ToolOutputBlock);
    Vue.component('LLMInputBlock', LLMInputBlock);
    Vue.component('LLMOutputBlock', LLMOutputBlock);
    Vue.component('ToolExchange', ToolExchange);
    Vue.component('LLMInteraction', LLMInteraction);
    Vue.component('IntentCard', IntentCard);
    Vue.component('MessageBlock', MessageBlock);
    Vue.component('TaskCard', TaskCard);
    Vue.component('RoundContainer', RoundContainer);
    Vue.component('TaskGroupPanel', TaskGroupPanel);
    Vue.component('SessionContainer', SessionContainer);
}

export default {
    ThinkBlock,
    TextBlock,
    ToolCallBlock,
    ToolInputBlock,
    ToolOutputBlock,
    LLMInputBlock,
    LLMOutputBlock,
    ToolExchange,
    LLMInteraction,
    IntentCard,
    MessageBlock,
    TaskCard,
    RoundContainer,
    TaskGroupPanel,
    SessionContainer,
    registerComponents
};