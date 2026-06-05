/**
 * ResponseBlockComponent - 单次LLM 交互响应块组件
 * 
 * 职责：
 * 1. 展示单次 LLM 交互的完整响应
 * 2. 包含思考块、文本块、工具调用块
 * 3. 管理响应块状态（streaming/completed）
 */
export const ResponseBlockComponent = {
    name: 'ResponseBlockComponent',
    props: {
        block: { 
            type: Object, 
            required: true,
            validator: (block) => {
                // 只验证基本结构，不验证内容（内容会动态更新）
                return block && block.responseId && block.requestId;
            }
        }
    },
    data() {
        return {
            debugMode: false
        };
    },
    mounted() {
        if (this.debugMode) {
            console.log('[ResponseBlock] mounted, block:', this.block);
            console.log('[ResponseBlock] block type:', typeof this.block);
            console.log('[ResponseBlock] block.responseId:', this.block.responseId);
            console.log('[ResponseBlock] block.thinkContent:', this.block.thinkContent);
            console.log('[ResponseBlock] block.textContent:', this.block.textContent);
            console.log('[ResponseBlock] block.toolCalls:', this.block.toolCalls);
        }
    },
    template: `
        <div class="response-block" 
             :class="'status-' + (block.status || 'completed')"
             :data-response-id="block.responseId"
             :data-request-id="block.requestId">
            <!-- DEBUG INFO -->
            <div v-if="debugMode" class="debug-info">
                [DEBUG] responseId: {{ block.responseId }}, 
                think: {{ !!block.thinkContent }}, 
                reason: {{ !!block.reasonContent }},
                text: {{ !!block.textContent }}, 
                tools: {{ block.toolCalls ? block.toolCalls.length : 0 }}
            </div>
            
            <!-- thinking 思考块 -->
            <think-block-component
                v-if="block.thinkContent"
                :content="block.thinkContent"
                :expanded="false"
                :status="block.status"
                :data-response-id="block.responseId">
            </think-block-component>
            
            <!-- reasoning 推理块 -->
            <reason-block-component
                v-if="block.reasonContent"
                :content="block.reasonContent"
                :expanded="false"
                :status="block.status"
                :data-response-id="block.responseId">
            </reason-block-component>
            
            <!-- 文本块 -->
            <text-block-component
                :content="block.textContent"
                :streaming="block.status === 'streaming'"
                :status="block.status"
                :data-response-id="block.responseId">
            </text-block-component>
            
            <!-- 工具调用块 -->
            <div class="tool-calls" v-if="block.toolCalls && block.toolCalls.length">
                <tool-card-component
                    v-for="tool in block.toolCalls"
                    :key="tool.callId"
                    :toolCall="tool">
                </tool-card-component>
            </div>
        </div>
    `
};

window.ResponseBlockComponent = ResponseBlockComponent;
