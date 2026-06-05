/**
 * ThinkBlockComponent - 思考块组件
 */
export const ThinkBlockComponent = {
    name: 'ThinkBlockComponent',
    props: {
        content: { type: String, default: '' },
        expanded: { type: Boolean, default: false },
        dataResponseId: { type: String, default: '' }
    },
    template: `
        <details class="think-block" 
                 :open="expanded"
                 :data-response-id="dataResponseId"
                 :data-think-content="content ? 'true' : 'false'">
            <summary>
                <span class="think-icon">🧠</span>
                <span>思考过程</span>
            </summary>
            <div class="think-content">{{ content }}</div>
        </details>
    `
};

window.ThinkBlockComponent = ThinkBlockComponent;
