/**
 * ReasonBlockComponent - 推理块组件（reasoning_content字段）
 */
export const ReasonBlockComponent = {
    name: 'ReasonBlockComponent',
    props: {
        content: { type: String, default: '' },
        expanded: { type: Boolean, default: false },
        dataResponseId: { type: String, default: '' }
    },
    template: `
        <details class="reason-block" 
                 :open="expanded"
                 :data-response-id="dataResponseId"
                 :data-reason-content="content ? 'true' : 'false'">
            <summary>
                <span class="reason-icon">💡</span>
                <span>推理过程</span>
            </summary>
            <div class="reason-content">{{ content }}</div>
        </details>
    `
};

window.ReasonBlockComponent = ReasonBlockComponent;
