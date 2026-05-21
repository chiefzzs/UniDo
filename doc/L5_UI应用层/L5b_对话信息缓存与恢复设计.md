# 对话信息缓存与恢复能力设计文档

---

## 1. 设计背景

### 1.1 问题描述

当前系统存在以下问题：
- **前端刷新丢失**：用户刷新浏览器后，所有对话历史、工具执行记录、思考过程等展示信息全部丢失
- **无法恢复上下文**：用户需要重新加载会话才能看到历史对话，但前端展示状态（如折叠/展开的工具卡片）无法恢复
- **体验不连贯**：页面切换或刷新导致用户体验中断

### 1.2 需求分析

**核心需求**：
1. **纯前端缓存**：所有缓存数据仅存储在浏览器端，不依赖后端持久化
2. **自动持久化**：实时缓存WebSocket收到的所有对话数据
3. **页面恢复**：刷新页面后自动从缓存恢复完整对话展示
4. **会话隔离**：按会话ID组织缓存，支持多会话管理
5. **容量控制**：限制缓存大小，防止占用过多存储空间

---

## 2. 设计方案

### 2.1 方案选择：纯前端缓存

**核心思路**：所有缓存数据仅存储在浏览器端，使用 `localStorage` 作为主存储，`sessionStorage` 存储临时状态。

**优点**：
- ✅ 纯前端实现，无需后端支持
- ✅ 零服务端改动，快速落地
- ✅ 实时缓存WebSocket数据
- ✅ 页面刷新后自动恢复
- ✅ 按会话隔离管理

**局限性**：
- ⚠️ 浏览器清除缓存会导致数据丢失
- ⚠️ 跨浏览器不共享缓存
- ⚠️ localStorage容量限制（约5MB）
- ⚠️ 敏感数据需注意安全

### 2.2 架构设计

