/**
 * WorkspacePageComponent - 工作区管理页面组件
 */
import { WorkspaceManager } from '../services/WorkspaceManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const WorkspacePageComponent = {
    name: 'WorkspacePageComponent',
    template: `
        <div class="admin-page page-container" id="page-workspaces">
            <div class="admin-header">
                <h2>📂 工作区管理</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + 新建工作区
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="搜索工作区..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>工作区名称</th>
                                <th>根路径</th>
                                <th>类型</th>
                                <th>编码</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="workspace in workspaces" :key="workspace.id">
                                <td>{{ workspace.name }}</td>
                                <td>{{ workspace.root_path }}</td>
                                <td>{{ workspace.type === 'local' ? '本地' : '远程' }}</td>
                                <td>{{ workspace.encoding }}</td>
                                <td>{{ formatDate(workspace.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(workspace)">编辑</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(workspace.id)">删除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!workspaces.length" class="empty-table">
                        暂无工作区数据
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '编辑工作区' : '新建工作区' }}</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>工作区名称 *</label>
                            <input type="text" v-model="formData.name" required placeholder="请输入工作区名称">
                        </div>
                        <div class="form-group">
                            <label>根路径</label>
                            <input type="text" v-model="formData.root_path" placeholder="工作区根路径">
                        </div>
                        <div class="form-group">
                            <label>类型</label>
                            <select v-model="formData.type">
                                <option value="local">本地</option>
                                <option value="remote">远程</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>编码</label>
                            <input type="text" v-model="formData.encoding" placeholder="utf-8">
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
            workspaces: [],
            searchQuery: '',
            showModal: false,
            currentWorkspace: null,
            formData: {
                name: '',
                root_path: '',
                type: 'local',
                encoding: 'utf-8',
                excluded_patterns: []
            }
        };
    },
    computed: {
        isEdit() {
            return !!this.currentWorkspace;
        }
    },
    async mounted() {
        console.log('[WorkspacePage] Mounted, loading workspaces...');

        // 先注册事件监听器，避免错过数据加载事件
        EventBus.on('workspace:loaded', ({ workspaces }) => {
            console.log('[WorkspacePage] Workspaces loaded:', workspaces);
            this.workspaces = workspaces;
        });
        EventBus.on('workspace:created', ({ workspace }) => {
            this.workspaces.push(workspace);
        });
        EventBus.on('workspace:updated', ({ workspace }) => {
            const index = this.workspaces.findIndex(w => w.id === workspace.id);
            if (index > -1) this.workspaces.splice(index, 1, workspace);
        });
        EventBus.on('workspace:deleted', ({ id }) => {
            this.workspaces = this.workspaces.filter(w => w.id !== id);
        });

        // 加载数据
        await this.loadWorkspaces();
        await this.loadProjects();

        // 如果 StateManager 中已有数据，也更新一下
        const stateWorkspaces = StateManager.getState('workspaces');
        if (stateWorkspaces && stateWorkspaces.length > 0 && this.workspaces.length === 0) {
            console.log('[WorkspacePage] Restoring from StateManager:', stateWorkspaces);
            this.workspaces = stateWorkspaces;
        }
    },
    methods: {
        async loadWorkspaces() {
            await WorkspaceManager.getWorkspaces({ search: this.searchQuery });
        },
        handleSearch() {
            this.loadWorkspaces();
        },
        showCreateModal() {
            this.currentWorkspace = null;
            this.formData = { 
                name: '', 
                root_path: '', 
                type: 'local', 
                encoding: 'utf-8',
                excluded_patterns: []
            };
            this.showModal = true;
        },
        handleEdit(workspace) {
            this.currentWorkspace = workspace;
            this.formData = { 
                name: workspace.name || '',
                root_path: workspace.root_path || '',
                type: workspace.type || 'local',
                encoding: workspace.encoding || 'utf-8',
                excluded_patterns: workspace.excluded_patterns || []
            };
            this.showModal = true;
        },
        async handleSave() {
            if (!this.formData.name) {
                alert('工作区名称不能为空');
                return;
            }
            if (this.currentWorkspace) {
                await WorkspaceManager.updateWorkspace(this.currentWorkspace.id, this.formData);
            } else {
                await WorkspaceManager.createWorkspace(this.formData);
            }
            this.closeModal();
        },
        async handleDelete(id) {
            if (confirm('确定要删除该工作区吗？')) {
                await WorkspaceManager.deleteWorkspace(id);
            }
        },
        closeModal() {
            this.showModal = false;
            this.currentWorkspace = null;
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '-';
        }
    }
};

window.WorkspacePageComponent = WorkspacePageComponent;
