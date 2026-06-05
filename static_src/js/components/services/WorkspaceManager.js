/**
 * WorkspaceManager - 工作区管理服务
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { DataNormalizer } from '../infrastructure/DataNormalizer.js';

export const WorkspaceManager = {
    api: ApiClient,

    // 获取工作区列表
    async getWorkspaces(params = {}) {
        EventBus.emit('workspace:loading');
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/workspaces' + (query ? '?' + query : ''));
            
            // 使用统一的规范化工具
            const rawData = DataNormalizer.parseResponse(result, 'workspaces');
            const workspaces = DataNormalizer.normalizeWorkspace(rawData);

            StateManager.setState('workspaces', workspaces);
            StateManager.setState('workspacesLoading', false);
            EventBus.emit('workspace:loaded', { workspaces, total: result.total || workspaces.length });
            return workspaces;
        } catch (error) {
            EventBus.emit('workspace:error', { error: error.message });
            throw error;
        }
    },

    // 创建工作区
    async createWorkspace(data) {
        EventBus.emit('workspace:loading');
        try {
            const result = await this.api.post('/workspaces', data);
            const workspace = DataNormalizer.normalizeWorkspace(result);
            EventBus.emit('workspace:created', { workspace });
            return workspace;
        } catch (error) {
            EventBus.emit('workspace:error', { error: error.message });
            throw error;
        }
    },

    // 更新工作区
    async updateWorkspace(id, data) {
        try {
            const result = await this.api.put(`/workspaces/${id}`, data);
            const workspace = DataNormalizer.normalizeWorkspace(result);
            EventBus.emit('workspace:updated', { workspace });
            return workspace;
        } catch (error) {
            EventBus.emit('workspace:error', { error: error.message });
            throw error;
        }
    },

    // 删除工作区
    async deleteWorkspace(id) {
        try {
            await this.api.delete(`/workspaces/${id}`);
            StateManager.setState('workspaces', StateManager.getState('workspaces').filter(w => w.id !== id));
            EventBus.emit('workspace:deleted', { id });
        } catch (error) {
            EventBus.emit('workspace:error', { error: error.message });
            throw error;
        }
    },

    // 批量删除
    async batchDelete(ids) {
        try {
            await this.api.post('/workspaces/batch-delete', { ids });
            StateManager.setState('workspaces', StateManager.getState('workspaces').filter(w => !ids.includes(w.id)));
            EventBus.emit('workspace:deleted', { ids });
        } catch (error) {
            EventBus.emit('workspace:error', { error: error.message });
            throw error;
        }
    }
};

window.WorkspaceManager = WorkspaceManager;
