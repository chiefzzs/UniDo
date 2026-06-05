/**
 * ProjectPageComponent - 项目管理页面组件
 */
import { ProjectManager } from '../services/ProjectManager.js';
import { WorkspaceManager } from '../services/WorkspaceManager.js';
import { ModelManager } from '../services/ModelManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ProjectPageComponent = {
    name: 'ProjectPageComponent',
    template: `
        <div class="admin-page page-container" id="page-projects">
            <div class="admin-header">
                <h2>📁 项目管理</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + 新建项目
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="搜索项目..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>项目名称</th>
                                <th>描述</th>
                                <th>状态</th>
                                <th>会话数</th>
                                <th>工作区</th>
                                <th>模型</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="project in projects" :key="project.id">
                                <td>{{ project.name }}</td>
                                <td>{{ project.description || '-' }}</td>
                                <td>
                                    <span class="status-badge" :class="project.status">
                                        {{ project.status === 'active' ? '活跃' : '停用' }}
                                    </span>
                                </td>
                                <td>{{ project.session_count || 0 }}</td>
                                <td>{{ getWorkspaceName(project.workspace_config_id) }}</td>
                                <td>{{ getModelName(project.model_config_id) }}</td>
                                <td>{{ formatDate(project.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(project)">编辑</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(project.id)">删除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!projects.length" class="empty-table">
                        暂无项目数据
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '编辑项目' : '新建项目' }}</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>项目名称 *</label>
                            <input type="text" v-model="formData.name" required placeholder="请输入项目名称">
                        </div>
                        <div class="form-group">
                            <label>描述</label>
                            <textarea v-model="formData.description" placeholder="请输入项目描述"></textarea>
                        </div>
                        <div class="form-group">
                            <label>关联工作区</label>
                            <select v-model="formData.workspace_config_id">
                                <option value="">不使用工作区</option>
                                <option v-for="w in workspaces" :key="w.id" :value="w.id">
                                    {{ w.name }}
                                </option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>关联模型</label>
                            <select v-model="formData.model_config_id">
                                <option value="">不使用模型</option>
                                <option v-for="m in models" :key="m.id" :value="m.id">
                                    {{ m.name }} ({{ getModelTypeName(m.type) }})
                                </option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>状态</label>
                            <select v-model="formData.status">
                                <option value="active">活跃</option>
                                <option value="inactive">停用</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">取消</button>
                        <button class="btn btn-primary" @click="handleSave">保存</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            projects: [],
            workspaces: [],
            models: [],
            searchQuery: '',
            showModal: false,
            currentProject: null,
            formData: {
                name: '',
                description: '',
                workspace_config_id: '',
                model_config_id: '',
                tool_config_ids: [],
                status: 'active'
            }
        };
    },
    computed: {
        isEdit() {
            return !!this.currentProject;
        }
    },
    async mounted() {
        console.log('[ProjectPage] Mounted, loading projects...');

        // 先注册事件监听器，避免错过数据加载事件
        EventBus.on('project:loaded', ({ projects }) => {
            console.log('[ProjectPage] project:loaded event received');
            console.log('[ProjectPage] Projects from event:', projects);
            console.log('[ProjectPage] First project from event:', projects[0]);
            console.log('[ProjectPage] First project.id from event:', projects[0]?.id);
            this.projects = projects;
        });
        EventBus.on('project:created', ({ project }) => {
            this.projects.push(project);
        });
        EventBus.on('project:updated', ({ project }) => {
            const index = this.projects.findIndex(p => p.id === project.id);
            if (index > -1) this.projects.splice(index, 1, project);
        });
        EventBus.on('project:deleted', ({ id }) => {
            this.projects = this.projects.filter(p => p.id !== id);
        });

        // 加载数据
        await this.loadProjects();
        await this.loadWorkspaces();
        await this.loadModels();

        // 如果 StateManager 中已有数据，也更新一下
        const stateProjects = StateManager.getState('projects');
        if (stateProjects && stateProjects.length > 0 && this.projects.length === 0) {
            console.log('[ProjectPage] Restoring from StateManager:', stateProjects);
            this.projects = stateProjects;
        }
    },
    methods: {
        async loadProjects() {
            await ProjectManager.getProjects({ search: this.searchQuery });
        },
        async loadWorkspaces() {
            try {
                const workspaces = await WorkspaceManager.getWorkspaces();
                this.workspaces = Array.isArray(workspaces) ? workspaces : [];
            } catch (error) {
                console.error('[ProjectPage] Failed to load workspaces:', error);
                this.workspaces = [];
            }
        },
        async loadModels() {
            try {
                const models = await ModelManager.getModels();
                this.models = Array.isArray(models) ? models : [];
            } catch (error) {
                console.error('[ProjectPage] Failed to load models:', error);
                this.models = [];
            }
        },
        handleSearch() {
            this.loadProjects();
        },
        showCreateModal() {
            this.currentProject = null;
            this.formData = { name: '', description: '', workspace_config_id: '', model_config_id: '', tool_config_ids: [], status: 'active' };
            this.showModal = true;
        },
        async handleEdit(project) {
            console.log('[ProjectPage] handleEdit called');
            console.log('[ProjectPage] Project to edit:', project);

            // 确保 currentProject 有正确的 id 字段
            this.currentProject = {
                ...project,
                id: project.id || project.project_id
            };

            // 先加载工作区和模型列表（等待数据加载完成）
            await Promise.all([
                this.loadWorkspaces(),
                this.loadModels()
            ]);

            console.log('[ProjectPage] workspaces loaded:', this.workspaces.length);
            console.log('[ProjectPage] models loaded:', this.models.length);
            console.log('[ProjectPage] project workspace_config_id:', project.workspace_config_id);
            console.log('[ProjectPage] project model_config_id:', project.model_config_id);

            // 后端使用 workspace_config_id 和 model_config_id
            this.formData = {
                name: project.name,
                description: project.description || '',
                workspace_config_id: project.workspace_config_id || '',
                model_config_id: project.model_config_id || '',
                tool_config_ids: project.tool_config_ids || [],
                status: project.status || 'active'
            };
            console.log('[ProjectPage] formData set:', this.formData);
            this.showModal = true;
        },
        async handleSave() {
            if (!this.formData.name) {
                alert('项目名称不能为空');
                return;
            }
            console.log('[ProjectPage] Saving project with data:', this.formData);
            if (this.currentProject) {
                await ProjectManager.updateProject(this.currentProject.id, this.formData);
            } else {
                await ProjectManager.createProject(this.formData);
            }
            this.closeModal();
        },
        async handleDelete(id) {
            if (confirm('确定要删除该项目吗？')) {
                await ProjectManager.deleteProject(id);
            }
        },
        closeModal() {
            this.showModal = false;
            this.currentProject = null;
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '-';
        },
        getWorkspaceName(workspaceId) {
            if (!workspaceId) return '-';
            const workspace = this.workspaces.find(w => w.id === workspaceId);
            return workspace ? workspace.name : '-';
        },
        getModelName(modelId) {
            if (!modelId) return '-';
            const model = this.models.find(m => m.id === modelId);
            return model ? model.name : '-';
        },
        getModelTypeName(type) {
            const types = { chat: '对话', tool: '工具', embed: '嵌入' };
            return types[type] || type;
        }
    }
};

window.ProjectPageComponent = ProjectPageComponent;
