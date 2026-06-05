/**
 * WSClient - WebSocket 客户端
 * 支持实时双向通信、心跳检测、自动重连
 */
import { EventBus } from './EventBus.js';
import { StateManager } from './StateManager.js';

export const WSClient = {
    socket: null,
    url: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,
    heartbeatInterval: null,
    listeners: new Map(),

    // 连接 WebSocket
    connect() {
        return new Promise((resolve, reject) => {
            const clientId = 'client-' + Math.random().toString(36).substr(2, 9);
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            this.url = `${protocol}//${window.location.host}/ws/${clientId}`;

            console.log('[WS] Connecting to:', this.url);
            this.socket = new WebSocket(this.url);

            this.socket.onopen = () => {
                console.log('[WS] Connected');
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                EventBus.emit('ws:connected', { clientId });
                StateManager.setState('wsConnected', true);
                StateManager.setState('clientId', clientId);
                resolve();
            };

            this.socket.onclose = (event) => {
                console.log('[WS] Disconnected:', event.code, event.reason);
                this.stopHeartbeat();
                EventBus.emit('ws:disconnected', { code: event.code, reason: event.reason });
                StateManager.setState('wsConnected', false);
                this.handleReconnect();
            };

            this.socket.onerror = (error) => {
                console.error('[WS] Error:', error);
                EventBus.emit('ws:error', { error });
                reject(error);
            };

            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    EventBus.emit('ws:message', data);
                } catch (e) {
                    console.error('[WS] Parse error:', e);
                }
            };
        });
    },

    // 发送消息
    send(action, data) {
        console.log(`%c[WS] 📤 尝试发送消息: action=${action}`, 'color: #2196F3; font-weight: bold');
        console.log(`%c[WS] 🔍 Socket状态: ${this.socket ? `readyState=${this.socket.readyState} (${this._getStateText(this.socket.readyState)})` : 'null'}`, 'color: #607D8B');
        
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = JSON.stringify({ action, data });
            console.log(`%c[WS] ✅ 发送消息成功: ${message.substring(0, 200)}${message.length > 200 ? '...' : ''}`, 'color: #4CAF50');
            this.socket.send(message);
            return true;
        }
        
        console.error(`%c[WS] ❌ 发送失败，socket未连接`, 'color: #F44336; font-weight: bold');
        console.log(`%c[WS] 📊 Socket详情: socket=${!!this.socket}, readyState=${this.socket?.readyState}`, 'color: #607D8B');
        return false;
    },
    
    _getStateText(state) {
        const states = {
            0: 'CONNECTING',
            1: 'OPEN',
            2: 'CLOSING',
            3: 'CLOSED'
        };
        return states[state] || 'UNKNOWN';
    },

    // 发送对话消息
    sendMessage(sessionId, content) {
        return this.send('send_message', { session_id: sessionId, content });
    },

    // 发送会话切换消息（触发后端历史回放）
    sendSessionSwitch(sessionId) {
        return this.send('switch_session', { session_id: sessionId });
    },
    
    // 发送自定义消息（直接发送完整payload）
    sendCustomMessage(payload) {
        console.log(`%c[WS] 📤 尝试发送自定义消息`, 'color: #2196F3; font-weight: bold');
        
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = JSON.stringify(payload);
            console.log(`%c[WS] ✅ 发送自定义消息成功: ${message.substring(0, 200)}${message.length > 200 ? '...' : ''}`, 'color: #4CAF50');
            this.socket.send(message);
            return true;
        }
        
        console.error(`%c[WS] ❌ 发送失败，socket未连接`, 'color: #F44336; font-weight: bold');
        return false;
    },
    
    // 心跳检测
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            this.send('ping', {});
        }, 30000);
    },

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    },

    // 自动重连
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[WS] Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('[WS] Max reconnect attempts reached');
            EventBus.emit('ws:reconnect-failed', {});
        }
    },

    // 断开连接
    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
};

window.WSClient = WSClient;
