/**
 * ModelManager - 模型管理服务
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { DataNormalizer } from '../infrastructure/DataNormalizer.js';

export const ModelManager = {
    api: ApiClient,

    // 获取模型列表
    async getModels(params = {}) {
        EventBus.emit('model:loading', { loading: true });
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/models' + (query ? '?' + query : ''));
            
            // 使用统一的规范化工具
            const rawData = DataNormalizer.parseResponse(result, 'models');
            const models = DataNormalizer.normalizeModel(rawData);

            StateManager.setState('models', models);
            StateManager.setState('modelsLoading', false);
            EventBus.emit('model:loaded', { models, total: result.total || models.length });
            return models;
        } catch (error) {
            StateManager.setState('modelsLoading', false);
            EventBus.emit('model:error', { error: error.message });
            throw error;
        }
    },

    // 创建模型
    async createModel(data) {
        EventBus.emit('model:loading');
        try {
            const result = await this.api.post('/models', data);
            const model = DataNormalizer.normalizeModel(result);
            EventBus.emit('model:created', { model });
            return model;
        } catch (error) {
            EventBus.emit('model:error', { error: error.message });
            throw error;
        }
    },

    // 更新模型
    async updateModel(id, data) {
        try {
            const result = await this.api.put(`/models/${id}`, data);
            const model = DataNormalizer.normalizeModel(result);
            EventBus.emit('model:updated', { model });
            return model;
        } catch (error) {
            EventBus.emit('model:error', { error: error.message });
            throw error;
        }
    },

    // 删除模型
    async deleteModel(id) {
        try {
            await this.api.delete(`/models/${id}`);
            StateManager.setState('models', StateManager.getState('models').filter(m => m.id !== id));
            EventBus.emit('model:deleted', { id });
        } catch (error) {
            EventBus.emit('model:error', { error: error.message });
            throw error;
        }
    },

    // 批量删除
    async batchDelete(ids) {
        try {
            await this.api.post('/models/batch-delete', { ids });
            StateManager.setState('models', StateManager.getState('models').filter(m => !ids.includes(m.id)));
            EventBus.emit('model:deleted', { ids });
        } catch (error) {
            EventBus.emit('model:error', { error: error.message });
            throw error;
        }
    }
};

window.ModelManager = ModelManager;
