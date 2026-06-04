/**
 * ToolPageComponent - 工具管理页面组件
 */
import { ToolManager } from '../services/ToolManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const ToolPageComponent = {
    name: 'ToolPageComponent',
    template: `
        <div class="admin-page page-container" id="page-tools">
            <div class="admin-header">
                <h2>🔧 工具管理</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + 新建工具
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="搜索工具..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>工具名称</th>
                                <th>工具类型</th>
                                <th>支持操作系统</th>
                                <th>支持终端</th>
                                <th>描述</th>
                                <th>状态</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="tool in tools" :key="tool.tool_id || tool.id">
                                <td>{{ tool.tool_name || tool.name || '-' }}</td>
                                <td>{{ getToolTypeName(tool.category || tool.type) || '-' }}</td>
                                <td>{{ getPlatformLabels(tool.supported_os) || '-' }}</td>
                                <td>{{ getTerminalLabels(tool.supported_terminals) || '-' }}</td>
                                <td>{{ tool.description || '-' }}</td>
                                <td>
                                    <span class="status-badge" :class="getToolStatus(tool)">
                                        {{ getToolStatus(tool) === 'active' ? '启用' : '停用' }}
                                    </span>
                                </td>
                                <td>{{ formatDate(tool.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(tool)">编辑</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(tool.tool_id || tool.id)">删除</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!tools.length" class="empty-table">
                        暂无工具数据
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '编辑工具' : '新建工具' }}</h3>
                        <button class="modal-close" @click="closeModal">×</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>工具名称 *</label>
                            <input type="text" v-model="formData.name" required placeholder="请输入工具名称">
                        </div>
                        <div class="form-group">
                            <label>工具类型</label>
                            <select v-model="formData.type">
                                <option value="websearch">网页搜索</option>
                                <option value="file">文件操作</option>
                                <option value="api">API调用</option>
                                <option value="calculator">计算器</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>支持操作系统</label>
                            <div class="checkbox-group">
                                <label v-for="os in osOptions" :key="os.value" class="checkbox-label">
                                    <input type="checkbox" :value="os.value" v-model="formData.supported_os">
                                    {{ os.label }}
                                </label>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>支持终端</label>
                            <div class="checkbox-group">
                                <label v-for="terminal in terminalOptions" :key="terminal.value" class="checkbox-label">
                                    <input type="checkbox" :value="terminal.value" v-model="formData.supported_terminals">
                                    {{ terminal.label }}
                                </label>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>描述</label>
                            <textarea v-model="formData.description" placeholder="工具描述"></textarea>
                        </div>
                        <div class="form-group">
                            <label>配置参数（JSON）</label>
                            <textarea v-model="formData.config" placeholder='{"key": "value"}'></textarea>
                        </div>
                        <div class="form-group">
                            <label>状态</label>
                            <select v-model="formData.status">
                                <option value="active">启用</option>
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
            tools: [],
            searchQuery: '',
            showModal: false,
            currentTool: null,
            osOptions: [
                { value: 'windows', label: 'Windows' },
                { value: 'linux', label: 'Linux' },
                { value: 'macos', label: 'macOS' }
            ],
            terminalOptions: [
                { value: 'powershell', label: 'PowerShell' },
                { value: 'cmd', label: 'CMD' },
                { value: 'bash', label: 'Bash' },
                { value: 'zsh', label: 'Zsh' }
            ],
            formData: {
                name: '',
                type: 'websearch',
                supported_os: ['windows', 'linux', 'macos'],
                supported_terminals: ['powershell', 'cmd', 'bash', 'zsh'],
                description: '',
                config: '{}',
                status: 'active'
            }
        };
    },
    computed: {
        isEdit() {
            return !!this.currentTool;
        }
    },
    async mounted() {
        console.log('[ToolPage] Mounted, loading tools...');

        // 先注册事件监听器，避免错过数据加载事件
        EventBus.on('tool:loaded', ({ tools }) => {
            console.log('[ToolPage] Tools loaded:', tools);
            this.tools = tools;
        });
        EventBus.on('tool:created', ({ tool }) => {
            this.tools.push(tool);
        });
        EventBus.on('tool:updated', ({ tool }) => {
            const index = this.tools.findIndex(t => t.id === tool.id);
            if (index > -1) this.tools.splice(index, 1, tool);
        });
        EventBus.on('tool:deleted', ({ id }) => {
            this.tools = this.tools.filter(t => t.id !== id);
        });

        // 加载数据
        await this.loadTools();

        // 如果 StateManager 中已有数据，也更新一下
        const stateTools = StateManager.getState('tools');
        if (stateTools && stateTools.length > 0 && this.tools.length === 0) {
            console.log('[ToolPage] Restoring from StateManager:', stateTools);
            this.tools = stateTools;
        }
    },
    methods: {
        async loadTools() {
            await ToolManager.getTools({ search: this.searchQuery });
        },
        handleSearch() {
            this.loadTools();
        },
        getToolTypeName(type) {
            const types = {
                websearch: '网页搜索',
                file: '文件操作',
                api: 'API调用',
                calculator: '计算器'
            };
            return types[type] || type;
        },
        getPlatformLabels(osArray) {
            if (!osArray || !Array.isArray(osArray) || osArray.length === 0) {
                return '全部平台';
            }
            return osArray.map(os => {
                const option = this.osOptions.find(o => o.value === os);
                return option ? option.label : os;
            }).join(', ');
        },
        getTerminalLabels(terminalArray) {
            if (!terminalArray || !Array.isArray(terminalArray) || terminalArray.length === 0) {
                return '全部终端';
            }
            return terminalArray.map(terminal => {
                const option = this.terminalOptions.find(t => t.value === terminal);
                return option ? option.label : terminal;
            }).join(', ');
        },
        getToolStatus(tool) {
            // 后端返回的是 is_active 布尔值，需要转换为 status 字符串
            if (tool.status) {
                return tool.status;
            } else if (tool.is_active !== undefined) {
                return tool.is_active ? 'active' : 'inactive';
            }
            return 'inactive';
        },
        showCreateModal() {
            this.currentTool = null;
            this.formData = { 
                name: '', 
                type: 'websearch', 
                supported_os: ['windows', 'linux', 'macos'],
                supported_terminals: ['powershell', 'cmd', 'bash', 'zsh'],
                description: '', 
                config: '{}', 
                status: 'active' 
            };
            this.showModal = true;
        },
        handleEdit(tool) {
            this.currentTool = tool;
            this.formData = { 
                ...tool,
                name: tool.tool_name || tool.name || '',
                type: tool.category || tool.type || 'websearch',
                supported_os: tool.supported_os || ['windows', 'linux', 'macos'],
                supported_terminals: tool.supported_terminals || ['powershell', 'cmd', 'bash', 'zsh'],
                status: this.getToolStatus(tool)
            };
            this.showModal = true;
        },
        async handleSave() {
            if (!this.formData.name) {
                alert('工具名称不能为空');
                return;
            }
            if (this.currentTool) {
                await ToolManager.updateTool(this.currentTool.id, this.formData);
            } else {
                await ToolManager.createTool(this.formData);
            }
            this.closeModal();
        },
        async handleDelete(id) {
            if (confirm('确定要删除该工具吗？')) {
                await ToolManager.deleteTool(id);
            }
        },
        closeModal() {
            this.showModal = false;
            this.currentTool = null;
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '-';
        }
    }
};

window.ToolPageComponent = ToolPageComponent;
