/**
 * PromptPageComponent - 提示词管理页面组件
 */
import { PromptManager } from '../services/PromptManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const PromptPageComponent = {
    name: 'PromptPageComponent',
    template: `
        <div class="admin-page page-container" id="page-prompts">
            <div class="admin-header">
                <h2>📝 提示词管理</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + 新建提示词
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="搜索提示词..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>提示词名称</th>
                                <th>分类</th>
                                <th>变量</th>
                                <th>状态</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="prompt in prompts" :key="prompt.prompt_id">
                                <td>{{ prompt.name }}</td>
                                <td>{{ getCategoryLabel(prompt.category) }}</td>
                                <td>{{ prompt.variables?.join(', ') || '-' }}</td>
                                <td>
                                    <span class="status-badge" :class="prompt.is_active ? 'active' : 'disabled'">
                                        {{ prompt.is_active ? '启用' : '停用' }}
                                    </span>
                                </td>
                                <td>{{ formatDate(prompt.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(prompt)">编辑</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(prompt.prompt_id)">删除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!prompts.length" class="empty-table">
                        暂无提示词数据
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '编辑提示词' : '新建提示词' }}</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>提示词名称 *</label>
                            <input type="text" v-model="formData.name" required placeholder="请输入提示词名称">
                        </div>
                        <div class="form-group">
                            <label>分类 *</label>
                            <select v-model="formData.category" required>
                                <option value="" disabled>请选择分类</option>
                                <option value="system_prompt">system_prompt (系统提示词)</option>
                                <option value="user_prompt">user_prompt (用户提示词)</option>
                                <option value="assistant_prompt">assistant_prompt (助手提示词)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>提示词内容 *</label>
                            <textarea v-model="formData.content" required rows="8" placeholder="提示词内容，支持 {{variable}} 格式的变量"></textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" v-model="formData.is_active">
                                启用状态
                            </label>
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
            prompts: [],
            searchQuery: '',
            showModal: false,
            currentPrompt: null,
            formData: {
                name: '',
                category: '',
                content: '',
                is_active: true
            },
            categories: [
                { value: 'system_prompt', label: 'system_prompt (系统提示词)' },
                { value: 'user_prompt', label: 'user_prompt (用户提示词)' },
                { value: 'assistant_prompt', label: 'assistant_prompt (助手提示词)' }
            ]
        };
    },
    computed: {
        isEdit() {
            return !!this.currentPrompt;
        }
    },
    async mounted() {
        console.log('[PromptPage] Mounted, loading prompts...');

        EventBus.on('prompt:loaded', ({ prompts }) => {
            console.log('[PromptPage] Prompts loaded:', prompts);
            this.prompts = prompts;
        });
        EventBus.on('prompt:created', ({ prompt }) => {
            this.prompts.push(prompt);
        });
        EventBus.on('prompt:updated', ({ prompt }) => {
            const index = this.prompts.findIndex(p => p.prompt_id === prompt.prompt_id);
            if (index > -1) this.prompts.splice(index, 1, prompt);
        });
        EventBus.on('prompt:deleted', ({ prompt_id }) => {
            this.prompts = this.prompts.filter(p => p.prompt_id !== prompt_id);
        });

        await this.loadPrompts();

        const statePrompts = StateManager.getState('prompts');
        if (statePrompts && statePrompts.length > 0 && this.prompts.length === 0) {
            console.log('[PromptPage] Restoring from StateManager:', statePrompts);
            this.prompts = statePrompts;
        }
    },
    methods: {
        getCategoryLabel(category) {
            const cat = this.categories.find(c => c.value === category);
            return cat ? cat.label : category || '-';
        },
        async loadPrompts() {
            await PromptManager.getPrompts({ search: this.searchQuery });
        },
        handleSearch() {
            this.loadPrompts();
        },
        showCreateModal() {
            this.currentPrompt = null;
            this.formData = { 
                name: '', 
                category: '', 
                content: '',
                is_active: true
            };
            this.showModal = true;
        },
        handleEdit(prompt) {
            this.currentPrompt = prompt;
            this.formData = { 
                name: prompt.name || '',
                category: prompt.category || '',
                content: prompt.content || '',
                is_active: prompt.is_active || true
            };
            this.showModal = true;
        },
        async handleSave() {
            if (!this.formData.name) {
                alert('提示词名称不能为空');
                return;
            }
            if (!this.formData.category) {
                alert('请选择提示词分类');
                return;
            }
            if (!this.formData.content) {
                alert('提示词内容不能为空');
                return;
            }
            if (this.currentPrompt) {
                await PromptManager.updatePrompt(this.currentPrompt.prompt_id, this.formData);
            } else {
                await PromptManager.createPrompt(this.formData);
            }
            this.closeModal();
        },
        async handleDelete(prompt_id) {
            if (confirm('确定要删除该提示词吗？')) {
                await PromptManager.deletePrompt(prompt_id);
            }
        },
        closeModal() {
            this.showModal = false;
            this.currentPrompt = null;
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '-';
        }
    }
};

window.PromptPageComponent = PromptPageComponent;