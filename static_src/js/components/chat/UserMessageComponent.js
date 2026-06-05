/**
 * UserMessageComponent - 用户消息组件
 */
export const UserMessageComponent = {
    name: 'UserMessageComponent',
    props: {
        message: { type: Object, required: true }
    },
    template: `
        <div class="message-item user-message" 
             :data-message-id="message.id"
             :data-message-role="message.role">
            <div class="message-avatar">👤</div>
            <div class="message-content">
                <div class="message-bubble">
                    {{ message.content }}
                </div>
                <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
        </div>
    `,
    methods: {
        formatTime(timestamp) {
            return timestamp ? new Date(timestamp).toLocaleTimeString() : '';
        }
    }
};

window.UserMessageComponent = UserMessageComponent;
