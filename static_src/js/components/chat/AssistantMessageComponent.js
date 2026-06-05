/**
 * AssistantMessageComponent - 助手消息组件
 * 
 * 职责：
 * 1. 展示助手的完整回复（包含多次 LLM 交互）
 * 2. 包含多个 ResponseBlock（每次 LLM 交互一个）
 * 3. 管理助手消息块状态
 */
import { ResponseBlockComponent } from './ResponseBlockComponent.js';

export const AssistantMessageComponent = {
    name: 'AssistantMessageComponent',
    components: {
        ResponseBlockComponent
    },
    props: {
        message: { 
            type: Object, 
            required: true,
            validator: (msg) => {
                return msg && msg.id && msg.role === 'assistant';
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
            console.log('[AssistantMessage] mounted, message:', this.message);
            console.log('[AssistantMessage] message.id:', this.message.id);
            console.log('[AssistantMessage] responseBlocks:', this.message.responseBlocks);
            console.log('[AssistantMessage] responseBlocks type:', typeof this.message.responseBlocks);
            console.log('[AssistantMessage] responseBlocks length:', this.message.responseBlocks ? this.message.responseBlocks.length : 0);
            console.log('[AssistantMessage] responseBlocks is Array:', Array.isArray(this.message.responseBlocks));
        }
    },
    computed: {
        blocks() {
            const responseBlockIds = this.message.responseBlocks || [];
            console.log('[AssistantMessage] computed blocks, responseBlockIds:', responseBlockIds.length);
            
            // 将 responseId 字符串转换为实际的 ResponseBlock 对象
            const result = responseBlockIds.map(id => {
                const block = window.StateManager.state.responseBlocks.get(id);
                if (!block) {
                    console.warn(`[AssistantMessage] ResponseBlock not found for id: ${id}`);
                }
                return block;
            }).filter(Boolean);
            
            console.log('[AssistantMessage] computed blocks, resolved:', result.length);
            return result;
        }
    },
    template: `
        <div class="message-item assistant-message"
             :data-message-id="message.id"
             :data-message-role="message.role"
             :data-dialog-id="message.dialogId">
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <!-- DEBUG INFO -->
                <div v-if="debugMode" class="debug-info">
                    [DEBUG] message.id: {{ message.id }}, 
                    responseBlocks: {{ blocks.length }}
                </div>
                <!-- 多次 LLM 交互，每次一个响应块 -->
                <response-block-component
                    v-for="responseBlock in blocks"
                    :key="responseBlock.responseId"
                    :block="responseBlock">
                </response-block-component>
            </div>
        </div>
    `
};

window.AssistantMessageComponent = AssistantMessageComponent;
