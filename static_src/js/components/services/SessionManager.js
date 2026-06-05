/**
 * SessionManager - 会话管理服务（增强版，包含详细日志）
 * 
 * 职责：
 * 1. 管理会话的创建、删除、切换
 * 2. 切换会话时通过WebSocket触发后端历史消息回放
 * 3. 维护会话列表状态
 */
import { ApiClient } from '../infrastructure/ApiClient.js';
import { EventBus } from '../infrastructure/EventBus.js';
import { StateManager } from '../infrastructure/StateManager.js';
import { DataNormalizer } from '../infrastructure/DataNormalizer.js';
import { WSClient } from '../infrastructure/WSClient.js';

export const SessionManager = {
    api: ApiClient,
    wsClient: WSClient,

    // 获取会话列表
    async getSessions(projectId) {
        EventBus.emit('session:loading');
        try {
            const url = `/projects/${projectId}/sessions`;
            console.log('[SessionManager] GET request URL:', url);

            const result = await this.api.get(url);
            console.log('[SessionManager] Raw response:', result);
            console.log('[SessionManager] Response type:', typeof result);

            // 使用统一的数据规范化工具
            const rawData = DataNormalizer.parseResponse(result, 'sessions');
            
            // 规范化会话数据，确保有 id 字段
            const sessions = rawData.map(session => ({
                ...session,
                id: session.id || session.session_id || ''
            }));

            console.log('[SessionManager] Parsed sessions:', sessions);
            console.log('[SessionManager] Sessions count:', sessions.length);

            StateManager.setState('sessions', sessions);
            EventBus.emit('session:loaded', { sessions });

            return sessions;
        } catch (error) {
            console.error('[SessionManager] Error loading sessions:', error);
            EventBus.emit('session:error', { error: error.message });
            throw error;
        }
    },

    // 创建会话
    async createSession(projectId, title = '新会话') {
        try {
            const url = `/projects/${projectId}/sessions`;
            console.log('[SessionManager] POST request URL:', url);

            const result = await this.api.post(url, { title });
            console.log('[SessionManager] Create session response:', result);

            // 获取新创建会话的ID（支持多种后端返回格式）
            const sessionId = result.id || result.session_id || result.data?.id || result.data?.session_id;
            console.log('[SessionManager] New session ID:', sessionId);

            // 刷新会话列表
            await this.getSessions(projectId);

            // 自动切换到新创建的会话（只有当 sessionId 有效时）
            if (sessionId) {
                await this.switchSession(sessionId);
            } else {
                console.warn('[SessionManager] Could not get session ID from response');
            }

            EventBus.emit('session:created', { sessionId, title });
            return result;
        } catch (error) {
            console.error('[SessionManager] Error creating session:', error);
            EventBus.emit('session:error', { error: error.message });
            throw error;
        }
    },

    // 切换会话
    async switchSession(sessionId) {
        // 添加 sessionId 检查
        if (!sessionId) {
            console.error('[SessionManager] switchSession called with undefined/null sessionId');
            EventBus.emit('session:error', { error: 'Invalid session ID' });
            return;
        }

        console.log('\n=== [SessionManager] Switching to session ===');
        console.log('[SessionManager] Session ID:', sessionId);
        
        // 检查WebSocket连接状态
        const wsConnected = StateManager.getState('wsConnected');
        console.log('[SessionManager] WebSocket connected:', wsConnected);
        
        if (!wsConnected) {
            console.warn('[SessionManager] WebSocket not connected, will retry after connection');
            // 等待WebSocket连接后再发送切换请求
            const handleConnected = () => {
                this._performSessionSwitch(sessionId);
                EventBus.off('ws:connected', handleConnected);
            };
            EventBus.on('ws:connected', handleConnected);
            return;
        }
        
        // 执行会话切换
        this._performSessionSwitch(sessionId);
    },

    // 执行会话切换（内部方法）
    _performSessionSwitch(sessionId) {
        // 清空当前消息列表，准备接收回放消息
        StateManager.setState('messages', []);
        
        // 更新当前会话ID
        StateManager.setState('currentSessionId', sessionId);
        
        // 发送会话切换消息到后端，触发历史消息回放
        // 后端会通过WebSocket主动推送历史消息
        const success = this.wsClient.sendSessionSwitch(sessionId);
        
        if (success) {
            console.log('[SessionManager] Session switch message sent successfully');
        } else {
            console.error('[SessionManager] Failed to send session switch message');
            EventBus.emit('session:error', { error: 'Failed to send session switch message' });
        }
        
        // 发布本地事件，通知UI会话正在切换
        EventBus.emit('session:switching', { sessionId });
    },

    // 删除会话
    async deleteSession(sessionId) {
        // 添加 sessionId 检查
        if (!sessionId) {
            console.error('[SessionManager] deleteSession called with undefined/null sessionId');
            return;
        }

        try {
            await this.api.delete(`/sessions/${sessionId}`);
            const currentProjectId = StateManager.getState('currentProjectId');
            if (currentProjectId) {
                await this.getSessions(currentProjectId);
            }
            EventBus.emit('session:deleted', { sessionId });
        } catch (error) {
            console.error('[SessionManager] Error deleting session:', error);
            EventBus.emit('session:error', { error: error.message });
            throw error;
        }
    }
};

window.SessionManager = SessionManager;
