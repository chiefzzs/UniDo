/**
 * ProjectManager - 项目管理服务
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { DataNormalizer } from '../infrastructure/DataNormalizer.js';

export const ProjectManager = {
    api: ApiClient,

    // 获取项目列表
    async getProjects(params = {}) {
        EventBus.emit('project:loading', { loading: true });
        try {
            const query = new URLSearchParams(params).toString();
            const result = await this.api.get('/projects' + (query ? '?' + query : ''));
            
            // 使用统一的规范化工具
            const rawData = DataNormalizer.parseResponse(result, 'projects');
            const projects = DataNormalizer.normalizeProject(rawData);

            console.log('[ProjectManager] Raw result:', result);
            console.log('[ProjectManager] Parsed projects:', projects);
            console.log('[ProjectManager] First project id:', projects[0]?.id);
            StateManager.setState('projects', projects);
            StateManager.setState('projectsLoading', false);
            EventBus.emit('project:loaded', { projects, total: projects.length });

            return projects;
        } catch (error) {
            console.error('[ProjectManager] Error loading projects:', error);
            StateManager.setState('projectsLoading', false);
            EventBus.emit('project:error', { error: error.message });
            throw error;
        }
    },

    // 创建项目
    async createProject(data) {
        EventBus.emit('project:loading');
        try {
            const result = await this.api.post('/projects', data);
            const project = DataNormalizer.normalizeProject(result);
            EventBus.emit('project:created', { project });
            return project;
        } catch (error) {
            EventBus.emit('project:error', { error: error.message });
            throw error;
        }
    },

    // 更新项目
    async updateProject(projectId, data) {
        try {
            const result = await this.api.put(`/projects/${projectId}`, data);
            const project = DataNormalizer.normalizeProject(result);
            EventBus.emit('project:updated', { project });
            return project;
        } catch (error) {
            EventBus.emit('project:error', { error: error.message });
            throw error;
        }
    },

    // 删除项目
    async deleteProject(projectId) {
        try {
            await this.api.delete(`/projects/${projectId}`);
            const projects = StateManager.getState('projects') || [];
            StateManager.setState('projects', projects.filter(p => p.id !== projectId));
            EventBus.emit('project:deleted', { id: projectId });
        } catch (error) {
            EventBus.emit('project:error', { error: error.message });
            throw error;
        }
    },

    // 批量删除
    async batchDelete(ids) {
        try {
            await this.api.post('/projects/batch-delete', { ids });
            const projects = StateManager.getState('projects') || [];
            StateManager.setState('projects', projects.filter(p => !ids.includes(p.id)));
            EventBus.emit('project:deleted', { ids });
        } catch (error) {
            EventBus.emit('project:error', { error: error.message });
            throw error;
        }
    }
};

window.ProjectManager = ProjectManager;
