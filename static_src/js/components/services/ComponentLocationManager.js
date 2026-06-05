import { StateManager } from '../infrastructure/StateManager.js';

export const ComponentLocationManager = {
    // 存储所有组件的位置记录
    locationRecords: new Map(),
    
    // 存储注册的定位策略
    locationStrategies: new Map(),

    /**
     * 初始化（注册默认策略）
     */
    init() {
        this.registerDefaultStrategies();
    },

    /**
     * 注册默认的组件定位策略
     */
    registerDefaultStrategies() {
        // 用户消息组件定位策略
        this.registerStrategy('UserMessage', {
            findParent: (data) => {
                const sessionId = data.sessionId || StateManager.getState('currentSessionId');
                return {
                    parentType: 'ChatContainer',
                    parentId: `chat-container-${sessionId}`,
                    selectionCriteria: { sessionId }
                };
            }
        });

        // 助手消息组件定位策略
        this.registerStrategy('AssistantMessage', {
            findParent: (data) => {
                const sessionId = data.sessionId || StateManager.getState('currentSessionId');
                return {
                    parentType: 'ChatContainer',
                    parentId: `chat-container-${sessionId}`,
                    selectionCriteria: { sessionId }
                };
            }
        });

        // 响应块组件定位策略 - 根据 dialogId 查找父助手消息
        this.registerStrategy('ResponseBlock', {
            findParent: (data) => {
                const { dialogId, messageId } = data;
                let parentId = null;
                let parentType = 'AssistantMessage';

                if (messageId) {
                    parentId = messageId;
                } else if (dialogId) {
                    // 根据 dialogId 查找对应的助手消息
                    const messages = StateManager.getState('messages') || [];
                    const assistantMsg = messages.find(m => 
                        m.role === 'assistant' && m.dialogId === dialogId
                    );
                    if (assistantMsg) {
                        parentId = assistantMsg.id;
                    }
                }

                return {
                    parentType,
                    parentId,
                    selectionCriteria: { dialogId, messageId }
                };
            }
        });

        // 工具卡组件定位策略 - 根据 dialogId 查找父响应块
        this.registerStrategy('ToolCard', {
            findParent: (data) => {
                const { dialogId, callId, responseId } = data;
                let parentId = null;
                let parentType = 'ResponseBlock';

                if (responseId) {
                    parentId = responseId;
                } else if (dialogId) {
                    // 根据 dialogId 查找对应的响应块
                    const blocks = StateManager.state.responseBlocks;
                    for (const [blockId, block] of blocks.entries()) {
                        if (block.dialogId === dialogId) {
                            parentId = blockId;
                            break;
                        }
                    }
                }

                return {
                    parentType,
                    parentId,
                    selectionCriteria: { dialogId, callId, responseId }
                };
            }
        });

        // 文本块组件定位策略
        this.registerStrategy('TextBlock', {
            findParent: (data) => {
                const { responseId } = data;
                return {
                    parentType: 'ResponseBlock',
                    parentId: responseId,
                    selectionCriteria: { responseId }
                };
            }
        });

        // 思考块组件定位策略
        this.registerStrategy('ThinkBlock', {
            findParent: (data) => {
                const { responseId } = data;
                return {
                    parentType: 'ResponseBlock',
                    parentId: responseId,
                    selectionCriteria: { responseId }
                };
            }
        });

        // 推理块组件定位策略
        this.registerStrategy('ReasonBlock', {
            findParent: (data) => {
                const { responseId } = data;
                return {
                    parentType: 'ResponseBlock',
                    parentId: responseId,
                    selectionCriteria: { responseId }
                };
            }
        });
    },

    /**
     * 注册自定义定位策略
     * @param {string} componentType - 组件类型
     * @param {object} strategy - 定位策略对象
     */
    registerStrategy(componentType, strategy) {
        this.locationStrategies.set(componentType, strategy);
        console.log(`[ComponentLocationManager] Registered strategy for ${componentType}`);
    },

    /**
     * 获取组件的定位信息
     * @param {string} componentType - 组件类型
     * @param {object} data - 组件数据
     * @returns {object} - 定位信息
     */
    getLocation(componentType, data) {
        const strategy = this.locationStrategies.get(componentType);
        if (!strategy) {
            console.warn(`[ComponentLocationManager] No strategy found for ${componentType}`);
            return null;
        }

        try {
            const location = strategy.findParent(data);
            return location;
        } catch (error) {
            console.error(`[ComponentLocationManager] Error getting location for ${componentType}:`, error);
            return null;
        }
    },

    /**
     * 记录组件创建位置
     * @param {string} componentId - 组件唯一ID
     * @param {string} componentType - 组件类型
     * @param {object} data - 创建组件时使用的数据
     * @param {object} options - 选项
     * @param {boolean} options.abandoned - 是否被抛弃
     * @param {string} options.abandonReason - 抛弃原因
     */
    recordCreation(componentId, componentType, data, options = {}) {
        const { abandoned = false, abandonReason = null } = options;
        const location = this.getLocation(componentType, data);

        const record = {
            componentId,
            componentType,
            parentType: location?.parentType || null,
            parentId: location?.parentId || null,
            selectionCriteria: location?.selectionCriteria || {},
            creationData: { ...data },
            timestamp: Date.now(),
            isValid: !!location?.parentId,
            abandoned,
            abandonReason
        };

        this.locationRecords.set(componentId, record);

        if (abandoned) {
            console.log(`%c[ComponentLocationManager] Component ABANDONED:`, 'color: #FF9800');
            console.log(`%c  ID: ${componentId}`, 'color: #FF9800');
            console.log(`%c  Type: ${componentType}`, 'color: #FF9800');
            console.log(`%c  Reason: ${abandonReason || 'Unknown'}`, 'color: #FF9800');
            console.log(`%c  Criteria: ${JSON.stringify(data)}`, 'color: #FF9800');
        } else {
            console.log(`%c[ComponentLocationManager] Recorded component creation:`, 'color: #4CAF50');
            console.log(`%c  ID: ${componentId}`, 'color: #4CAF50');
            console.log(`%c  Type: ${componentType}`, 'color: #4CAF50');
            console.log(`%c  Parent: ${location?.parentType || 'Unknown'} (${location?.parentId || 'N/A'})`, 'color: #4CAF50');
            console.log(`%c  Criteria: ${JSON.stringify(location?.selectionCriteria || {})}`, 'color: #4CAF50');
            console.log(`%c  Valid: ${record.isValid}`, record.isValid ? 'color: #4CAF50' : 'color: #f44336');
        }

        return record;
    },

    /**
     * 记录被抛弃的组件
     * @param {string} componentId - 组件唯一ID
     * @param {string} componentType - 组件类型
     * @param {object} data - 创建组件时使用的数据
     * @param {string} reason - 抛弃原因
     */
    recordAbandoned(componentId, componentType, data, reason) {
        return this.recordCreation(componentId, componentType, data, {
            abandoned: true,
            abandonReason: reason
        });
    },

    /**
     * 获取组件的位置记录
     * @param {string} componentId - 组件ID
     * @returns {object|null} - 位置记录
     */
    getRecord(componentId) {
        return this.locationRecords.get(componentId) || null;
    },

    /**
     * 获取所有组件位置记录
     * @returns {Array} - 所有记录数组
     */
    getAllRecords() {
        return Array.from(this.locationRecords.values());
    },

    /**
     * 验证所有组件的位置是否正确
     * @returns {object} - 验证结果
     */
    validateAll() {
        const results = {
            valid: [],
            invalid: [],
            warnings: [],
            abandoned: []
        };

        for (const [componentId, record] of this.locationRecords.entries()) {
            // 首先检查是否被抛弃
            if (record.abandoned) {
                results.abandoned.push({
                    componentId,
                    componentType: record.componentType,
                    reason: record.abandonReason || 'Unknown',
                    criteria: record.creationData
                });
                continue;
            }

            if (!record.parentId) {
                results.invalid.push({
                    componentId,
                    componentType: record.componentType,
                    reason: '无法找到父组件',
                    criteria: record.selectionCriteria
                });
            } else {
                // 检查父组件是否存在
                const parentExists = this._checkParentExists(record.parentType, record.parentId);
                if (parentExists) {
                    results.valid.push({
                        componentId,
                        componentType: record.componentType,
                        parentType: record.parentType,
                        parentId: record.parentId
                    });
                } else {
                    results.warnings.push({
                        componentId,
                        componentType: record.componentType,
                        reason: '父组件不存在',
                        parentType: record.parentType,
                        parentId: record.parentId
                    });
                }
            }
        }

        console.log(`%c[ComponentLocationManager] Validation Complete`, 'color: #2196F3; font-weight: bold');
        console.log(`%c  ✅ Valid: ${results.valid.length}`, 'color: #4CAF50');
        console.log(`%c  ⚠️ Warnings: ${results.warnings.length}`, 'color: #FF9800');
        console.log(`%c  ❌ Invalid: ${results.invalid.length}`, 'color: #f44336');
        console.log(`%c  🗑️ Abandoned: ${results.abandoned.length}`, 'color: #9E9E9E');

        if (results.warnings.length > 0) {
            console.log(`%c[ComponentLocationManager] Warnings Details:`, 'color: #FF9800');
            results.warnings.forEach(w => {
                console.log(`  - ${w.componentType}(${w.componentId}): ${w.reason}`);
            });
        }

        if (results.invalid.length > 0) {
            console.log(`%c[ComponentLocationManager] Invalid Details:`, 'color: #f44336');
            results.invalid.forEach(i => {
                console.log(`  - ${i.componentType}(${i.componentId}): ${i.reason}`);
                console.log(`    Criteria: ${JSON.stringify(i.criteria)}`);
            });
        }

        if (results.abandoned.length > 0) {
            console.log(`%c[ComponentLocationManager] Abandoned Details:`, 'color: #9E9E9E');
            results.abandoned.forEach(a => {
                console.log(`  - ${a.componentType}(${a.componentId}): ${a.reason}`);
                console.log(`    Criteria: ${JSON.stringify(a.criteria)}`);
            });
        }

        return results;
    },

    /**
     * 检查父组件是否存在
     * @param {string} parentType - 父组件类型
     * @param {string} parentId - 父组件ID
     * @returns {boolean}
     */
    _checkParentExists(parentType, parentId) {
        if (!parentId) return false;

        switch (parentType) {
            case 'ChatContainer':
                return true;
            case 'AssistantMessage': {
                const messages = StateManager.getState('messages') || [];
                return messages.some(m => m.id === parentId);
            }
            case 'ResponseBlock': {
                return StateManager.state.responseBlocks.has(parentId);
            }
            default:
                return true;
        }
    },

    /**
     * 按父组件分组获取组件
     * @param {string} parentId - 父组件ID
     * @returns {Array} - 子组件列表
     */
    getComponentsByParent(parentId) {
        return Array.from(this.locationRecords.values()).filter(
            record => record.parentId === parentId
        );
    },

    /**
     * 获取组件树结构
     * @returns {object} - 组件树
     */
    getComponentTree() {
        const tree = {};

        for (const record of this.locationRecords.values()) {
            const parentId = record.parentId || 'root';

            if (!tree[parentId]) {
                tree[parentId] = {
                    parentType: record.parentType,
                    children: []
                };
            }

            tree[parentId].children.push({
                componentId: record.componentId,
                componentType: record.componentType,
                criteria: record.selectionCriteria
            });
        }

        return tree;
    },

    /**
     * 导出所有记录为JSON
     * @returns {string} - JSON字符串
     */
    exportRecords() {
        return JSON.stringify(Array.from(this.locationRecords.values()), null, 2);
    },

    /**
     * 清除所有记录
     */
    clear() {
        this.locationRecords.clear();
        console.log('[ComponentLocationManager] All records cleared');
    }
};

// 挂载到全局对象，供其他模块和测试使用
window.ComponentLocationManager = ComponentLocationManager;

// 自动初始化
ComponentLocationManager.init();
