/**
 * TextBlockComponent - 文本块组件
 */
export const TextBlockComponent = {
    name: 'TextBlockComponent',
    props: {
        content: { type: String, default: '' },
        streaming: { type: Boolean, default: false },
        dataResponseId: { type: String, default: '' }
    },
    template: `
        <div class="text-block" 
             :class="{ streaming }"
             :data-response-id="dataResponseId">
            <span class="text-content" v-html="renderedContent"></span>
            <span v-if="streaming" class="cursor">▊</span>
        </div>
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

window.TextBlockComponent = TextBlockComponent;
