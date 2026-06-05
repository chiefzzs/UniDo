/**
 * PromptManager - 提示词管理服务
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';

export const PromptManager = {
    api: ApiClient,

    // 获取提示词列表
    async getPrompts(params = {}) {
        EventBus.emit('prompt:loading', { loading: true });
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/prompts' + (query ? '?' + query : ''));
            
            const prompts = result || [];

            StateManager.setState('prompts', prompts);
            StateManager.setState('promptsLoading', false);
            EventBus.emit('prompt:loaded', { prompts, total: result.total || prompts.length });
            return prompts;
        } catch (error) {
            StateManager.setState('promptsLoading', false);
            EventBus.emit('prompt:error', { error: error.message });
            throw error;
        }
    },

    // 创建提示词
    async createPrompt(data) {
        EventBus.emit('prompt:loading');
        try {
            const result = await this.api.post('/prompts', data);
            EventBus.emit('prompt:created', { prompt: result });
            return result;
        } catch (error) {
            EventBus.emit('prompt:error', { error: error.message });
            throw error;
        }
    },

    // 更新提示词
    async updatePrompt(promptId, data) {
        try {
            const result = await this.api.put(`/prompts/${promptId}`, data);
            EventBus.emit('prompt:updated', { prompt: result });
            return result;
        } catch (error) {
            EventBus.emit('prompt:error', { error: error.message });
            throw error;
        }
    },

    // 删除提示词
    async deletePrompt(promptId) {
        try {
            await this.api.delete(`/prompts/${promptId}`);
            StateManager.setState('prompts', StateManager.getState('prompts').filter(p => p.prompt_id !== promptId));
            EventBus.emit('prompt:deleted', { prompt_id: promptId });
        } catch (error) {
            EventBus.emit('prompt:error', { error: error.message });
            throw error;
        }
    },

    // 获取提示词详情
    async getPrompt(promptId) {
        try {
            const result = await this.api.get(`/prompts/${promptId}`);
            return result;
        } catch (error) {
            EventBus.emit('prompt:error', { error: error.message });
            throw error;
        }
    },

    // 渲染提示词（替换变量）
    async renderPrompt(promptId, variables = {}) {
        try {
            const result = await this.api.post(`/prompts/${promptId}/render`, { variables });
            return result;
        } catch (error) {
            EventBus.emit('prompt:error', { error: error.message });
            throw error;
        }
    }
};

window.PromptManager = PromptManager;