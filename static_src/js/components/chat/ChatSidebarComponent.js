/**
 * ChatSidebarComponent - 聊天侧边栏组件
 */
import { ProjectManager } from '../services/ProjectManager.js';
import { SessionManager } from '../services/SessionManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ChatSidebarComponent = {
    name: 'ChatSidebarComponent',
    props: {
        projectId: { type: String, default: null },
        sessions: { type: Array, default: () => [] },
        currentSessionId: { type: String, default: null }
    },
    template: `
        <aside class="chat-sidebar">
            <div class="chat-sidebar-header">
                <select v-model="selectedProject" @change="handleProjectChange" class="project-select">
                    <option value="">选择项目</option>
                    <option v-for="p in projects" :key="p.id" :value="p.id">
                        {{ p.name }}
                    </option>
                </select>
                <button 
                    class="btn btn-sm btn-outline" 
                    @click="handleCreateSession"
                    :disabled="!selectedProject"
                    :title="selectedProject ? '新建会话' : '请先选择项目'">
                    + 新建
                </button>
            </div>
            <div class="chat-sidebar-content">
                <div class="section-title">💬 会话列表</div>
                <div class="session-list">
                    <div
                        v-for="session in sessions"
                        :key="session.id"
                        class="session-item"
                        :class="{ active: session.id === currentSessionId }"
                        @click="handleSessionSelect(session.id)">
                        <span class="session-title">{{ session.title || '未命名会话' }}</span>
                        <span class="session-date">{{ formatDate(session.updated_at) }}</span>
                    </div>
                    <div v-if="!sessions.length" class="empty-hint">
                        {{ selectedProject ? '暂无会话，点击上方"新建"按钮创建' : '请先选择项目' }}
                    </div>
                </div>
            </div>
        </aside>
    `,
    data() {
        return {
            projects: [],
            selectedProject: this.projectId || ''
        };
    },
    async mounted() {
        console.log('[ChatSidebar] Mounted with props:', {
            projectId: this.projectId,
            sessions: this.sessions,
            currentSessionId: this.currentSessionId
        });
        
        await this.loadProjects();

        // 监听项目事件
        EventBus.on('project:loaded', ({ projects }) => {
            console.log('[ChatSidebar] Projects loaded:', projects);
            this.projects = projects;
        });
        EventBus.on('session:loaded', ({ sessions }) => {
            console.log('[ChatSidebar] Sessions loaded:', sessions);
            this.sessions = sessions;
        });
    },
    methods: {
        async loadProjects() {
            try {
                await ProjectManager.getProjects();
                this.projects = StateManager.getState('projects');
            } catch (e) {
                console.error('Load projects error:', e);
            }
        },
        handleProjectChange() {
            StateManager.setState('currentProjectId', this.selectedProject);
            if (this.selectedProject) {
                SessionManager.getSessions(this.selectedProject);
            }
        },
        handleSessionSelect(sessionId) {
            SessionManager.switchSession(sessionId);
        },
        async handleCreateSession() {
            const projectId = this.selectedProject;
            if (projectId) {
                await SessionManager.createSession(projectId);
            }
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '';
        }
    }
};

window.ChatSidebarComponent = ChatSidebarComponent;
