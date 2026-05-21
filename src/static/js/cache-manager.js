class CacheManager {
  constructor() {
    this.storageKeyPrefix = 'chat_session_';
    this.currentSessionId = null;
    this.throttleTimers = {};
    this.pendingUpdates = {};
  }

  init(sessionId) {
    this.currentSessionId = sessionId;
    return this.loadSession(sessionId);
  }

  loadSession(sessionId) {
    const key = this._getStorageKey(sessionId);
    const data = localStorage.getItem(key);
    
    if (!data) {
      return this._createEmptySession(sessionId);
    }
    
    try {
      const parsed = JSON.parse(data);
      if (this._validateSessionData(parsed)) {
        return parsed;
      }
      return this._createEmptySession(sessionId);
    } catch {
      this.clearSession(sessionId);
      return this._createEmptySession(sessionId);
    }
  }

  saveResponseBlock(blockId, blockData) {
    const sessionData = this._getCurrentSessionData();
    
    const existingIndex = sessionData.response_blocks.findIndex(
      b => b.block_id === blockId
    );
    
    if (existingIndex >= 0) {
      sessionData.response_blocks[existingIndex] = {
        ...sessionData.response_blocks[existingIndex],
        ...blockData,
        updated_at: new Date().toISOString()
      };
    } else {
      sessionData.response_blocks.push({
        ...blockData,
        block_id: blockId,
        created_at: new Date().toISOString()
      });
    }
    
    this._trimBlocks(sessionData);
    this._saveSession(sessionData);
  }

  updateToolOutput(blockId, callId, output) {
    const throttleKey = `tool_output_${callId}`;
    if (this.throttleTimers[throttleKey]) {
      clearTimeout(this.throttleTimers[throttleKey]);
    }
    
    if (!this.pendingUpdates[blockId]) {
      this.pendingUpdates[blockId] = {};
    }
    if (!this.pendingUpdates[blockId][callId]) {
      this.pendingUpdates[blockId][callId] = '';
    }
    this.pendingUpdates[blockId][callId] += output;
    
    this.throttleTimers[throttleKey] = setTimeout(() => {
      const sessionData = this._getCurrentSessionData();
      const block = sessionData.response_blocks.find(b => b.block_id === blockId);
      
      if (block && block.tool_calls) {
        const toolCall = block.tool_calls.find(tc => tc.call_id === callId);
        if (toolCall) {
          toolCall.output = (toolCall.output || '') + this.pendingUpdates[blockId][callId];
          if (toolCall.output.length > CACHE_CONFIG.max_tool_output_length) {
            toolCall.output = toolCall.output.slice(0, CACHE_CONFIG.max_tool_output_length) + '...[truncated]';
          }
        }
      }
      
      this._saveSession(sessionData);
      delete this.pendingUpdates[blockId][callId];
      delete this.throttleTimers[throttleKey];
    }, 100);
  }

  updateDisplayState(state) {
    const sessionData = this._getCurrentSessionData();
    sessionData.display_state = {
      ...sessionData.display_state,
      ...state,
      last_accessed_at: new Date().toISOString()
    };
    this._saveSession(sessionData);
  }

  updateScrollPosition(position) {
    sessionStorage.setItem(`scroll_${this.currentSessionId}`, position.toString());
  }

  getScrollPosition() {
    const saved = sessionStorage.getItem(`scroll_${this.currentSessionId}`);
    return saved ? parseInt(saved, 10) : 0;
  }

  addToolCall(blockId, toolCallData) {
    const sessionData = this._getCurrentSessionData();
    const block = sessionData.response_blocks.find(b => b.block_id === blockId);
    
    if (block) {
      block.tool_calls = block.tool_calls || [];
      block.tool_calls.push({
        ...toolCallData,
        started_at: new Date().toISOString()
      });
      this._saveSession(sessionData);
    }
  }

  updateToolResult(blockId, callId, resultData) {
    const sessionData = this._getCurrentSessionData();
    const block = sessionData.response_blocks.find(b => b.block_id === blockId);
    
    if (block && block.tool_calls) {
      const toolCall = block.tool_calls.find(tc => tc.call_id === callId);
      if (toolCall) {
        toolCall.status = resultData.success ? 'completed' : 'failed';
        toolCall.result = resultData.result;
        toolCall.completed_at = new Date().toISOString();
      }
    }
    
    this._saveSession(sessionData);
  }

  saveUserMessage(message) {
    const sessionData = this._getCurrentSessionData();
    
    sessionData.messages = sessionData.messages || [];
    
    const existingIndex = sessionData.messages.findIndex(
      m => m.id === message.id || m.timestamp === message.timestamp
    );
    
    if (existingIndex >= 0) {
      sessionData.messages[existingIndex] = {
        ...sessionData.messages[existingIndex],
        ...message
      };
    } else {
      sessionData.messages.push(message);
    }
    
    // 限制消息数量
    if (sessionData.messages.length > CACHE_CONFIG.max_blocks_per_session) {
      sessionData.messages = sessionData.messages.slice(
        -CACHE_CONFIG.max_blocks_per_session
      );
    }
    
    this._saveSession(sessionData);
  }

  getMessages() {
    const sessionData = this._getCurrentSessionData();
    return sessionData.messages || [];
  }

  // 保存WebSocket消息（用户消息和助手消息）
  saveWebSocketMessage(message) {
    const sessionData = this._getCurrentSessionData();

    // 确保有ws_messages数组
    sessionData.ws_messages = sessionData.ws_messages || [];

    // 添加消息，包含时间戳
    sessionData.ws_messages.push({
      ...message,
      cached_at: new Date().toISOString()
    });

    // 限制消息数量
    if (sessionData.ws_messages.length > CACHE_CONFIG.max_blocks_per_session * 2) {
      sessionData.ws_messages = sessionData.ws_messages.slice(-CACHE_CONFIG.max_blocks_per_session * 2);
    }

    this._saveSession(sessionData);
  }

  // 获取WebSocket消息
  getWebSocketMessages() {
    const sessionData = this._getCurrentSessionData();
    return sessionData.ws_messages || [];
  }

  clearSession(sessionId) {
    const key = this._getStorageKey(sessionId);
    localStorage.removeItem(key);
    sessionStorage.removeItem(`scroll_${sessionId}`);
  }

  clearAll() {
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(this.storageKeyPrefix)) {
        localStorage.removeItem(key);
      }
    });
    Object.keys(sessionStorage).forEach(key => {
      if (key.startsWith('scroll_')) {
        sessionStorage.removeItem(key);
      }
    });
  }

  cleanupExpiredSessions() {
    const now = new Date();
    const maxAgeMs = CACHE_CONFIG.max_session_age_days * 24 * 60 * 60 * 1000;
    
    const sessionKeys = Object.keys(localStorage).filter(
      key => key.startsWith(this.storageKeyPrefix)
    );
    
    const sessions = sessionKeys.map(key => {
      try {
        const data = JSON.parse(localStorage.getItem(key));
        return { key, lastAccess: new Date(data.display_state?.last_accessed_at || 0) };
      } catch {
        return { key, lastAccess: new Date(0) };
      }
    });
    
    sessions.sort((a, b) => b.lastAccess.getTime() - a.lastAccess.getTime());
    
    sessions.forEach((session, index) => {
      const ageMs = now.getTime() - session.lastAccess.getTime();
      if (ageMs > maxAgeMs || index >= CACHE_CONFIG.max_sessions) {
        localStorage.removeItem(session.key);
        const sessionId = session.key.replace(this.storageKeyPrefix, '');
        sessionStorage.removeItem(`scroll_${sessionId}`);
      }
    });
  }

  _getStorageKey(sessionId) {
    return `${this.storageKeyPrefix}${sessionId}`;
  }
  
  _createEmptySession(sessionId) {
    return {
      session_id: sessionId,
      response_blocks: [],
      display_state: {
        scroll_position: 0,
        last_accessed_at: new Date().toISOString()
      }
    };
  }
  
  _validateSessionData(data) {
    return data && data.session_id && Array.isArray(data.response_blocks);
  }
  
  _getCurrentSessionData() {
    const key = this._getStorageKey(this.currentSessionId);
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : this._createEmptySession(this.currentSessionId);
  }
  
  _saveSession(sessionData) {
    const key = this._getStorageKey(sessionData.session_id);
    localStorage.setItem(key, JSON.stringify(sessionData));
  }
  
  _trimBlocks(sessionData) {
    if (sessionData.response_blocks.length > CACHE_CONFIG.max_blocks_per_session) {
      sessionData.response_blocks = sessionData.response_blocks.slice(
        -CACHE_CONFIG.max_blocks_per_session
      );
    }
  }
}

const CACHE_CONFIG = {
  max_blocks_per_session: 100,
  max_tool_calls_per_block: 10,
  max_tool_output_length: 10000,
  max_storage_size: 4 * 1024 * 1024,
  max_session_age_days: 30,
  max_sessions: 10
};

window.cacheManager = new CacheManager();