/**
 * StoragePageComponent - 存储配置管理页面组件
 * 
 * 支持两个标签页：
 * 1. 实体存储配置 - 控制哪些实体类型需要持久化
 * 2. 事件存储配置 - 控制哪些事件类型需要存储到项目时间
 */
import { StorageManager } from '../services/StorageManager.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { EventBus } from '../infrastructure/EventBus.js';

export const StoragePageComponent = {
    name: 'StoragePageComponent',
    template: `
        <div class="admin-page page-container" id="page-storage">
            <div class="admin-header">
                <h2>💾 存储配置</h2>
            </div>
            
            <!-- 标签页切换 -->
            <div class="tabs">
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'entity' }"
                    @click="switchTab('entity')">
                    📦 实体存储配置
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'event' }"
                    @click="switchTab('event')">
                    ⚡ 事件存储配置
                </button>
            </div>
            
            <!-- 实体存储配置 -->
            <div v-if="activeTab === 'entity'" class="tab-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="搜索存储配置..."
                        @input="handleEntitySearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>实体类型</th>
                                <th>描述</th>
                                <th>持久化</th>
                                <th>更新时间</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="storage in filteredEntityStorages" :key="storage.entity_type">
                                <td><code>{{ storage.entity_type }}</code></td>
                                <td>{{ storage.description }}</td>
                                <td>
                                    <label class="switch">
                                        <input 
                                            type="checkbox" 
                                            :checked="storage.persist"
                                            @change="toggleEntityPersist(storage)">
                                        <span class="slider"></span>
                                    </label>
                                    <span class="switch-label">{{ storage.persist ? '是' : '否' }}</span>
                                </td>
                                <td>{{ formatDate(storage.updated_at) }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!filteredEntityStorages.length" class="empty-table">
                        暂无实体存储配置数据
                    </div>
                </div>
                <div class="batch-actions" v-if="pendingEntityChanges.length">
                    <span>待保存的更改: {{ pendingEntityChanges.length }} 项</span>
                    <button class="btn btn-primary" @click="saveEntityChanges">保存更改</button>
                    <button class="btn btn-secondary" @click="discardEntityChanges">放弃</button>
                </div>
            </div>
            
            <!-- 事件存储配置 -->
            <div v-if="activeTab === 'event'" class="tab-content">
                <div class="event-filter-bar">
                    <div class="filter-group">
                        <label>事件类型筛选:</label>
                        <select v-model="eventTypeFilter" @change="filterEvents">
                            <option value="">全部</option>
                            <option value="project">项目事件</option>
                            <option value="session">会话事件</option>
                            <option value="dialog">对话事件</option>
                            <option value="message">消息事件</option>
                            <option value="llm">LLM事件</option>
                            <option value="tool">工具事件</option>
                            <option value="task">任务事件</option>
                            <option value="round">轮次事件</option>
                            <option value="client">客户端事件</option>
                            <option value="system">系统事件</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>
                            <input type="checkbox" v-model="showOnlyDisabled" @change="filterEvents">
                            仅显示停用项
                        </label>
                    </div>
                    <div class="filter-actions">
                        <button class="btn btn-secondary" @click="resetEventStorage">重置为默认</button>
                        <button class="btn btn-primary" @click="toggleAllEvents">
                            {{ allEventsEnabled ? '禁用全部' : '启用全部' }}
                        </button>
                    </div>
                </div>
                
                <div class="data-table event-table">
                    <table>
                        <thead>
                            <tr>
                                <th>事件类型</th>
                                <th>描述</th>
                                <th>存储</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="(events, category) in groupedEvents" :key="category">
                                <tr class="category-header">
                                    <td colspan="3">
                                        <strong>{{ getCategoryName(category) }}</strong>
                                        <span class="category-count">
                                            ({{ events.filter(e => e.persist).length }}/{{ events.length }})
                                        </span>
                                    </td>
                                </tr>
                                <tr v-for="event in events" :key="event.event_type" :class="{ 'disabled-row': !event.persist }">
                                    <td><code>{{ event.event_type }}</code></td>
                                    <td>{{ event.description }}</td>
                                    <td>
                                        <label class="switch">
                                            <input 
                                                type="checkbox" 
                                                :checked="event.persist"
                                                @change="toggleEventPersist(event)">
                                            <span class="slider"></span>
                                        </label>
                                        <span class="switch-label">{{ event.persist ? '是' : '否' }}</span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                    <div v-if="!Object.keys(groupedEvents).length" class="empty-table">
                        暂无事件存储配置数据
                    </div>
                </div>
                
                <div class="batch-actions" v-if="pendingEventChanges.length">
                    <span>待保存的更改: {{ pendingEventChanges.length }} 项</span>
                    <button class="btn btn-primary" @click="saveEventChanges">保存更改</button>
                    <button class="btn btn-secondary" @click="discardEventChanges">放弃</button>
                </div>
            </div>
        </div>
    `,
    data() {
        return {
            activeTab: 'event',
            searchQuery: '',
            entityStorages: [],
            eventStorages: [],
            pendingEntityChanges: [],
            pendingEventChanges: [],
            eventTypeFilter: '',
            showOnlyDisabled: false,
        };
    },
    computed: {
        filteredEntityStorages() {
            if (!this.searchQuery) return this.entityStorages;
            const query = this.searchQuery.toLowerCase();
            return this.entityStorages.filter(s => 
                s.entity_type.toLowerCase().includes(query) ||
                (s.description && s.description.toLowerCase().includes(query))
            );
        },
        filteredEvents() {
            let events = this.eventStorages;
            
            if (this.eventTypeFilter) {
                events = events.filter(e => e.event_type.startsWith(this.eventTypeFilter));
            }
            
            if (this.showOnlyDisabled) {
                events = events.filter(e => !e.persist);
            }
            
            return events;
        },
        groupedEvents() {
            const groups = {};
            for (const event of this.filteredEvents) {
                const parts = event.event_type.split('.');
                const category = parts[0];
                if (!groups[category]) {
                    groups[category] = [];
                }
                groups[category].push(event);
            }
            return groups;
        },
        allEventsEnabled() {
            return this.eventStorages.length > 0 && 
                   this.eventStorages.every(e => e.persist);
        }
    },
    async mounted() {
        console.log('[StoragePage] Mounted');
        
        // 注册事件监听器
        EventBus.on('storage:loaded', ({ storages }) => {
            console.log('[StoragePage] Entity storages loaded:', storages);
            this.entityStorages = storages;
        });
        EventBus.on('storage:error', ({ error }) => {
            console.error('[StoragePage] Storage error:', error);
        });
        
        EventBus.on('eventStorage:loaded', ({ eventStorages }) => {
            console.log('[StoragePage] Event storages loaded:', eventStorages);
            this.eventStorages = eventStorages;
        });
        EventBus.on('eventStorage:updated', () => {
            this.loadEventStorages();
        });
        EventBus.on('eventStorage:batch_updated', () => {
            this.loadEventStorages();
            this.pendingEventChanges = [];
        });
        EventBus.on('eventStorage:reset', () => {
            this.loadEventStorages();
            this.pendingEventChanges = [];
        });
        EventBus.on('eventStorage:error', ({ error }) => {
            console.error('[StoragePage] Event storage error:', error);
        });
        
        // 加载数据
        this.loadEntityStorages();
        this.loadEventStorages();
    },
    methods: {
        switchTab(tab) {
            this.activeTab = tab;
        },
        
        // 实体存储配置方法
        async loadEntityStorages() {
            await StorageManager.getStorages();
        },
        handleEntitySearch() {
            // 搜索是响应式的，不需要额外处理
        },
        toggleEntityPersist(storage) {
            const newValue = !storage.persist;
            // 更新本地状态
            storage.persist = newValue;
            // 记录待保存的更改
            const existingIndex = this.pendingEntityChanges.findIndex(
                c => c.entity_type === storage.entity_type
            );
            if (existingIndex >= 0) {
                this.pendingEntityChanges.splice(existingIndex, 1);
            }
            this.pendingEntityChanges.push({
                entity_type: storage.entity_type,
                persist: newValue
            });
        },
        async saveEntityChanges() {
            try {
                await StorageManager.batchUpdateStorage(this.pendingEntityChanges);
                this.pendingEntityChanges = [];
                await this.loadEntityStorages();
            } catch (error) {
                console.error('保存失败:', error);
            }
        },
        discardEntityChanges() {
            this.pendingEntityChanges = [];
            this.loadEntityStorages();
        },
        
        // 事件存储配置方法
        async loadEventStorages() {
            await StorageManager.getEventStorages();
        },
        filterEvents() {
            // 筛选是响应式的
        },
        toggleEventPersist(event) {
            const newValue = !event.persist;
            // 更新本地状态
            event.persist = newValue;
            // 记录待保存的更改
            const existingIndex = this.pendingEventChanges.findIndex(
                c => c.event_type === event.event_type
            );
            if (existingIndex >= 0) {
                this.pendingEventChanges.splice(existingIndex, 1);
            }
            this.pendingEventChanges.push({
                event_type: event.event_type,
                persist: newValue
            });
        },
        async saveEventChanges() {
            try {
                await StorageManager.batchUpdateEventStorage(this.pendingEventChanges);
                this.pendingEventChanges = [];
                await this.loadEventStorages();
            } catch (error) {
                console.error('保存失败:', error);
            }
        },
        discardEventChanges() {
            this.pendingEventChanges = [];
            this.loadEventStorages();
        },
        async resetEventStorage() {
            if (confirm('确定要重置所有事件存储配置为默认值吗？')) {
                await StorageManager.resetEventStorage();
            }
        },
        toggleAllEvents() {
            const newValue = !this.allEventsEnabled;
            for (const event of this.eventStorages) {
                if (event.persist !== newValue) {
                    event.persist = newValue;
                    const existingIndex = this.pendingEventChanges.findIndex(
                        c => c.event_type === event.event_type
                    );
                    if (existingIndex >= 0) {
                        this.pendingEventChanges.splice(existingIndex, 1);
                    }
                    this.pendingEventChanges.push({
                        event_type: event.event_type,
                        persist: newValue
                    });
                }
            }
        },
        getCategoryName(category) {
            const names = {
                'project': '项目事件',
                'session': '会话事件',
                'dialog': '对话事件',
                'message': '消息事件',
                'llm': 'LLM事件',
                'tool': '工具事件',
                'task': '任务事件',
                'task_group': '任务组事件',
                'round': '轮次事件',
                'client': '客户端事件',
                'system': '系统事件',
                'history': '历史回放事件'
            };
            return names[category] || category;
        },
        formatDate(dateStr) {
            return dateStr ? new Date(dateStr).toLocaleDateString() : '-';
        }
    }
};

window.StoragePageComponent = StoragePageComponent;
