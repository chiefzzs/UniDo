/**
 * StorageManager - 存储配置管理服务
 * 
 * 支持两种配置：
 * 1. 实体存储配置 (Entity Storage Config) - 控制哪些实体类型需要持久化
 * 2. 事件存储配置 (Event Storage Config) - 控制哪些事件类型需要存储到项目时间
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { DataNormalizer } from '../infrastructure/DataNormalizer.js';

export const StorageManager = {
    api: ApiClient,

    // ==================== 实体存储配置 ====================

    // 获取存储配置列表
    async getStorages(params = {}) {
        EventBus.emit('storage:loading');
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/storage-config' + (query ? '?' + query : ''));
            
            // 直接返回配置列表
            const storages = Array.isArray(result) ? result : [];
            StateManager.setState('storages', storages);
            StateManager.setState('storagesLoading', false);
            EventBus.emit('storage:loaded', { storages, total: storages.length });
            return storages;
        } catch (error) {
            EventBus.emit('storage:error', { error: error.message });
            throw error;
        }
    },

    // 更新存储配置
    async updateStorage(entity_type, data) {
        try {
            const result = await this.api.put(`/storage-config/${entity_type}`, data);
            EventBus.emit('storage:updated', { entity_type, data });
            return result;
        } catch (error) {
            EventBus.emit('storage:error', { error: error.message });
            throw error;
        }
    },

    // 批量更新存储配置
    async batchUpdateStorage(updates) {
        try {
            const result = await this.api.put(`/storage-config/batch`, { updates });
            EventBus.emit('storage:batch_updated', { updates });
            return result;
        } catch (error) {
            EventBus.emit('storage:error', { error: error.message });
            throw error;
        }
    },

    // ==================== 事件存储配置 ====================

    // 获取事件存储配置列表
    async getEventStorages(params = {}) {
        EventBus.emit('eventStorage:loading');
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/event-storage-config' + (query ? '?' + query : ''));
            
            const eventStorages = Array.isArray(result) ? result : [];
            StateManager.setState('eventStorages', eventStorages);
            StateManager.setState('eventStoragesLoading', false);
            EventBus.emit('eventStorage:loaded', { eventStorages, total: eventStorages.length });
            return eventStorages;
        } catch (error) {
            EventBus.emit('eventStorage:error', { error: error.message });
            throw error;
        }
    },

    // 更新单个事件存储配置
    async updateEventStorage(event_type, data) {
        try {
            const result = await this.api.put(`/event-storage-config/${encodeURIComponent(event_type)}`, data);
            EventBus.emit('eventStorage:updated', { event_type, data });
            return result;
        } catch (error) {
            EventBus.emit('eventStorage:error', { error: error.message });
            throw error;
        }
    },

    // 批量更新事件存储配置
    async batchUpdateEventStorage(updates, projectId = null) {
        try {
            const url = projectId 
                ? `/event-storage-config/batch?project_id=${encodeURIComponent(projectId)}`
                : '/event-storage-config/batch';
            const result = await this.api.post(url, { updates });
            EventBus.emit('eventStorage:batch_updated', { updates });
            return result;
        } catch (error) {
            EventBus.emit('eventStorage:error', { error: error.message });
            throw error;
        }
    },

    // 重置事件存储配置为默认值
    async resetEventStorage(projectId = null) {
        try {
            const url = projectId 
                ? `/event-storage-config/reset?project_id=${encodeURIComponent(projectId)}`
                : '/event-storage-config/reset';
            const result = await this.api.post(url);
            EventBus.emit('eventStorage:reset');
            return result;
        } catch (error) {
            EventBus.emit('eventStorage:error', { error: error.message });
            throw error;
        }
    },

    // 检查事件是否应该被存储
    async checkEventPersist(event_type, projectId = null) {
        try {
            const url = projectId 
                ? `/event-storage-config/check/${encodeURIComponent(event_type)}?project_id=${encodeURIComponent(projectId)}`
                : `/event-storage-config/check/${encodeURIComponent(event_type)}`;
            const result = await this.api.get(url);
            return result;
        } catch (error) {
            EventBus.emit('eventStorage:error', { error: error.message });
            throw error;
        }
    }
};

window.StorageManager = StorageManager;
