/**
 * LLMInvokePanel - LLM调用面板组件
 * 迭代二：ST-v0.2-04, ST-v0.2-05, ST-v0.2-06
 * 
 * 功能：
 * - 显示模型信息
 * - 同步调用LLM
 * - 流式调用LLM
 * - 显示调用结果
 */

const LLMInvokePanel = {
    name: 'LLMInvokePanel',
    
    data() {
        return {
            // 模型信息
            modelInfo: {
                model_name: '',
                model_address: '',
                api_type: '',
                temperature: 0.7,
                max_tokens: 4096
            },
            
            // 调用参数
            messages: [],
            userInput: '',
            temperature: 0.7,
            maxTokens: 4096,
            streamMode: true,
            
            // 调用状态
            loading: false,
            responseText: '',
            streamingText: '',
            error: null,
            callDuration: 0,
            
            // 模型信息加载状态
            modelInfoLoading: true
        };
    },
    
    created() {
        this.fetchModelInfo();
        
        // 监听WebSocket流式文本事件
        if (window.socket) {
            window.socket.on('stream_text', (data) => {
                if (this.loading && this.streamMode) {
                    this.streamingText += data.delta || '';
                }
            });
            
            window.socket.on('llm.response', (data) => {
                if (this.loading && !this.streamMode) {
                    this.responseText = data.content || '';
                }
            });
        }
    },
    
    methods: {
        async fetchModelInfo() {
            this.modelInfoLoading = true;
            try {
                const response = await fetch('/api/llm/model-info');
                const data = await response.json();
                
                this.modelInfo = {
                    model_name: data.model_name || 'default',
                    model_address: data.model_address || '',
                    api_type: data.api_type || 'qwen',
                    temperature: data.temperature || 0.7,
                    max_tokens: data.max_tokens || 4096
                };
                
                this.temperature = this.modelInfo.temperature;
                this.maxTokens = this.modelInfo.max_tokens;
                
                this.$emit('model-info-loaded', this.modelInfo);
            } catch (e) {
                console.error('获取模型信息失败:', e);
                this.$emit('error', { message: '获取模型信息失败' });
            } finally {
                this.modelInfoLoading = false;
            }
        },
        
        async invokeLLM() {
            if (!this.userInput.trim()) {
                this.$emit('error', { message: '请输入消息' });
                return;
            }
            
            this.loading = true;
            this.responseText = '';
            this.streamingText = '';
            this.error = null;
            const startTime = Date.now();
            
            try {
                const response = await fetch('/api/llm/invoke', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: [
                            ...this.messages,
                            { role: 'user', content: this.userInput }
                        ],
                        model: this.modelInfo.model_name,
                        temperature: this.temperature,
                        max_tokens: this.maxTokens,
                        stream: this.streamMode
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error: ${response.status}`);
                }
                
                if (this.streamMode) {
                    // 流式响应处理
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();
                    
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\n');
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = JSON.parse(line.slice(6));
                                if (data.delta) {
                                    this.streamingText += data.delta;
                                }
                                if (data.finish_reason) {
                                    this.callDuration = Date.now() - startTime;
                                }
                            }
                        }
                    }
                    
                    // 添加到消息历史
                    this.messages.push({ role: 'user', content: this.userInput });
                    this.messages.push({ role: 'assistant', content: this.streamingText });
                } else {
                    // 同步响应处理
                    const data = await response.json();
                    this.responseText = data.content || '';
                    this.callDuration = Date.now() - startTime;
                    
                    // 添加到消息历史
                    this.messages.push({ role: 'user', content: this.userInput });
                    this.messages.push({ role: 'assistant', content: this.responseText });
                }
                
                this.userInput = '';
                this.$emit('llm-response', { 
                    content: this.streamMode ? this.streamingText : this.responseText,
                    duration: this.callDuration
                });
                
            } catch (e) {
                console.error('LLM调用失败:', e);
                this.error = e.message;
                this.$emit('error', { message: 'LLM调用失败: ' + e.message });
            } finally {
                this.loading = false;
            }
        },
        
        clearHistory() {
            this.messages = [];
            this.responseText = '';
            this.streamingText = '';
        }
    },
    
    template: `
        <div class="llm-invoke-panel">
            <div class="panel-header">
                <span class="panel-title">LLM调用</span>
                <button class="refresh-btn" @click="fetchModelInfo">🔄</button>
            </div>
            
            <div class="panel-content">
                <!-- 模型信息区域 -->
                <div class="model-info-section">
                    <div class="section-label">模型信息</div>
                    <div class="loading-state" v-if="modelInfoLoading">
                        <span class="spinner"></span>
                        <span>加载中...</span>
                    </div>
                    <div class="model-info" v-else>
                        <div class="info-row">
                            <span class="info-label">模型</span>
                            <span class="info-value">{{ modelInfo.model_name }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">API类型</span>
                            <span class="info-value">{{ modelInfo.api_type }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Temperature</span>
                            <span class="info-value">{{ modelInfo.temperature }}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">最大Token</span>
                            <span class="info-value">{{ modelInfo.max_tokens }}</span>
                        </div>
                    </div>
                </div>
                
                <!-- 调用参数区域 -->
                <div class="invoke-params">
                    <div class="param-row">
                        <label>Temperature</label>
                        <input type="range" v-model.number="temperature" min="0" max="2" step="0.1">
                        <span class="param-value">{{ temperature }}</span>
                    </div>
                    <div class="param-row">
                        <label>Max Tokens</label>
                        <input type="number" v-model.number="maxTokens" min="1" max="8192">
                    </div>
                    <div class="param-row">
                        <label class="checkbox-label">
                            <input type="checkbox" v-model="streamMode">
                            <span>流式输出</span>
                        </label>
                    </div>
                </div>
                
                <!-- 消息输入区域 -->
                <div class="message-input">
                    <textarea 
                        v-model="userInput" 
                        placeholder="输入消息..."
                        rows="3"
                        @keydown.enter.exact.prevent="invokeLLM">
                    </textarea>
                    <button 
                        class="invoke-btn" 
                        :disabled="loading || !userInput.trim()"
                        @click="invokeLLM">
                        {{ loading ? '调用中...' : '发送' }}
                    </button>
                </div>
                
                <!-- 响应显示区域 -->
                <div class="response-area">
                    <div class="response-header">
                        <span>响应</span>
                        <span class="response-meta" v-if="callDuration > 0">
                            耗时: {{ callDuration }}ms
                        </span>
                    </div>
                    
                    <div class="loading-indicator" v-if="loading">
                        <span class="spinner"></span>
                        <span>{{ streamMode ? '流式输出中...' : '加载中...' }}</span>
                    </div>
                    
                    <div class="error-message" v-if="error">
                        ❌ {{ error }}
                    </div>
                    
                    <div class="response-text" v-if="!loading && !error">
                        <span v-if="streamMode">{{ streamingText }}</span>
                        <span v-else>{{ responseText }}</span>
                    </div>
                </div>
                
                <!-- 历史消息 -->
                <div class="history-section" v-if="messages.length > 0">
                    <div class="history-header">
                        <span>历史消息 ({{ messages.length / 2 }}轮)</span>
                        <button class="clear-btn" @click="clearHistory">清空</button>
                    </div>
                </div>
            </div>
        </div>
    `
};

// 注册为全局组件
if (window.Vue) {
    Vue.component('llm-invoke-panel', LLMInvokePanel);
}

export default LLMInvokePanel;
