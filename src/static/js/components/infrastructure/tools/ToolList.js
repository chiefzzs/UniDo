/**
 * ToolList - 工具列表组件
 * 迭代二：ST-v0.2-03
 * 
 * 功能：
 * - 自动加载工具列表
 * - 显示工具名称、描述、状态
 * - 显示工具总数
 */

const ToolList = {
    name: 'ToolList',
    
    data() {
        return {
            tools: [],
            totalCount: 0,
            loading: false,
            selectedTool: null,
            filterEnabled: true
        };
    },
    
    created() {
        this.fetchTools();
    },
    
    methods: {
        async fetchTools() {
            this.loading = true;
            try {
                const response = await fetch('/api/tools');
                const data = await response.json();
                
                this.tools = data.tools || [];
                this.totalCount = data.total || this.tools.length;
                this.$emit('tools-loaded', { tools: this.tools, total: this.totalCount });
            } catch (e) {
                console.error('获取工具列表失败:', e);
                this.$emit('error', { message: '获取工具列表失败' });
            } finally {
                this.loading = false;
            }
        },
        
        selectTool(tool) {
            this.selectedTool = tool;
            this.$emit('tool-selected', tool);
        },
        
        getToolIcon(tool) {
            // 根据工具名称返回图标
            const name = tool.name?.toLowerCase() || '';
            if (name.includes('search')) return '🔍';
            if (name.includes('read') || name.includes('file')) return '📄';
            if (name.includes('write') || name.includes('save')) return '💾';
            if (name.includes('delete') || name.includes('remove')) return '🗑️';
            if (name.includes('run') || name.includes('execute')) return '▶️';
            return '🔧';
        },
        
        getStatusClass(tool) {
            return {
                'tool-enabled': tool.enabled !== false,
                'tool-disabled': tool.enabled === false
            };
        }
    },
    
    computed: {
        filteredTools() {
            if (this.filterEnabled) {
                return this.tools.filter(tool => tool.enabled !== false);
            }
            return this.tools;
        }
    },
    
    template: `
        <div class="tool-list">
            <div class="panel-header">
                <span class="panel-title">工具列表</span>
                <span class="tool-count">{{ filteredTools.length }} / {{ totalCount }}</span>
            </div>
            
            <div class="panel-content">
                <div class="loading-state" v-if="loading">
                    <span class="spinner"></span>
                    <span>加载中...</span>
                </div>
                
                <div class="tool-filter" v-if="!loading">
                    <label class="filter-checkbox">
                        <input type="checkbox" v-model="filterEnabled">
                        <span>仅显示启用</span>
                    </label>
                    <button class="refresh-btn" @click="fetchTools">🔄</button>
                </div>
                
                <div class="tools-container" v-if="!loading">
                    <div 
                        class="tool-item"
                        :class="getStatusClass(tool)"
                        v-for="tool in filteredTools"
                        :key="tool.tool_id"
                        @click="selectTool(tool)">
                        <div class="tool-icon">{{ getToolIcon(tool) }}</div>
                        <div class="tool-info">
                            <div class="tool-name">{{ tool.name }}</div>
                            <div class="tool-description">{{ tool.description || '无描述' }}</div>
                        </div>
                        <div class="tool-status">
                            <span class="status-dot" :class="{ active: tool.enabled !== false }"></span>
                        </div>
                    </div>
                    
                    <div class="empty-state" v-if="filteredTools.length === 0">
                        <span>暂无工具</span>
                    </div>
                </div>
            </div>
            
            <div class="tool-detail" v-if="selectedTool">
                <div class="detail-header">
                    <span>{{ selectedTool.name }}</span>
                    <button class="close-btn" @click="selectedTool = null">×</button>
                </div>
                <div class="detail-content">
                    <div class="detail-row">
                        <span class="detail-label">ID:</span>
                        <span class="detail-value">{{ selectedTool.tool_id }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">描述:</span>
                        <span class="detail-value">{{ selectedTool.description || '无' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">状态:</span>
                        <span class="detail-value">{{ selectedTool.enabled !== false ? '启用' : '禁用' }}</span>
                    </div>
                    <div class="detail-row" v-if="selectedTool.parameters?.length">
                        <span class="detail-label">参数:</span>
                        <div class="params-list">
                            <div v-for="param in selectedTool.parameters" :key="param.name" class="param-item">
                                <span class="param-name">{{ param.name }}</span>
                                <span class="param-type">{{ param.type }}</span>
                                <span class="param-required" v-if="param.required">*</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

// 注册为全局组件
if (window.Vue) {
    Vue.component('tool-list', ToolList);
}

export default ToolList;