```
┌──────────────────────────────────────────────────────────────┐
│                        前端层 (L5)                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    CacheManager                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │  │
│  │  │ localStorage│  │ sessionStorage│ │ 内存状态    │    │  │
│  │  │ (持久化数据) │  │ (临时状态)   │ │ (运行时)    │    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                               │
│                              ▼                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              响应块渲染与展示状态管理                    │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ThinkBlock│  │TextBlock │  │ToolCard  │             │  │
│  │  │(可折叠)  │  │(Markdown)│  │(独立卡片)│             │  │
│  │  └──────────┘  └──────────┘  └──────────┘             │  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                               │
│                              │ WebSocket                     │
│                              ▼                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 数据模型设计

### 3.1 缓存数据结构

**会话缓存对象**（存储在 localStorage）：

```javascript
{
  "chat_session_sess-abc123": {
    "session_id": "sess-abc123",
    "name": "我的会话",
    "response_blocks": [
      {
        "block_id": "msg-1779262012787",
        "status": "completed",
        "think_content": "用户需要创建目录，我需要分析意图...",
        "think_expanded": false,
        "text_content": "根据工具执行结果，我来总结一下：\n\n**任务完成情况：** ✅ 成功...",
        "tool_calls": [
          {
            "call_id": "call-xyz789",
            "tool_name": "RunCommand",
            "tool_id": "T12",
            "arguments": {
              "command": "mkdir test_10",
              "workspace": "D:\\learnning\\260521\\workspace"
            },
            "arguments_expanded": true,
            "output": "mkdir: created directory 'test_10'",
            "output_expanded": false,
            "status": "completed",
            "result": {
              "success": true,
              "message": "目录 test_10 已成功创建",
              "return_code": 0
            },
            "result_expanded": true,
            "started_at": "2026-05-20T15:27:30",
            "completed_at": "2026-05-20T15:27:31"
          }
        ],
        "created_at": "2026-05-20T15:27:30",
        "completed_at": "2026-05-20T15:27:31"
      }
    ],
    "display_state": {
      "scroll_position": 520,
      "last_accessed_at": "2026-05-20T15:30:00"
    }
  }
}
```

### 3.2 字段说明

#### 会话级别（Session）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| `session_id` | string | 会话唯一标识 | 非空 |
| `name` | string | 会话名称 | 可选 |
| `response_blocks` | array | 响应块列表 | 非空 |
| `display_state` | object | 展示状态 | 非空 |

#### 响应块级别（ResponseBlock）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| `block_id` | string | 响应块唯一标识 | 非空 |
| `status` | string | 状态：in_progress/completed/failed | 非空 |
| `think_content` | string | 思考过程文本 | 可选 |
| `think_expanded` | boolean | 思考块是否展开 | 默认false |
| `text_content` | string | Markdown文本回复 | 可选 |
| `tool_calls` | array | 工具调用列表 | 非空数组 |
| `created_at` | string | 创建时间(ISO格式) | 非空 |
| `completed_at` | string | 完成时间(ISO格式) | 可选 |

#### 工具调用级别（ToolCall）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| `call_id` | string | 调用唯一标识 | 非空 |
| `tool_name` | string | 工具名称 | 非空 |
| `tool_id` | string | 工具实例ID | 可选 |
| `arguments` | object | 调用参数 | 可选 |
| `arguments_expanded` | boolean | 参数区域是否展开 | 默认true |
| `output` | string | 执行输出文本 | 可选 |
| `output_expanded` | boolean | 输出区域是否展开 | 默认false |
| `status` | string | 状态：running/completed/failed | 非空 |
| `result` | object | 执行结果 | 可选 |
| `result_expanded` | boolean | 结果区域是否展开 | 默认true |
| `started_at` | string | 开始时间(ISO格式) | 非空 |
| `completed_at` | string | 完成时间(ISO格式) | 可选 |

#### 展示状态（DisplayState）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| `scroll_position` | number | 消息区域滚动位置 | 默认0 |
| `last_accessed_at` | string | 最后访问时间 | 非空 |

---

## 4. 缓存读写时机

### 4.1 写入时机

| 时机 | 触发事件 | 写入内容 | 存储位置 |
|-----|---------|---------|---------|
| **响应块创建** | `response_block.created` | 块基本结构 | localStorage |
| **思考内容更新** | 收到思考文本 | 思考内容（增量追加） | localStorage |
| **文本内容更新** | 收到文本回复 | 文本内容（增量追加） | localStorage |
| **工具调用添加** | `tool.call_started` | 工具调用信息 | localStorage |
| **工具输出更新** | `tool.execution_output` | 工具输出（增量追加，节流） | localStorage |
| **工具结果更新** | `tool.call_completed` | 工具执行结果 | localStorage |
| **响应块完成** | `response_block.completed` | 最终状态标记 | localStorage |
| **滚动位置变化** | 滚动事件（节流500ms） | 滚动位置 | sessionStorage |

### 4.2 读取时机

| 时机 | 触发事件 | 读取内容 | 说明 |
|-----|---------|---------|------|
| **页面加载** | `DOMContentLoaded` | 当前会话的所有数据 | 恢复完整对话 |
| **会话切换** | 选择会话 | 目标会话的所有数据 | 加载新会话 |
| **页面刷新** | `window.onload` | 当前会话数据 | 刷新后恢复 |
| **WebSocket重连** | 连接恢复 | 最新缓存数据 | 同步状态 |

### 4.3 写入策略配置

```javascript
const CACHE_WRITE_STRATEGIES = {
  // 实时写入：立即持久化
  realtime: ['response_block.created', 'tool.call_completed', 'response_block.completed'],
  
  // 节流写入：每 N ms 批量写入一次
  throttled: {
    'tool.execution_output': 100,  // 工具输出：每100ms写入一次
    'think_update': 200,           // 思考内容：每200ms写入一次
    'text_update': 300,            // 文本内容：每300ms写入一次
    'scroll': 500                  // 滚动位置：每500ms写入一次
  }
};
```

---

## 5. 容量控制与清理策略

### 5.1 缓存容量配置

```javascript
const CACHE_CONFIG = {
  // 单会话最大响应块数
  max_blocks_per_session: 100,
  
  // 单响应块最大工具调用数
  max_tool_calls_per_block: 10,
  
  // 工具输出最大字符数
  max_tool_output_length: 10000,
  
  // localStorage 最大占用空间（字节）
  max_storage_size: 4 * 1024 * 1024,  // 4MB
  
  // 会话最大保存天数
  max_session_age_days: 30,
  
  // 最多保存的会话数
  max_sessions: 10
};
```

### 5.2 清理策略

| 场景 | 清理条件 | 清理方式 |
|-----|---------|---------|
| **会话过期** | 超过 30 天未访问 | 自动删除 |
| **会话数量超限** | 超过 10 个会话 | 删除最旧的会话 |
| **存储容量超限** | 超过 4MB | 按LRU策略删除 |
| **数据损坏** | JSON解析失败 | 删除该会话缓存 |
| **手动清除** | 用户主动清除 | 清空所有缓存 |

---

## 6. 前端实现方案

### 6.1 缓存管理器类

**创建文件**：`src/static/js/cache-manager.js`

```javascript
class CacheManager {
  constructor() {
    this.storageKeyPrefix = 'chat_session_';
    this.currentSessionId = null;
    this.throttleTimers = {};
    this.pendingUpdates = {};
  }

