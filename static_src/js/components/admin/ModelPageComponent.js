/**
 * ModelPageComponent - 模型管理页面组件
 */
import { ModelManager } from '../services/ModelManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ModelPageComponent = {
    name: 'ModelPageComponent',
    template: `
        <div class="admin-page page-container" id="page-models">
            <div class="admin-header">
                <h2>🤖 模型管理</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + 新建模型
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="搜索模型..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>模型名称</th>
                                <th>模型类型</th>
                                <th>API地址</th>
                                <th>状态</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="model in models" :key="model.id">
                                <td>{{ model.name }}</td>
                                <td>{{ getModelTypeName(model.type) }}</td>
                                <td>{{ model.apiUrl }}</td>
                                <td>
                                    <span class="status-badge" :class="model.status">
                                        {{ model.status === 'active' ? '启用' : '停用' }}
                                    </span>
                                </td>
                                <td>{{ formatDate(model.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(model)">编辑</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(model.id)">删除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!models.length" class="empty-table">
                        暂无模型数据
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '编辑模型' : '新建模型' }}</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>模型名称 *</label>
                            <input type="text" v-model="formData.name" required placeholder="请输入模型名称">
                        </div>
                        <div class="form-group">
                            <label>模型类型</label>
                            <select v-model="formData.api_type">
                                <option value="chat">对话模型</option>
                                <option value="embedding">嵌入模型</option>
                                <option value="image">图像模型</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>API地址</label>
                            <input type="text" v-model="formData.api_address" placeholder="https://api.example.com/v1">
                        </div>
                        <div class="form-group">
                            <label>API密钥</label>
                            <input type="password" v-model="formData.api_key" placeholder="API密钥">
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
            models: [],
            searchQuery: '',
            showModal: false,
            currentModel: null,
            formData: {
                name: '',
                type: 'chat',
                apiUrl: '',
                apiKey: '',
                status: 'active'
            }
        };
    },
    computed: {
        isEdit() {
            return !!this.currentModel;
        }
    },
    async mounted() {
        console.log('[ModelPage] Mounted, loading models...');

        // 先注册事件监听器，避免错过数据加载事件
        EventBus.on('model:loaded', ({ models }) => {
            console.log('[ModelPage] Models loaded:', models);
            this.models = models;
        });
        EventBus.on('model:created', ({ model }) => {
            this.models.push(model);
        });
        EventBus.on('model:updated', ({ model }) => {
            const index = this.models.findIndex(m => m.id === model.id);
            if (index > -1) this.models.splice(index, 1, model);
        });
        EventBus.on('model:deleted', ({ id }) => {
            this.models = this.models.filter(m => m.id !== id);
        });

        // 加载数据
        await this.loadModels();

        // 如果 StateManager 中已有数据，也更新一下
        const stateModels = StateManager.getState('models');
        if (stateModels && stateModels.length > 0 && this.models.length === 0) {
            console.log('[ModelPage] Restoring from StateManager:', stateModels);
            this.models = stateModels;
        }
    },
    methods: {
        async loadModels() {
            await ModelManager.getModels({ search: this.searchQuery });
        },
        handleSearch() {
            this.loadModels();
        },
        getModelTypeName(type) {
            const types = {
                chat: '对话模型',
                embedding: '嵌入模型',
                image: '图像模型'
            };
            return types[type] || type;
        },
        showCreateModal() {
            this.currentModel = null;
            this.formData = { 
                name: '', 
                model_name: '',
                api_type: 'chat', 
                api_address: '', 
                api_key: '',
                parameters: {}
            };
            this.showModal = true;
        },
        handleEdit(model) {
            this.currentModel = model;
            this.formData = { 
                name: model.name || '',
                model_name: model.model_name || '',
                api_type: model.api_type || 'chat',
                api_address: model.api_address || '',
                api_key: model.api_key || '',
                parameters: model.parameters || {}
            };
            this.showModal = true;
        },
        async handleSave() {
            if (!this.formData.name) {
                alert('模型名称不能为空');
                return;
            }
            if (this.currentModel) {
                await ModelManager.updateModel(this.currentModel.id, this.formData);
            } else {
                await ModelManager.createModel(this.formData);
            }
            this.closeModal();
        },
        async handleDelete(id) {
            if (confirm('确定要删除该模型吗？')) {
                await ModelManager.deleteModel(id);
            }
        },
        closeModal() {
            this.showModal = false;
            this.currentModel = null;
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '-';
        }
    }
};

window.ModelPageComponent = ModelPageComponent;
