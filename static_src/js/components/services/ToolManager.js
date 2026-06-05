/**
 * ToolManager - 工具管理服务
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { DataNormalizer } from '../infrastructure/DataNormalizer.js';

export const ToolManager = {
    api: ApiClient,

    // 获取工具列表
    async getTools(params = {}) {
        EventBus.emit('tool:loading');
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/tools' + (query ? '?' + query : ''));
            
            // 使用统一的规范化工具
            const rawData = DataNormalizer.parseResponse(result, 'tools');
            const tools = DataNormalizer.normalizeTool(rawData);

            StateManager.setState('tools', tools);
            StateManager.setState('toolsLoading', false);
            EventBus.emit('tool:loaded', { tools, total: result.total || tools.length });
            return tools;
        } catch (error) {
            EventBus.emit('tool:error', { error: error.message });
            throw error;
        }
    },

    // 创建工具
    async createTool(data) {
        EventBus.emit('tool:loading');
        try {
            const result = await this.api.post('/tools', data);
            const tool = DataNormalizer.normalizeTool(result);
            EventBus.emit('tool:created', { tool });
            return tool;
        } catch (error) {
            EventBus.emit('tool:error', { error: error.message });
            throw error;
        }
    },

    // 更新工具
    async updateTool(id, data) {
        try {
            const result = await this.api.put(`/tools/${id}`, data);
            const tool = DataNormalizer.normalizeTool(result);
            EventBus.emit('tool:updated', { tool });
            return tool;
        } catch (error) {
            EventBus.emit('tool:error', { error: error.message });
            throw error;
        }
    },

    // 删除工具
    async deleteTool(id) {
        try {
            await this.api.delete(`/tools/${id}`);
            StateManager.setState('tools', StateManager.getState('tools').filter(t => t.id !== id));
            EventBus.emit('tool:deleted', { id });
        } catch (error) {
            EventBus.emit('tool:error', { error: error.message });
            throw error;
        }
    },

    // 批量删除
    async batchDelete(ids) {
        try {
            await this.api.post('/tools/batch-delete', { ids });
            StateManager.setState('tools', StateManager.getState('tools').filter(t => !ids.includes(t.id)));
            EventBus.emit('tool:deleted', { ids });
        } catch (error) {
            EventBus.emit('tool:error', { error: error.message });
            throw error;
        }
    }
};

window.ToolManager = ToolManager;