  /**
   * 初始化缓存（页面加载时调用）
   */
  init(sessionId) {
    this.currentSessionId = sessionId;
    return this.loadSession(sessionId);
  }

  /**
   * 加载会话数据
   */
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

  /**
   * 保存响应块
   */
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

  /**
   * 更新工具调用输出（流式）
   */
  updateToolOutput(blockId, callId, output) {
    const throttleKey = `tool_output_${callId}`;
    if (this.throttleTimers[throttleKey]) {
      clearTimeout(this.throttleTimers[throttleKey]);
    }
    
    // 累积待更新的数据
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

  /**
   * 更新展示状态
   */
  updateDisplayState(state) {
    const sessionData = this._getCurrentSessionData();
    sessionData.display_state = {
      ...sessionData.display_state,
      ...state,
      last_accessed_at: new Date().toISOString()
    };
    this._saveSession(sessionData);
  }

  /**
   * 更新滚动位置（临时存储）
   */
  updateScrollPosition(position) {
    sessionStorage.setItem(`scroll_${this.currentSessionId}`, position.toString());
  }

  /**
   * 获取滚动位置
   */
  getScrollPosition() {
    const saved = sessionStorage.getItem(`scroll_${this.currentSessionId}`);
    return saved ? parseInt(saved, 10) : 0;
  }

  /**
   * 添加工具调用
   */
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

  /**
   * 更新工具调用结果
   */
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

  /**
   * 清除会话缓存
   */
  clearSession(sessionId) {
    const key = this._getStorageKey(sessionId);
    localStorage.removeItem(key);
    sessionStorage.removeItem(`scroll_${sessionId}`);
  }

  /**
   * 清除所有缓存
   */
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

  /**
   * 执行定期清理
   */
  cleanupExpiredSessions() {
    const now = new Date();
    const maxAgeMs = CACHE_CONFIG.max_session_age_days * 24 * 60 * 60 * 1000;
    
    // 获取所有会话缓存键
    const sessionKeys = Object.keys(localStorage).filter(
      key => key.startsWith(this.storageKeyPrefix)
    );
    
    // 按访问时间排序，保留最近的
    const sessions = sessionKeys.map(key => {
      try {
        const data = JSON.parse(localStorage.getItem(key));
        return { key, lastAccess: new Date(data.display_state?.last_accessed_at || 0) };
      } catch {
        return { key, lastAccess: new Date(0) };
      }
    });
    
    // 按最后访问时间排序
    sessions.sort((a, b) => b.lastAccess.getTime() - a.lastAccess.getTime());
    
    // 删除过期和超出数量限制的会话
    sessions.forEach((session, index) => {
      const ageMs = now.getTime() - session.lastAccess.getTime();
      if (ageMs > maxAgeMs || index >= CACHE_CONFIG.max_sessions) {
        localStorage.removeItem(session.key);
        const sessionId = session.key.replace(this.storageKeyPrefix, '');
        sessionStorage.removeItem(`scroll_${sessionId}`);
      }
    });
  }

  // ===== 私有方法 =====
  
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

// 缓存配置常量
const CACHE_CONFIG = {
  max_blocks_per_session: 100,
  max_tool_calls_per_block: 10,
  max_tool_output_length: 10000,
  max_storage_size: 4 * 1024 * 1024,
  max_session_age_days: 30,
  max_sessions: 10
};

// 创建全局实例
window.cacheManager = new CacheManager();
```

### 6.2 页面恢复逻辑

**修改**：`src/static/index.html`

```javascript
// 页面加载时恢复
document.addEventListener('DOMContentLoaded', async () => {
  // 执行定期清理
  window.cacheManager.cleanupExpiredSessions();
  
  // 获取当前会话ID
  const sessionId = getCurrentSessionId();
  
  if (sessionId) {
    // 从缓存加载会话数据
    const sessionData = await window.cacheManager.init(sessionId);
    
    if (sessionData && sessionData.response_blocks.length > 0) {
      // 恢复响应块
      restoreResponseBlocks(sessionData.response_blocks);
      
      // 恢复滚动位置
      const scrollPos = window.cacheManager.getScrollPosition();
      setTimeout(() => {
        document.getElementById('messagesArea').scrollTop = scrollPos;
      }, 100);
    }
  }
});

/**
 * 恢复响应块到页面
 */
function restoreResponseBlocks(blocks) {
  const messagesArea = document.getElementById('messagesArea');
  if (!messagesArea) return;

  blocks.forEach(blockData => {
    // 创建响应块元素
    const blockEl = createResponseBlockFromCache(blockData);
    messagesArea.appendChild(blockEl);
  });
}

/**
 * 从缓存数据创建响应块DOM
 */
function createResponseBlockFromCache(blockData) {
  // 创建响应块容器
  const blockEl = document.createElement('div');
  blockEl.className = 'response-block';
  blockEl.id = `response-${blockData.block_id}`;
  
  // 构建HTML内容
  let html = `
    <div class="response-block-header">
      <span class="response-avatar">🤖</span>
      <span class="response-status">${blockData.status === 'completed' ? '已完成' : '处理中'}</span>
    </div>
    <div class="response-block-content">
  `;
  
  // 思考块
  if (blockData.think_content) {
    html += `
      <div class="think-block ${blockData.think_expanded ? 'expanded' : ''}" id="think-${blockData.block_id}">
        <div class="think-header" onclick="toggleThink(this.parentElement)">
          <span class="think-icon">🧠</span>
          <span class="think-label">思考过程</span>
          <button class="think-copy-btn" onclick="event.stopPropagation(); copyContent(this)">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
              <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
            </svg>
          </button>
          <span class="think-arrow">▼</span>
        </div>
        <div class="think-content" ${blockData.think_expanded ? '' : 'hidden'}>
          <p class="think-text">${escapeHtml(blockData.think_content)}</p>
        </div>
      </div>
    `;
  }
  
  // 文本块
  if (blockData.text_content) {
    html += `
      <div class="text-block" id="text-${blockData.block_id}">
        ${blockData.text_content}
      </div>
    `;
  }
  
  // 工具调用卡片
  if (blockData.tool_calls && blockData.tool_calls.length > 0) {
    html += `<div class="tool-calls-container" id="tools-${blockData.block_id}">`;
    
    blockData.tool_calls.forEach(toolCall => {
      html += `
        <div class="tool-execution-card" id="tool-card-${toolCall.call_id}">
          <div class="tool-card-header">
            <div class="tool-icon-wrapper">
              <span class="tool-icon">🔧</span>
            </div>
            <div class="tool-info">
              <span class="tool-name">${escapeHtml(toolCall.tool_name)}</span>
              <span class="tool-status-badge ${toolCall.status}">${getStatusText(toolCall.status)}</span>
            </div>
            <div class="tool-timestamp">${formatTime(toolCall.started_at)}</div>
          </div>
          
          <!-- 工具调用信息 -->
          <div class="tool-section ${toolCall.arguments_expanded ? 'expanded' : ''}">
            <div class="section-header" onclick="toggleSection(this)">
              <span class="section-title">工具调用</span>
              <span class="section-arrow">▼</span>
            </div>
            <div class="section-content" ${toolCall.arguments_expanded ? '' : 'hidden'}>
              <div class="tool-arguments">
                <div class="arg-label">执行命令：</div>
                <pre class="arg-value">${escapeHtml(JSON.stringify(toolCall.arguments, null, 2))}</pre>
              </div>
            </div>
          </div>
          
          <!-- 工具输出 -->
          <div class="tool-section ${toolCall.output_expanded ? 'expanded' : ''}">
            <div class="section-header" onclick="toggleSection(this)">
              <span class="section-title">执行输出</span>
              <span class="section-arrow">▼</span>
            </div>
            <div class="section-content" ${toolCall.output_expanded ? '' : 'hidden'}>
              <div class="tool-output">
                <pre class="output-content">${escapeHtml(toolCall.output || '')}</pre>
              </div>
            </div>
          </div>
          
          <!-- 工具结果 -->
          <div class="tool-section ${toolCall.result_expanded ? 'expanded' : ''}">
            <div class="section-header" onclick="toggleSection(this)">
              <span class="section-title">执行结果</span>
              <span class="section-arrow">▼</span>
            </div>
            <div class="section-content" ${toolCall.result_expanded ? '' : 'hidden'}>
              <div class="tool-result">
                <div class="result-icon">${toolCall.status === 'completed' ? '✅' : '❌'}</div>
                <div class="result-info">
                  <div class="result-title">${toolCall.result?.message || '无结果'}</div>
                  ${toolCall.result?.return_code !== undefined ? `<div class="result-code">返回码: ${toolCall.result.return_code}</div>` : ''}
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
    });
    
    html += '</div>';
  }
  
  html += '</div>';
  blockEl.innerHTML = html;
  
  return blockEl;
}
```

### 6.3 WebSocket事件缓存

**修改**：`src/static/index.html` 中的事件处理

```javascript
// WebSocket 事件处理
function handleRealtimeEvent(event) {
  const { type, payload } = event;
  
  switch (type) {
    case 'response_block.created': {
      const { block_id, session_id } = payload;
      window.cacheManager.saveResponseBlock(block_id, {
        session_id,
        status: 'in_progress',
        think_content: '',
        text_content: '',
        tool_calls: []
      });
      break;
    }
    
    case 'response_block.think_updated': {
      const { block_id, think_content } = payload;
      window.cacheManager.saveResponseBlock(block_id, { think_content });
      break;
    }
    
    case 'response_block.text_updated': {
      const { block_id, text_content } = payload;
      window.cacheManager.saveResponseBlock(block_id, { text_content });
      break;
    }
    
    case 'tool.call_started': {
      const { block_id, call_id, tool_name, tool_id, arguments } = payload;
      window.cacheManager.addToolCall(block_id, {
        call_id,
        tool_name,
        tool_id,
        arguments,
        arguments_expanded: true,
        output: '',
        output_expanded: false,
        status: 'running',
        result: null,
        result_expanded: true
      });
      break;
    }
    
    case 'tool.execution_output': {
      const { call_id, block_id, output } = payload;
      window.cacheManager.updateToolOutput(block_id, call_id, output);
      break;
    }
    
    case 'tool.call_completed': {
      const { call_id, block_id, success, result } = payload;
      window.cacheManager.updateToolResult(block_id, call_id, { success, result });
      break;
    }
    
    case 'response_block.completed': {
      const { block_id } = payload;
      window.cacheManager.saveResponseBlock(block_id, {
        status: 'completed',
        completed_at: new Date().toISOString()
      });
      break;
    }
  }
}

// 滚动事件监听
document.getElementById('messagesArea')?.addEventListener('scroll', (e) => {
  window.cacheManager.updateScrollPosition(e.target.scrollTop);
});
```

---

## 7. 实施计划

### 7.1 第一阶段：创建缓存管理器（1天）

1. **创建文件**：`src/static/js/cache-manager.js`
2. **实现核心功能**：
   - 会话数据的加载/保存
   - 响应块的增删改查
   - 工具调用的管理
   - 节流写入机制
   - 定期清理策略

### 7.2 第二阶段：集成到现有前端（1天）

1. **修改**：`src/static/index.html`
2. **添加页面恢复逻辑**：
   - DOMContentLoaded 事件中加载缓存
   - 实现 `restoreResponseBlocks` 和 `createResponseBlockFromCache`
3. **集成事件处理**：
   - 在 WebSocket 事件处理中调用缓存管理器
   - 添加滚动事件监听

### 7.3 第三阶段：测试与优化（1天）

1. **功能测试**：
   - 测试页面刷新后恢复
   - 测试切换会话后恢复
   - 测试工具卡片展开/折叠状态恢复
2. **性能优化**：
   - 验证节流机制效果
   - 测试大数据量场景
3. **边界情况处理**：
   - 处理缓存数据损坏
   - 测试存储容量限制

---

## 8. 总结

### 8.1 方案优势

| 优势 | 说明 |
|-----|------|
| **纯前端实现** | 无需后端支持，零服务端改动 |
| **实时缓存** | WebSocket数据实时持久化 |
| **页面恢复** | 刷新后自动恢复完整对话 |
| **容量可控** | 自动清理过期/超限数据 |
| **跨会话支持** | 按会话ID隔离管理 |

### 8.2 注意事项

| 注意事项 | 说明 |
|---------|------|
| **数据安全** | 敏感数据可能被浏览器缓存，建议HTTPS |
| **跨浏览器** | 不同浏览器缓存独立 |
| **存储限制** | localStorage约5MB，需控制数据量 |
| **隐私保护** | 用户清除浏览器数据会丢失缓存 |

### 8.3 后续优化方向

1. **数据压缩**：对大文本内容进行压缩存储
2. **智能清理**：根据使用频率动态调整保留策略
3. **导出功能**：支持用户导出对话数据
4. **同步提示**：提示用户定期导出重要数据

---

**文档版本**: v2.0（纯前端缓存方案）  
**创建日期**: 2026-05-20  
**适用项目**: Trae AI Assistant  
**作者**: Trae AI Team