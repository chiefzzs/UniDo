(() => {
  // js/components/infrastructure/EventBus.js
  var EventBus = {
    listeners: /* @__PURE__ */ new Map(),
    conditionalListeners: /* @__PURE__ */ new Map(),
    // 事件缓存 - 用于处理时序问题：事件可能在订阅者订阅之前到达
    _eventCache: /* @__PURE__ */ new Map(),
    _maxCacheSize: 100,
    // 追踪统计
    _stats: {
      emitted: 0,
      consumed: 0,
      dropped: 0,
      componentCreations: 0,
      componentUpdates: 0
    },
    // 已注册的订阅者信息（用于追踪）
    _subscribers: /* @__PURE__ */ new Map(),
    // 已配置为抛弃的事件列表（这些事件不需要处理）
    droppedMessages: [
      "round.created",
      "event.round.created",
      "round.started",
      "round.completed",
      "event.round.completed",
      "project:loaded",
      "project:loading",
      "ws:connected",
      "llm.request_prepared",
      "llm.response_received",
      "component:user-message-created",
      "component:assistant-message-created",
      "component:response-block-created",
      "session:loading",
      "event.session.created"
    ],
    // 规定要订阅的事件列表（订阅关系表中定义的事件）
    subscribedEvents: [
      "event.session.created",
      "event.client.message_received",
      "event.dialog.created",
      "event.llm.request_sent",
      "event.llm.call_thinking_completed",
      "event.llm.call_reasoning_completed",
      "event.llm.call_text_completed",
      "event.tool.call_started",
      "event.llm.call_text_streaming",
      "event.llm.call_thinking_streaming",
      "event.llm.call_reasoning_streaming",
      "event.tool.execution_output",
      "event.llm.call_text_completed_end",
      "event.llm.call_thinking_completed_end",
      "event.llm.call_reasoning_completed_end",
      "event.llm.call_completed_end",
      "event.tool.execution_output_end",
      "event.tool.call_completed_end"
    ],
    // 发布事件
    emit(eventType, payload) {
      this._stats.emitted++;
      const startTime = Date.now();
      const action = payload?.action || payload?.type || "";
      const normalCount = this.listeners.has(eventType) ? this.listeners.get(eventType).length : 0;
      const conditionalCount = this.conditionalListeners.has(eventType) ? this.conditionalListeners.get(eventType).length : 0;
      console.log(`%c[EventBus] \u{1F4E4} \u53D1\u5E03\u4E8B\u4EF6: ${eventType} action=${action}`, "color: #2196F3; font-weight: bold");
      console.log(`%c[EventBus]   \u251C\u2500\u2500 \u666E\u901A\u8BA2\u9605\u8005\u6570: ${normalCount}`, "color: #2196F3");
      console.log(`%c[EventBus]   \u2514\u2500\u2500 \u6761\u4EF6\u8BA2\u9605\u8005\u6570: ${conditionalCount}`, "color: #2196F3");
      let totalConsumed = 0;
      let consumers = [];
      if (this.listeners.has(eventType)) {
        const handlers = this.listeners.get(eventType);
        handlers.forEach((handler, index) => {
          const subscriberInfo = this._getSubscriberInfo(eventType, index, "normal");
          const subscriberName = subscriberInfo.name;
          try {
            if (subscriberName !== "\u533F\u540D\u8BA2\u9605\u8005") {
              console.log(`%c[EventBus]   \u2514\u2500\u2500 \u{1F504} \u6D88\u8D39\u4E2D: ${subscriberName} action=${action}`, "color: #4CAF50");
            }
            handler(payload);
            totalConsumed++;
            consumers.push(subscriberName || "\u533F\u540D\u8BA2\u9605\u8005");
            if (subscriberName !== "\u533F\u540D\u8BA2\u9605\u8005") {
              console.log(`%c[EventBus]   \u2514\u2500\u2500 \u2705 \u5DF2\u6D88\u8D39: ${subscriberName} action=${action}`, "color: #4CAF50");
            }
          } catch (e) {
            console.error(`%c[EventBus]   \u2514\u2500\u2500 \u274C \u6D88\u8D39\u5931\u8D25: ${subscriberName || "\u533F\u540D\u8BA2\u9605\u8005"} action=${action}`, "color: #F44336", e);
          }
        });
      }
      if (this.conditionalListeners.has(eventType)) {
        this.conditionalListeners.get(eventType).forEach((listener, index) => {
          const subscriberInfo = this._getSubscriberInfo(eventType, index, "conditional");
          const subscriberName = subscriberInfo.name;
          try {
            if (listener.condition(payload)) {
              if (subscriberName !== "\u533F\u540D\u8BA2\u9605\u8005") {
                console.log(`%c[EventBus]   \u2514\u2500\u2500 \u{1F504} \u6761\u4EF6\u6D88\u8D39\u4E2D: ${subscriberName} action=${action}`, "color: #FF9800");
              }
              listener.handler(payload);
              totalConsumed++;
              consumers.push(subscriberName || "\u533F\u540D\u8BA2\u9605\u8005");
              if (subscriberName !== "\u533F\u540D\u8BA2\u9605\u8005") {
                console.log(`%c[EventBus]   \u2514\u2500\u2500 \u2705 \u6761\u4EF6\u5339\u914D\u5E76\u6D88\u8D39: ${subscriberName} action=${action}`, "color: #FF9800");
              }
            } else {
              if (subscriberName !== "\u533F\u540D\u8BA2\u9605\u8005") {
                console.log(`%c[EventBus]   \u2514\u2500\u2500 \u23ED\uFE0F \u6761\u4EF6\u4E0D\u5339\u914D\u8DF3\u8FC7: ${subscriberName} action=${action}`, "color: #9E9E9E");
              }
            }
          } catch (e) {
            console.error(`%c[EventBus]   \u2514\u2500\u2500 \u274C \u6761\u4EF6\u6D88\u8D39\u5931\u8D25: ${subscriberName || "\u533F\u540D\u8BA2\u9605\u8005"} action=${action}`, "color: #F44336", e);
          }
        });
      }
      this._stats.consumed += totalConsumed;
      if (totalConsumed === 0) {
        if (this.subscribedEvents.includes(eventType)) {
          this._cacheEvent(eventType, payload);
          console.log(`%c[EventBus] \u{1F4E6} \u4E8B\u4EF6 ${eventType} action=${action} \u6682\u5B58\u5230\u7F13\u5B58`, "color: #FF9800");
        } else {
          this._stats.dropped++;
          if (this.droppedMessages.includes(eventType)) {
            console.log(`[EventBus] \u4E8B\u4EF6 ${eventType} action=${action} \u65E0\u4EBA\u8BA2\u9605\uFF0C\u5DF2\u629B\u5F03`);
          } else {
            console.warn(`%c[EventBus] \u26A0\uFE0F \u4E8B\u4EF6 ${eventType} action=${action} \u65E0\u4EBA\u8BA2\u9605\uFF0C\u5DF2\u629B\u5F03\uFF08\u53EF\u80FD\u9700\u8981\u6DFB\u52A0\u5230\u8BA2\u9605\u5173\u7CFB\u8868\uFF09`, "color: #FFC107; font-weight: bold");
          }
        }
      } else {
        const namedConsumers = consumers.filter((c) => c !== "\u533F\u540D\u8BA2\u9605\u8005");
        if (namedConsumers.length > 0) {
          console.log(`%c[EventBus] \u2705 \u4E8B\u4EF6 ${eventType} action=${action} \u5DF2\u88AB ${namedConsumers.join(", ")} \u6D88\u8D39 (\u8017\u65F6: ${Date.now() - startTime}ms)`, "color: #4CAF50");
        }
      }
    },
    // 订阅事件
    on(eventType, handler, subscriberName = "\u533F\u540D\u8BA2\u9605\u8005") {
      if (!this.listeners.has(eventType)) {
        this.listeners.set(eventType, []);
      }
      this.listeners.get(eventType).push(handler);
      if (!this._subscribers.has(eventType)) {
        this._subscribers.set(eventType, []);
      }
      this._subscribers.get(eventType).push({
        type: "normal",
        name: subscriberName,
        handler
      });
      console.log(`%c[EventBus] \u{1F4E5} \u8BA2\u9605\u4E8B\u4EF6: ${eventType} (\u8BA2\u9605\u8005: ${subscriberName}, \u5F53\u524D\u8BA2\u9605\u8005\u6570: ${this.listeners.get(eventType).length})`, "color: #9C27B0");
      this._processCachedEvents(eventType, (payload) => handler(payload));
    },
    // 带条件的订阅
    onConditional(eventType, condition, handler, subscriberName = "\u533F\u540D\u8BA2\u9605\u8005") {
      if (!this.conditionalListeners.has(eventType)) {
        this.conditionalListeners.set(eventType, []);
      }
      const listener = {
        condition,
        handler,
        id: Date.now() + Math.random(),
        subscriberName
      };
      this.conditionalListeners.get(eventType).push(listener);
      if (!this._subscribers.has(eventType)) {
        this._subscribers.set(eventType, []);
      }
      this._subscribers.get(eventType).push({
        type: "conditional",
        name: subscriberName,
        handler,
        id: listener.id
      });
      console.log(`%c[EventBus] \u{1F4E5} \u6761\u4EF6\u8BA2\u9605\u4E8B\u4EF6: ${eventType} (\u8BA2\u9605\u8005: ${subscriberName}, \u5F53\u524D\u8BA2\u9605\u8005\u6570: ${this.conditionalListeners.get(eventType).length})`, "color: #FF9800");
      this._processCachedEvents(eventType, (payload) => {
        if (condition(payload)) {
          handler(payload);
        }
      });
    },
    // 获取订阅者信息
    _getSubscriberInfo(eventType, index, type) {
      if (this._subscribers.has(eventType)) {
        const subscribers = this._subscribers.get(eventType);
        const filtered = subscribers.filter((s) => s.type === type);
        if (filtered[index]) {
          return filtered[index];
        }
      }
      return { name: `\u533F\u540D${type === "conditional" ? "\u6761\u4EF6" : ""}\u8BA2\u9605\u8005_${index}` };
    },
    // 取消订阅
    off(eventType, handler) {
      if (this.listeners.has(eventType)) {
        const handlers = this.listeners.get(eventType);
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
          if (this._subscribers.has(eventType)) {
            const subscribers = this._subscribers.get(eventType);
            const subIndex = subscribers.findIndex((s) => s.handler === handler);
            if (subIndex > -1) {
              console.log(`%c[EventBus] \u{1F6AB} \u53D6\u6D88\u8BA2\u9605: ${eventType} (\u8BA2\u9605\u8005: ${subscribers[subIndex].name})`, "color: #F44336");
              subscribers.splice(subIndex, 1);
            }
          }
        }
      }
    },
    // 取消带条件的订阅（通过handler或id）
    offConditional(eventType, handlerOrId) {
      if (this.conditionalListeners.has(eventType)) {
        const listeners = this.conditionalListeners.get(eventType);
        const filtered = listeners.filter((listener) => {
          if (typeof handlerOrId === "function") {
            if (listener.handler === handlerOrId) {
              console.log(`%c[EventBus] \u{1F6AB} \u53D6\u6D88\u6761\u4EF6\u8BA2\u9605: ${eventType} (\u8BA2\u9605\u8005: ${listener.subscriberName})`, "color: #F44336");
            }
            return listener.handler !== handlerOrId;
          } else {
            if (listener.id === handlerOrId) {
              console.log(`%c[EventBus] \u{1F6AB} \u53D6\u6D88\u6761\u4EF6\u8BA2\u9605: ${eventType} (\u8BA2\u9605\u8005: ${listener.subscriberName})`, "color: #F44336");
            }
            return listener.id !== handlerOrId;
          }
        });
        this.conditionalListeners.set(eventType, filtered);
      }
    },
    // 一次性订阅
    once(eventType, handler, subscriberName = "\u533F\u540D\u8BA2\u9605\u8005") {
      const wrappedHandler = (payload) => {
        handler(payload);
        this.off(eventType, wrappedHandler);
      };
      this.on(eventType, wrappedHandler, subscriberName);
    },
    // 一次性带条件订阅（处理完后自动取消订阅）
    onceConditional(eventType, condition, handler, subscriberName = "\u533F\u540D\u8BA2\u9605\u8005") {
      const listener = {
        condition,
        handler,
        id: Date.now() + Math.random(),
        subscriberName
      };
      const wrappedHandler = (payload) => {
        if (condition(payload)) {
          try {
            handler(payload);
          } catch (e) {
            console.error(`[EventBus] Once conditional handler error (${eventType}):`, e);
          }
          this.offConditional(eventType, listener.id);
        }
      };
      if (!this.conditionalListeners.has(eventType)) {
        this.conditionalListeners.set(eventType, []);
      }
      listener.handler = wrappedHandler;
      this.conditionalListeners.get(eventType).push(listener);
      if (!this._subscribers.has(eventType)) {
        this._subscribers.set(eventType, []);
      }
      this._subscribers.get(eventType).push({
        type: "conditional_once",
        name: subscriberName,
        handler: wrappedHandler,
        id: listener.id
      });
      if (this.subscribedEvents.includes(eventType)) {
        console.log(`%c[EventBus] \u{1F4E5} \u4E00\u6B21\u6027\u6761\u4EF6\u8BA2\u9605: ${eventType} (\u8BA2\u9605\u8005: ${subscriberName})`, "color: #9C27B0");
      } else {
        console.log(`[EventBus] \u{1F4E5} \u4E00\u6B21\u6027\u6761\u4EF6\u8BA2\u9605: ${eventType} (\u8BA2\u9605\u8005: ${subscriberName}) [\u975E\u8BA2\u9605\u5173\u7CFB\u8868\u5B9A\u4E49]`);
      }
      return listener.id;
    },
    // 记录组件创建
    trackComponentCreation(parentName, childName, details = {}) {
      this._stats.componentCreations++;
      console.log(`%c[EventBus] \u{1F476} \u7EC4\u4EF6\u521B\u5EFA: ${parentName} \u2192 ${childName}`, "color: #00BCD4; font-weight: bold", details);
    },
    // 记录组件更新
    trackComponentUpdate(componentName, updateType, details = {}) {
      this._stats.componentUpdates++;
      console.log(`%c[EventBus] \u{1F504} \u7EC4\u4EF6\u66F4\u65B0: ${componentName} (${updateType})`, "color: #8BC34A", details);
    },
    // 记录异常抛弃（设计应该被消费但没有被消费）
    trackUnexpectedDrop(eventType, expectedConsumers, payload) {
      console.error(`%c[EventBus] \u274C \u5F02\u5E38\u629B\u5F03: ${eventType}`, "color: #F44336; font-weight: bold");
      console.error(`   \u671F\u671B\u6D88\u8D39\u8005: ${expectedConsumers.join(", ")}`);
      console.error(`   \u5B9E\u9645\u6D88\u8D39\u8005: \u65E0`);
      console.error(`   \u6D88\u606F\u5185\u5BB9:`, payload);
    },
    // 获取统计信息
    getStats() {
      return { ...this._stats };
    },
    // 打印统计摘要
    printStats() {
      console.log(`%c[EventBus] \u{1F4CA} \u6D88\u606F\u7EDF\u8BA1\u6458\u8981`, "color: #333; font-weight: bold; font-size: 14px");
      console.log(`   \u53D1\u5E03\u4E8B\u4EF6: ${this._stats.emitted}`);
      console.log(`   \u6D88\u8D39\u4E8B\u4EF6: ${this._stats.consumed}`);
      console.log(`   \u629B\u5F03\u4E8B\u4EF6: ${this._stats.dropped}`);
      console.log(`   \u521B\u5EFA\u7EC4\u4EF6: ${this._stats.componentCreations}`);
      console.log(`   \u66F4\u65B0\u7EC4\u4EF6: ${this._stats.componentUpdates}`);
    },
    // 缓存事件（用于处理时序问题）
    _cacheEvent(eventType, payload) {
      if (!this._eventCache.has(eventType)) {
        this._eventCache.set(eventType, []);
      }
      const cache = this._eventCache.get(eventType);
      if (cache.length >= this._maxCacheSize) {
        cache.shift();
      }
      cache.push({
        payload,
        timestamp: Date.now()
      });
    },
    // 处理缓存的事件
    _processCachedEvents(eventType, handler) {
      if (!this._eventCache.has(eventType)) {
        return;
      }
      const cache = this._eventCache.get(eventType);
      const processedIndices = [];
      for (let i = 0; i < cache.length; i++) {
        try {
          handler(cache[i].payload);
          processedIndices.push(i);
          console.log(`%c[EventBus] \u{1F3AF} \u5904\u7406\u7F13\u5B58\u4E8B\u4EF6: ${eventType}`, "color: #8BC34A");
        } catch (e) {
          console.error(`%c[EventBus] \u274C \u5904\u7406\u7F13\u5B58\u4E8B\u4EF6\u5931\u8D25: ${eventType}`, "color: #F44336", e);
        }
      }
      for (let i = processedIndices.length - 1; i >= 0; i--) {
        cache.splice(processedIndices[i], 1);
      }
    },
    // 清空所有监听器
    clear() {
      console.log(`%c[EventBus] \u{1F9F9} \u6E05\u7A7A\u6240\u6709\u76D1\u542C\u5668`, "color: #9E9E9E");
      this.listeners.clear();
      this.conditionalListeners.clear();
      this._subscribers.clear();
      this._eventCache.clear();
      this._stats = {
        emitted: 0,
        consumed: 0,
        dropped: 0,
        componentCreations: 0,
        componentUpdates: 0
      };
    }
  };
  window.EventBus = EventBus;

  // js/components/infrastructure/StateManager.js
  var StateManager = {
    state: {
      // 连接状态
      wsConnected: false,
      clientId: null,
      // 菜单状态
      menus: [
        { id: "chat", label: "\u5BF9\u8BDD", icon: "\u{1F4AC}", page: "chat", sortOrder: 0 },
        { id: "projects", label: "\u9879\u76EE", icon: "\u{1F4C1}", page: "projects", sortOrder: 1 },
        { id: "workspaces", label: "\u5DE5\u4F5C\u533A", icon: "\u{1F4C2}", page: "workspaces", sortOrder: 2 },
        { id: "models", label: "\u6A21\u578B", icon: "\u{1F916}", page: "models", sortOrder: 3 },
        { id: "tools", label: "\u5DE5\u5177", icon: "\u{1F527}", page: "tools", sortOrder: 4 },
        { id: "prompts", label: "\u63D0\u793A\u8BCD", icon: "\u{1F4DD}", page: "prompts", sortOrder: 5 },
        { id: "storage", label: "\u5B58\u50A8\u914D\u7F6E", icon: "\u{1F4BE}", page: "storage", sortOrder: 6 }
      ],
      activeMenuId: "chat",
      // UI 状态
      currentPage: "chat",
      theme: "dark",
      replayEnabled: false,
      replayMode: "off",
      replaySpeed: "normal",
      // 项目状态
      projects: [],
      currentProjectId: null,
      projectsLoading: false,
      // 会话状态
      sessions: [],
      currentSessionId: null,
      sessionsLoading: false,
      // 消息状态
      messages: [],
      // 响应块状态
      responseBlocks: /* @__PURE__ */ new Map(),
      currentResponseBlockId: null,
      // 工具调用状态
      pendingToolCalls: /* @__PURE__ */ new Map(),
      toolCallIdMap: /* @__PURE__ */ new Map(),
      // 生成状态（用于控制发送按钮）
      isGenerating: false,
      // 错误信息
      lastError: null
    },
    listeners: /* @__PURE__ */ new Map(),
    // 获取状态
    getState(key) {
      return key ? this.state[key] : this.state;
    },
    // 设置状态
    setState(key, value) {
      const oldValue = this.state[key];
      this.state[key] = value;
      console.log(`[State] ${key}:`, oldValue, "\u2192", value);
      this.notify(key, value, oldValue);
      if (typeof window !== "undefined" && window.EventBus) {
        window.EventBus.emit("state:updated", { key, value, oldValue });
      }
    },
    // 批量设置状态
    setStates(states) {
      Object.entries(states).forEach(([key, value]) => {
        this.setState(key, value);
      });
    },
    // 订阅状态变更
    subscribe(key, listener) {
      if (!this.listeners.has(key)) {
        this.listeners.set(key, /* @__PURE__ */ new Set());
      }
      this.listeners.get(key).add(listener);
      return () => this.listeners.get(key).delete(listener);
    },
    // 通知状态变更
    notify(key, newValue, oldValue) {
      if (this.listeners.has(key)) {
        this.listeners.get(key).forEach((listener) => {
          try {
            listener(newValue, oldValue);
          } catch (e) {
            console.error(`[State] Subscriber error (${key}):`, e);
          }
        });
      }
    }
  };
  window.StateManager = StateManager;

  // js/components/infrastructure/ApiClient.js
  var ApiClient = {
    baseUrl: "/api",
    async request(method, endpoint, data = null) {
      const url = `${this.baseUrl}${endpoint}`;
      const options = {
        method,
        headers: { "Content-Type": "application/json" }
      };
      if (data) {
        options.body = JSON.stringify(data);
      }
      const response = await fetch(url, options);
      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: "Request failed" }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }
      return response.json();
    },
    get(endpoint) {
      return this.request("GET", endpoint);
    },
    post(endpoint, data) {
      return this.request("POST", endpoint, data);
    },
    put(endpoint, data) {
      return this.request("PUT", endpoint, data);
    },
    delete(endpoint) {
      return this.request("DELETE", endpoint);
    }
  };
  window.ApiClient = ApiClient;

  // js/components/infrastructure/WSClient.js
  var WSClient2 = {
    socket: null,
    url: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,
    reconnectDelay: 1e3,
    heartbeatInterval: null,
    listeners: /* @__PURE__ */ new Map(),
    // 连接 WebSocket
    connect() {
      return new Promise((resolve, reject) => {
        const clientId = "client-" + Math.random().toString(36).substr(2, 9);
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        this.url = `${protocol}//${window.location.host}/ws/${clientId}`;
        console.log("[WS] Connecting to:", this.url);
        this.socket = new WebSocket(this.url);
        this.socket.onopen = () => {
          console.log("[WS] Connected");
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          EventBus.emit("ws:connected", { clientId });
          StateManager.setState("wsConnected", true);
          StateManager.setState("clientId", clientId);
          resolve();
        };
        this.socket.onclose = (event) => {
          console.log("[WS] Disconnected:", event.code, event.reason);
          this.stopHeartbeat();
          EventBus.emit("ws:disconnected", { code: event.code, reason: event.reason });
          StateManager.setState("wsConnected", false);
          this.handleReconnect();
        };
        this.socket.onerror = (error) => {
          console.error("[WS] Error:", error);
          EventBus.emit("ws:error", { error });
          reject(error);
        };
        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            EventBus.emit("ws:message", data);
          } catch (e) {
            console.error("[WS] Parse error:", e);
          }
        };
      });
    },
    // 发送消息
    send(action, data) {
      console.log(`%c[WS] \u{1F4E4} \u5C1D\u8BD5\u53D1\u9001\u6D88\u606F: action=${action}`, "color: #2196F3; font-weight: bold");
      console.log(`%c[WS] \u{1F50D} Socket\u72B6\u6001: ${this.socket ? `readyState=${this.socket.readyState} (${this._getStateText(this.socket.readyState)})` : "null"}`, "color: #607D8B");
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const message = JSON.stringify({ action, data });
        console.log(`%c[WS] \u2705 \u53D1\u9001\u6D88\u606F\u6210\u529F: ${message.substring(0, 200)}${message.length > 200 ? "..." : ""}`, "color: #4CAF50");
        this.socket.send(message);
        return true;
      }
      console.error(`%c[WS] \u274C \u53D1\u9001\u5931\u8D25\uFF0Csocket\u672A\u8FDE\u63A5`, "color: #F44336; font-weight: bold");
      console.log(`%c[WS] \u{1F4CA} Socket\u8BE6\u60C5: socket=${!!this.socket}, readyState=${this.socket?.readyState}`, "color: #607D8B");
      return false;
    },
    _getStateText(state) {
      const states = {
        0: "CONNECTING",
        1: "OPEN",
        2: "CLOSING",
        3: "CLOSED"
      };
      return states[state] || "UNKNOWN";
    },
    // 发送对话消息
    sendMessage(sessionId, content) {
      return this.send("send_message", { session_id: sessionId, content });
    },
    // 发送会话切换消息（触发后端历史回放）
    sendSessionSwitch(sessionId) {
      return this.send("switch_session", { session_id: sessionId });
    },
    // 发送自定义消息（直接发送完整payload）
    sendCustomMessage(payload) {
      console.log(`%c[WS] \u{1F4E4} \u5C1D\u8BD5\u53D1\u9001\u81EA\u5B9A\u4E49\u6D88\u606F`, "color: #2196F3; font-weight: bold");
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        const message = JSON.stringify(payload);
        console.log(`%c[WS] \u2705 \u53D1\u9001\u81EA\u5B9A\u4E49\u6D88\u606F\u6210\u529F: ${message.substring(0, 200)}${message.length > 200 ? "..." : ""}`, "color: #4CAF50");
        this.socket.send(message);
        return true;
      }
      console.error(`%c[WS] \u274C \u53D1\u9001\u5931\u8D25\uFF0Csocket\u672A\u8FDE\u63A5`, "color: #F44336; font-weight: bold");
      return false;
    },
    // 心跳检测
    startHeartbeat() {
      this.heartbeatInterval = setInterval(() => {
        this.send("ping", {});
      }, 3e4);
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
        console.error("[WS] Max reconnect attempts reached");
        EventBus.emit("ws:reconnect-failed", {});
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
  window.WSClient = WSClient2;

  // js/components/infrastructure/PageRouter.js
  var PageRouter = {
    // 路由映射表
    routeMap: {
      "chat": { component: "ChatPageComponent", label: "\u5BF9\u8BDD" },
      "projects": { component: "ProjectPageComponent", label: "\u9879\u76EE\u7BA1\u7406" },
      "workspaces": { component: "WorkspacePageComponent", label: "\u5DE5\u4F5C\u533A\u7BA1\u7406" },
      "models": { component: "ModelPageComponent", label: "\u6A21\u578B\u914D\u7F6E" },
      "tools": { component: "ToolPageComponent", label: "\u5DE5\u5177\u7BA1\u7406" },
      "prompts": { component: "PromptPageComponent", label: "\u63D0\u793A\u8BCD\u7BA1\u7406" },
      "storage": { component: "StoragePageComponent", label: "\u5B58\u50A8\u914D\u7F6E" }
    },
    // 初始化路由
    init() {
      const hash = window.location.hash.replace("#", "");
      const initialPage = hash || StateManager.getState("currentPage") || "chat";
      StateManager.setState("currentPage", initialPage);
      EventBus.on("menu:click", ({ menu }) => {
        this.navigateTo(menu.page);
      });
      window.addEventListener("hashchange", () => {
        const hash2 = window.location.hash.replace("#", "");
        if (hash2 && hash2 !== StateManager.getState("currentPage")) {
          StateManager.setState("currentPage", hash2);
          EventBus.emit("page:change", { page: hash2 });
        }
      });
      console.log("[PageRouter] Initialized, current page:", initialPage);
    },
    // 导航到指定页面
    navigateTo(page) {
      if (!page || page === StateManager.getState("currentPage"))
        return;
      StateManager.setState("currentPage", page);
      window.location.hash = page;
      EventBus.emit("page:change", { page });
    },
    // 获取当前页面
    getCurrentPage() {
      return StateManager.getState("currentPage");
    },
    // 获取路由配置
    getRoute(page) {
      return this.routeMap[page];
    },
    // 检查页面是否激活
    isPageActive(page) {
      return StateManager.getState("currentPage") === page;
    }
  };
  window.PageRouter = PageRouter;

  // js/components/infrastructure/DataNormalizer.js
  var DataNormalizer = {
    /**
     * 规范化项目数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeProject(data) {
      if (Array.isArray(data)) {
        return data.map((item) => this._normalizeProjectItem(item));
      }
      return this._normalizeProjectItem(data);
    },
    _normalizeProjectItem(item) {
      if (!item)
        return item;
      return {
        ...item,
        id: item.id || item.project_id || ""
      };
    },
    /**
     * 规范化工作区数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeWorkspace(data) {
      if (Array.isArray(data)) {
        return data.map((item) => this._normalizeWorkspaceItem(item));
      }
      return this._normalizeWorkspaceItem(data);
    },
    _normalizeWorkspaceItem(item) {
      if (!item)
        return item;
      return {
        ...item,
        id: item.id || item.config_id || ""
      };
    },
    /**
     * 规范化模型配置数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeModel(data) {
      if (Array.isArray(data)) {
        return data.map((item) => this._normalizeModelItem(item));
      }
      return this._normalizeModelItem(data);
    },
    _normalizeModelItem(item) {
      if (!item)
        return item;
      return {
        ...item,
        id: item.id || item.config_id || ""
      };
    },
    /**
     * 规范化工具配置数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeTool(data) {
      if (Array.isArray(data)) {
        return data.map((item) => this._normalizeToolItem(item));
      }
      return this._normalizeToolItem(data);
    },
    _normalizeToolItem(item) {
      if (!item)
        return item;
      return {
        ...item,
        id: item.id || item.tool_id || item.config_id || "",
        name: item.name || item.tool_name || "",
        type: item.type || item.category || "",
        status: item.status || (item.is_active !== void 0 ? item.is_active ? "active" : "inactive" : "inactive"),
        supported_os: item.supported_os || [],
        supported_terminals: item.supported_terminals || []
      };
    },
    /**
     * 规范化存储配置数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeStorage(data) {
      if (Array.isArray(data)) {
        return data.map((item) => this._normalizeStorageItem(item));
      }
      return this._normalizeStorageItem(data);
    },
    _normalizeStorageItem(item) {
      if (!item)
        return item;
      return {
        ...item,
        id: item.id || item.config_id || ""
      };
    },
    /**
     * 通用规范化方法
     * @param {Object|Array} data - 原始数据
     * @param {string} type - 数据类型: 'project', 'workspace', 'model', 'tool', 'storage'
     * @returns {Object|Array} - 规范化后的数据
     */
    normalize(data, type) {
      switch (type) {
        case "project":
          return this.normalizeProject(data);
        case "workspace":
          return this.normalizeWorkspace(data);
        case "model":
          return this.normalizeModel(data);
        case "tool":
          return this.normalizeTool(data);
        case "storage":
          return this.normalizeStorage(data);
        default:
          return data;
      }
    },
    /**
     * 解析API响应数据
     * @param {Object|Array} result - API响应结果
     * @param {string} dataField - 数据字段名（如 'projects', 'data'）
     * @returns {Array} - 数据数组
     */
    parseResponse(result, dataField) {
      if (Array.isArray(result)) {
        return result;
      } else if (result && result.data && Array.isArray(result.data)) {
        return result.data;
      } else if (result && result[dataField] && Array.isArray(result[dataField])) {
        return result[dataField];
      }
      return [];
    }
  };
  window.DataNormalizer = DataNormalizer;

  // js/components/services/ProjectManager.js
  var ProjectManager = {
    api: ApiClient,
    // 获取项目列表
    async getProjects(params = {}) {
      EventBus.emit("project:loading", { loading: true });
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/projects" + (query ? "?" + query : ""));
        const rawData = DataNormalizer.parseResponse(result, "projects");
        const projects = DataNormalizer.normalizeProject(rawData);
        console.log("[ProjectManager] Raw result:", result);
        console.log("[ProjectManager] Parsed projects:", projects);
        console.log("[ProjectManager] First project id:", projects[0]?.id);
        StateManager.setState("projects", projects);
        StateManager.setState("projectsLoading", false);
        EventBus.emit("project:loaded", { projects, total: projects.length });
        return projects;
      } catch (error) {
        console.error("[ProjectManager] Error loading projects:", error);
        StateManager.setState("projectsLoading", false);
        EventBus.emit("project:error", { error: error.message });
        throw error;
      }
    },
    // 创建项目
    async createProject(data) {
      EventBus.emit("project:loading");
      try {
        const result = await this.api.post("/projects", data);
        const project = DataNormalizer.normalizeProject(result);
        EventBus.emit("project:created", { project });
        return project;
      } catch (error) {
        EventBus.emit("project:error", { error: error.message });
        throw error;
      }
    },
    // 更新项目
    async updateProject(projectId, data) {
      try {
        const result = await this.api.put(`/projects/${projectId}`, data);
        const project = DataNormalizer.normalizeProject(result);
        EventBus.emit("project:updated", { project });
        return project;
      } catch (error) {
        EventBus.emit("project:error", { error: error.message });
        throw error;
      }
    },
    // 删除项目
    async deleteProject(projectId) {
      try {
        await this.api.delete(`/projects/${projectId}`);
        const projects = StateManager.getState("projects") || [];
        StateManager.setState("projects", projects.filter((p) => p.id !== projectId));
        EventBus.emit("project:deleted", { id: projectId });
      } catch (error) {
        EventBus.emit("project:error", { error: error.message });
        throw error;
      }
    },
    // 批量删除
    async batchDelete(ids) {
      try {
        await this.api.post("/projects/batch-delete", { ids });
        const projects = StateManager.getState("projects") || [];
        StateManager.setState("projects", projects.filter((p) => !ids.includes(p.id)));
        EventBus.emit("project:deleted", { ids });
      } catch (error) {
        EventBus.emit("project:error", { error: error.message });
        throw error;
      }
    }
  };
  window.ProjectManager = ProjectManager;

  // js/components/services/SessionManager.js
  var SessionManager = {
    api: ApiClient,
    wsClient: WSClient2,
    // 获取会话列表
    async getSessions(projectId) {
      EventBus.emit("session:loading");
      try {
        const url = `/projects/${projectId}/sessions`;
        console.log("[SessionManager] GET request URL:", url);
        const result = await this.api.get(url);
        console.log("[SessionManager] Raw response:", result);
        console.log("[SessionManager] Response type:", typeof result);
        const rawData = DataNormalizer.parseResponse(result, "sessions");
        const sessions = rawData.map((session) => ({
          ...session,
          id: session.id || session.session_id || ""
        }));
        console.log("[SessionManager] Parsed sessions:", sessions);
        console.log("[SessionManager] Sessions count:", sessions.length);
        StateManager.setState("sessions", sessions);
        EventBus.emit("session:loaded", { sessions });
        return sessions;
      } catch (error) {
        console.error("[SessionManager] Error loading sessions:", error);
        EventBus.emit("session:error", { error: error.message });
        throw error;
      }
    },
    // 创建会话
    async createSession(projectId, title = "\u65B0\u4F1A\u8BDD") {
      try {
        const url = `/projects/${projectId}/sessions`;
        console.log("[SessionManager] POST request URL:", url);
        const result = await this.api.post(url, { title });
        console.log("[SessionManager] Create session response:", result);
        const sessionId = result.id || result.session_id || result.data?.id || result.data?.session_id;
        console.log("[SessionManager] New session ID:", sessionId);
        await this.getSessions(projectId);
        if (sessionId) {
          await this.switchSession(sessionId);
        } else {
          console.warn("[SessionManager] Could not get session ID from response");
        }
        EventBus.emit("session:created", { sessionId, title });
        return result;
      } catch (error) {
        console.error("[SessionManager] Error creating session:", error);
        EventBus.emit("session:error", { error: error.message });
        throw error;
      }
    },
    // 切换会话
    async switchSession(sessionId) {
      if (!sessionId) {
        console.error("[SessionManager] switchSession called with undefined/null sessionId");
        EventBus.emit("session:error", { error: "Invalid session ID" });
        return;
      }
      console.log("\n=== [SessionManager] Switching to session ===");
      console.log("[SessionManager] Session ID:", sessionId);
      const wsConnected = StateManager.getState("wsConnected");
      console.log("[SessionManager] WebSocket connected:", wsConnected);
      if (!wsConnected) {
        console.warn("[SessionManager] WebSocket not connected, will retry after connection");
        const handleConnected = () => {
          this._performSessionSwitch(sessionId);
          EventBus.off("ws:connected", handleConnected);
        };
        EventBus.on("ws:connected", handleConnected);
        return;
      }
      this._performSessionSwitch(sessionId);
    },
    // 执行会话切换（内部方法）
    _performSessionSwitch(sessionId) {
      StateManager.setState("messages", []);
      StateManager.setState("currentSessionId", sessionId);
      const success = this.wsClient.sendSessionSwitch(sessionId);
      if (success) {
        console.log("[SessionManager] Session switch message sent successfully");
      } else {
        console.error("[SessionManager] Failed to send session switch message");
        EventBus.emit("session:error", { error: "Failed to send session switch message" });
      }
      EventBus.emit("session:switching", { sessionId });
    },
    // 删除会话
    async deleteSession(sessionId) {
      if (!sessionId) {
        console.error("[SessionManager] deleteSession called with undefined/null sessionId");
        return;
      }
      try {
        await this.api.delete(`/sessions/${sessionId}`);
        const currentProjectId = StateManager.getState("currentProjectId");
        if (currentProjectId) {
          await this.getSessions(currentProjectId);
        }
        EventBus.emit("session:deleted", { sessionId });
      } catch (error) {
        console.error("[SessionManager] Error deleting session:", error);
        EventBus.emit("session:error", { error: error.message });
        throw error;
      }
    }
  };
  window.SessionManager = SessionManager;

  // js/components/services/ComponentLocationManager.js
  var ComponentLocationManager = {
    // 存储所有组件的位置记录
    locationRecords: /* @__PURE__ */ new Map(),
    // 存储注册的定位策略
    locationStrategies: /* @__PURE__ */ new Map(),
    /**
     * 初始化（注册默认策略）
     */
    init() {
      this.registerDefaultStrategies();
    },
    /**
     * 注册默认的组件定位策略
     */
    registerDefaultStrategies() {
      this.registerStrategy("UserMessage", {
        findParent: (data) => {
          const sessionId = data.sessionId || StateManager.getState("currentSessionId");
          return {
            parentType: "ChatContainer",
            parentId: `chat-container-${sessionId}`,
            selectionCriteria: { sessionId }
          };
        }
      });
      this.registerStrategy("AssistantMessage", {
        findParent: (data) => {
          const sessionId = data.sessionId || StateManager.getState("currentSessionId");
          return {
            parentType: "ChatContainer",
            parentId: `chat-container-${sessionId}`,
            selectionCriteria: { sessionId }
          };
        }
      });
      this.registerStrategy("ResponseBlock", {
        findParent: (data) => {
          const { dialogId, messageId } = data;
          let parentId = null;
          let parentType = "AssistantMessage";
          if (messageId) {
            parentId = messageId;
          } else if (dialogId) {
            const messages = StateManager.getState("messages") || [];
            const assistantMsg = messages.find(
              (m) => m.role === "assistant" && m.dialogId === dialogId
            );
            if (assistantMsg) {
              parentId = assistantMsg.id;
            }
          }
          return {
            parentType,
            parentId,
            selectionCriteria: { dialogId, messageId }
          };
        }
      });
      this.registerStrategy("ToolCard", {
        findParent: (data) => {
          const { dialogId, callId, responseId } = data;
          let parentId = null;
          let parentType = "ResponseBlock";
          if (responseId) {
            parentId = responseId;
          } else if (dialogId) {
            const blocks = StateManager.state.responseBlocks;
            for (const [blockId, block] of blocks.entries()) {
              if (block.dialogId === dialogId) {
                parentId = blockId;
                break;
              }
            }
          }
          return {
            parentType,
            parentId,
            selectionCriteria: { dialogId, callId, responseId }
          };
        }
      });
      this.registerStrategy("TextBlock", {
        findParent: (data) => {
          const { responseId } = data;
          return {
            parentType: "ResponseBlock",
            parentId: responseId,
            selectionCriteria: { responseId }
          };
        }
      });
      this.registerStrategy("ThinkBlock", {
        findParent: (data) => {
          const { responseId } = data;
          return {
            parentType: "ResponseBlock",
            parentId: responseId,
            selectionCriteria: { responseId }
          };
        }
      });
      this.registerStrategy("ReasonBlock", {
        findParent: (data) => {
          const { responseId } = data;
          return {
            parentType: "ResponseBlock",
            parentId: responseId,
            selectionCriteria: { responseId }
          };
        }
      });
    },
    /**
     * 注册自定义定位策略
     * @param {string} componentType - 组件类型
     * @param {object} strategy - 定位策略对象
     */
    registerStrategy(componentType, strategy) {
      this.locationStrategies.set(componentType, strategy);
      console.log(`[ComponentLocationManager] Registered strategy for ${componentType}`);
    },
    /**
     * 获取组件的定位信息
     * @param {string} componentType - 组件类型
     * @param {object} data - 组件数据
     * @returns {object} - 定位信息
     */
    getLocation(componentType, data) {
      const strategy = this.locationStrategies.get(componentType);
      if (!strategy) {
        console.warn(`[ComponentLocationManager] No strategy found for ${componentType}`);
        return null;
      }
      try {
        const location = strategy.findParent(data);
        return location;
      } catch (error) {
        console.error(`[ComponentLocationManager] Error getting location for ${componentType}:`, error);
        return null;
      }
    },
    /**
     * 记录组件创建位置
     * @param {string} componentId - 组件唯一ID
     * @param {string} componentType - 组件类型
     * @param {object} data - 创建组件时使用的数据
     * @param {object} options - 选项
     * @param {boolean} options.abandoned - 是否被抛弃
     * @param {string} options.abandonReason - 抛弃原因
     */
    recordCreation(componentId, componentType, data, options = {}) {
      const { abandoned = false, abandonReason = null } = options;
      const location = this.getLocation(componentType, data);
      const record = {
        componentId,
        componentType,
        parentType: location?.parentType || null,
        parentId: location?.parentId || null,
        selectionCriteria: location?.selectionCriteria || {},
        creationData: { ...data },
        timestamp: Date.now(),
        isValid: !!location?.parentId,
        abandoned,
        abandonReason
      };
      this.locationRecords.set(componentId, record);
      if (abandoned) {
        console.log(`%c[ComponentLocationManager] Component ABANDONED:`, "color: #FF9800");
        console.log(`%c  ID: ${componentId}`, "color: #FF9800");
        console.log(`%c  Type: ${componentType}`, "color: #FF9800");
        console.log(`%c  Reason: ${abandonReason || "Unknown"}`, "color: #FF9800");
        console.log(`%c  Criteria: ${JSON.stringify(data)}`, "color: #FF9800");
      } else {
        console.log(`%c[ComponentLocationManager] Recorded component creation:`, "color: #4CAF50");
        console.log(`%c  ID: ${componentId}`, "color: #4CAF50");
        console.log(`%c  Type: ${componentType}`, "color: #4CAF50");
        console.log(`%c  Parent: ${location?.parentType || "Unknown"} (${location?.parentId || "N/A"})`, "color: #4CAF50");
        console.log(`%c  Criteria: ${JSON.stringify(location?.selectionCriteria || {})}`, "color: #4CAF50");
        console.log(`%c  Valid: ${record.isValid}`, record.isValid ? "color: #4CAF50" : "color: #f44336");
      }
      return record;
    },
    /**
     * 记录被抛弃的组件
     * @param {string} componentId - 组件唯一ID
     * @param {string} componentType - 组件类型
     * @param {object} data - 创建组件时使用的数据
     * @param {string} reason - 抛弃原因
     */
    recordAbandoned(componentId, componentType, data, reason) {
      return this.recordCreation(componentId, componentType, data, {
        abandoned: true,
        abandonReason: reason
      });
    },
    /**
     * 获取组件的位置记录
     * @param {string} componentId - 组件ID
     * @returns {object|null} - 位置记录
     */
    getRecord(componentId) {
      return this.locationRecords.get(componentId) || null;
    },
    /**
     * 获取所有组件位置记录
     * @returns {Array} - 所有记录数组
     */
    getAllRecords() {
      return Array.from(this.locationRecords.values());
    },
    /**
     * 验证所有组件的位置是否正确
     * @returns {object} - 验证结果
     */
    validateAll() {
      const results = {
        valid: [],
        invalid: [],
        warnings: [],
        abandoned: []
      };
      for (const [componentId, record] of this.locationRecords.entries()) {
        if (record.abandoned) {
          results.abandoned.push({
            componentId,
            componentType: record.componentType,
            reason: record.abandonReason || "Unknown",
            criteria: record.creationData
          });
          continue;
        }
        if (!record.parentId) {
          results.invalid.push({
            componentId,
            componentType: record.componentType,
            reason: "\u65E0\u6CD5\u627E\u5230\u7236\u7EC4\u4EF6",
            criteria: record.selectionCriteria
          });
        } else {
          const parentExists = this._checkParentExists(record.parentType, record.parentId);
          if (parentExists) {
            results.valid.push({
              componentId,
              componentType: record.componentType,
              parentType: record.parentType,
              parentId: record.parentId
            });
          } else {
            results.warnings.push({
              componentId,
              componentType: record.componentType,
              reason: "\u7236\u7EC4\u4EF6\u4E0D\u5B58\u5728",
              parentType: record.parentType,
              parentId: record.parentId
            });
          }
        }
      }
      console.log(`%c[ComponentLocationManager] Validation Complete`, "color: #2196F3; font-weight: bold");
      console.log(`%c  \u2705 Valid: ${results.valid.length}`, "color: #4CAF50");
      console.log(`%c  \u26A0\uFE0F Warnings: ${results.warnings.length}`, "color: #FF9800");
      console.log(`%c  \u274C Invalid: ${results.invalid.length}`, "color: #f44336");
      console.log(`%c  \u{1F5D1}\uFE0F Abandoned: ${results.abandoned.length}`, "color: #9E9E9E");
      if (results.warnings.length > 0) {
        console.log(`%c[ComponentLocationManager] Warnings Details:`, "color: #FF9800");
        results.warnings.forEach((w) => {
          console.log(`  - ${w.componentType}(${w.componentId}): ${w.reason}`);
        });
      }
      if (results.invalid.length > 0) {
        console.log(`%c[ComponentLocationManager] Invalid Details:`, "color: #f44336");
        results.invalid.forEach((i) => {
          console.log(`  - ${i.componentType}(${i.componentId}): ${i.reason}`);
          console.log(`    Criteria: ${JSON.stringify(i.criteria)}`);
        });
      }
      if (results.abandoned.length > 0) {
        console.log(`%c[ComponentLocationManager] Abandoned Details:`, "color: #9E9E9E");
        results.abandoned.forEach((a) => {
          console.log(`  - ${a.componentType}(${a.componentId}): ${a.reason}`);
          console.log(`    Criteria: ${JSON.stringify(a.criteria)}`);
        });
      }
      return results;
    },
    /**
     * 检查父组件是否存在
     * @param {string} parentType - 父组件类型
     * @param {string} parentId - 父组件ID
     * @returns {boolean}
     */
    _checkParentExists(parentType, parentId) {
      if (!parentId)
        return false;
      switch (parentType) {
        case "ChatContainer":
          return true;
        case "AssistantMessage": {
          const messages = StateManager.getState("messages") || [];
          return messages.some((m) => m.id === parentId);
        }
        case "ResponseBlock": {
          return StateManager.state.responseBlocks.has(parentId);
        }
        default:
          return true;
      }
    },
    /**
     * 按父组件分组获取组件
     * @param {string} parentId - 父组件ID
     * @returns {Array} - 子组件列表
     */
    getComponentsByParent(parentId) {
      return Array.from(this.locationRecords.values()).filter(
        (record) => record.parentId === parentId
      );
    },
    /**
     * 获取组件树结构
     * @returns {object} - 组件树
     */
    getComponentTree() {
      const tree = {};
      for (const record of this.locationRecords.values()) {
        const parentId = record.parentId || "root";
        if (!tree[parentId]) {
          tree[parentId] = {
            parentType: record.parentType,
            children: []
          };
        }
        tree[parentId].children.push({
          componentId: record.componentId,
          componentType: record.componentType,
          criteria: record.selectionCriteria
        });
      }
      return tree;
    },
    /**
     * 导出所有记录为JSON
     * @returns {string} - JSON字符串
     */
    exportRecords() {
      return JSON.stringify(Array.from(this.locationRecords.values()), null, 2);
    },
    /**
     * 清除所有记录
     */
    clear() {
      this.locationRecords.clear();
      console.log("[ComponentLocationManager] All records cleared");
    }
  };
  window.ComponentLocationManager = ComponentLocationManager;
  ComponentLocationManager.init();

  // js/components/services/ChatManager.js
  var ChatManager = {
    initialized: false,
    messageLog: [],
    // 记录消息处理历史，用于测试调试
    // ========== 初始化方法 ==========
    init() {
      if (this.initialized)
        return;
      console.log(`%c[ChatManager] \u{1F680} \u521D\u59CB\u5316 ChatManager`, "color: #2196F3; font-weight: bold");
      if (!EventBus) {
        console.error(`%c[ChatManager] \u274C EventBus \u4E0D\u53EF\u7528!`, "color: #F44336; font-weight: bold");
        return;
      }
      console.log(`%c[ChatManager] \u2705 EventBus \u53EF\u7528`, "color: #4CAF50");
      EventBus.on("ws:message", (data) => {
        console.log(`%c[ChatManager] \u{1F4E5} \u6536\u5230 ws:message \u4E8B\u4EF6`, "color: #2196F3");
        this.handleWebSocketMessage(data);
      });
      this.initialized = true;
      console.log(`%c[ChatManager] \u2705 ChatManager \u521D\u59CB\u5316\u5B8C\u6210`, "color: #4CAF50; font-weight: bold");
    },
    // ========== 消息处理方法 ==========
    // 数据校验函数
    validateEventData(action, data) {
      const requiredFieldsMap = {
        "session.created": ["session_id"],
        "client.message_received": ["session_id", "content"],
        "dialog.created": ["session_id", "dialog_id"],
        "llm.request_sent": ["session_id", "request_id", "dialog_id"],
        "llm.call_thinking": ["request_id"],
        "llm.call_thinking_completed": ["request_id", "thinking"],
        "llm.call_reasoning": ["request_id"],
        "llm.call_reasoning_completed": ["request_id", "reasoning"],
        "llm.call_text": ["request_id", "content"],
        "llm.call_text_completed": ["request_id", "content"],
        "llm.call_completed": ["request_id"],
        "tool.call_started": ["call_id", "tool_name"],
        // request_id 和 parameters 改为可选（后台数据格式）
        "tool.execution_output": ["call_id", "output"],
        "tool.execution_output_end": ["call_id"],
        "tool.call_completed": ["call_id"]
        // result 和 status 改为可选（后台数据格式）
      };
      const requiredFields = requiredFieldsMap[action];
      if (!requiredFields)
        return true;
      const missingFields = requiredFields.filter((field) => {
        let value = data[field];
        if (value === void 0 || value === null || value === "") {
          value = data.data?.[field];
        }
        return value === void 0 || value === null || value === "";
      });
      if (missingFields.length > 0) {
        console.error(`%c[ChatManager] \u274C [DATA_ERROR] \u7F3A\u5C11\u5FC5\u9700\u5B57\u6BB5: ${missingFields.join(", ")} in ${action}`, "color: #F44336; font-weight: bold");
        console.error(`%c[ChatManager] \u274C [DATA_ERROR_DETAIL]`, "color: #F44336", {
          action,
          missingFields,
          receivedData: data,
          timestamp: Date.now()
        });
        console.warn(`%c[ChatManager] \u26A0\uFE0F [FLOW_STOPPED] \u6570\u636E\u6821\u9A8C\u5931\u8D25\uFF0C\u7EC8\u6B62\u5904\u7406\u6D41\u7A0B`, "color: #FF9800; font-weight: bold");
        return false;
      }
      return true;
    },
    // 处理 WebSocket 消息
    handleWebSocketMessage(data) {
      const action = data.action || data.type;
      const sessionId = StateManager.getState("currentSessionId");
      this.messageLog.push({
        action,
        timestamp: Date.now(),
        data: { ...data }
      });
      console.log(`%c[ChatManager] \u{1F4E4} [EVENT_RECEIVED] ${action}`, "color: #2196F3");
      console.log(`%c[ChatManager] \u{1F4E4} [EVENT_DATA]`, "color: #2196F3", JSON.stringify(data, null, 2));
      if (!action) {
        console.error(`%c[ChatManager] \u274C [DATA_ERROR] \u4E8B\u4EF6\u540D\u79F0\u683C\u5F0F\u9519\u8BEF: ${action}`, "color: #F44336; font-weight: bold");
        return;
      }
      if (!this.validateEventData(action, data)) {
        return;
      }
      const msgSessionId = data.session_id || data.sessionId;
      if (msgSessionId && sessionId && msgSessionId !== sessionId) {
        console.log(`%c[ChatManager] \u23ED\uFE0F \u8DF3\u8FC7\u975E\u5F53\u524D\u4F1A\u8BDD\u6D88\u606F: ${msgSessionId}`, "color: #9E9E9E");
        return;
      }
      let wasHandled = false;
      wasHandled = this.emitCreationMessage(action, data, sessionId) || wasHandled;
      wasHandled = this.emitUpdateMessage(action, data, sessionId) || wasHandled;
      wasHandled = this.emitFailedMessage(action, data, sessionId) || wasHandled;
      wasHandled = this.emitEndMessage(action, data, sessionId) || wasHandled;
      if (!wasHandled) {
        console.log(`%c[ChatManager] \u{1F4ED} \u672A\u5904\u7406\u7684\u6D88\u606F: ${action}`, "color: #795548");
      }
    },
    // ========== 消息转发方法 ==========
    // 转发创建类消息
    emitCreationMessage(action, data, currentSessionId) {
      const creationMap = {
        "session.created": "event.session.created",
        "client.message_received": "event.client.message_received",
        "dialog.created": "event.dialog.created",
        "llm.request_sent": "event.llm.request_sent",
        "tool.call_started": "event.tool.call_started"
      };
      const eventName = creationMap[action];
      if (eventName) {
        const mergedData = {
          ...data,
          ...data.data,
          // 合并内层data
          __currentSessionId: currentSessionId
        };
        console.log(`%c[ChatManager] \u{1F476} \u8F6C\u53D1\u521B\u5EFA\u7C7B\u6D88\u606F: ${action} \u2192 ${eventName}`, "color: #00BCD4");
        console.log(`%c[ChatManager]   \u2514\u2500\u2500 \u6570\u636E\u6458\u8981: session_id=${mergedData.session_id}, dialog_id=${mergedData.dialog_id}, request_id=${mergedData.request_id}`, "color: #00BCD4");
        EventBus.emit(eventName, mergedData);
        return true;
      }
      return false;
    },
    // 转发失败类消息
    emitFailedMessage(action, data, currentSessionId) {
      const failedMap = {
        "llm.call_failed": "event.llm.call_failed",
        "llm.response_classified": "event.llm.response_classified"
      };
      const eventName = failedMap[action];
      if (eventName) {
        const mergedData = {
          ...data,
          ...data.data,
          __currentSessionId: currentSessionId
        };
        console.log(`%c[ChatManager] \u274C \u8F6C\u53D1\u5931\u8D25\u7C7B\u6D88\u606F: ${action} \u2192 ${eventName}`, "color: #F44336");
        EventBus.emit(eventName, mergedData);
        return true;
      }
      return false;
    },
    // 转发更新类消息
    emitUpdateMessage(action, data, currentSessionId) {
      const updateMap = {
        "llm.call_thinking": "event.llm.call_thinking",
        "llm.call_reasoning": "event.llm.call_reasoning",
        "llm.call_text": "event.llm.call_text",
        "tool.execution_output": "event.tool.execution_output",
        "event.tool.execution_output": "event.tool.execution_output"
      };
      const eventName = updateMap[action];
      if (eventName) {
        const mergedData = {
          ...data,
          ...data.data,
          __currentSessionId: currentSessionId
        };
        console.log(`%c[ChatManager] \u{1F504} \u8F6C\u53D1\u66F4\u65B0\u7C7B\u6D88\u606F: ${action} \u2192 ${eventName}`, "color: #8BC34A");
        EventBus.emit(eventName, mergedData);
        return true;
      }
      return false;
    },
    // 转发结束类消息
    emitEndMessage(action, data, currentSessionId) {
      const endMap = {
        "llm.call_thinking_completed": "event.llm.call_thinking_completed",
        "llm.call_reasoning_completed": "event.llm.call_reasoning_completed",
        "llm.call_text_completed": "event.llm.call_text_completed",
        "llm.call_completed": "event.llm.call_completed",
        "tool.execution_output_end": "event.tool.execution_output_end",
        "event.tool.execution_output_end": "event.tool.execution_output_end",
        "tool.call_completed": "event.tool.call_completed",
        "dialog.completed": "event.dialog.completed"
      };
      const eventName = endMap[action];
      if (eventName) {
        const mergedData = {
          ...data,
          ...data.data,
          __currentSessionId: currentSessionId
        };
        console.log(`%c[ChatManager] \u{1F3C1} \u8F6C\u53D1\u7ED3\u675F\u7C7B\u6D88\u606F: ${action} \u2192 ${eventName}`, "color: #FF5722");
        EventBus.emit(eventName, mergedData);
        return true;
      }
      return false;
    },
    // ========== 消息发送方法 ==========
    // 发送消息到后端
    sendMessage(content) {
      const sessionId = StateManager.getState("currentSessionId");
      console.log(`%c[ChatManager] \u{1F4E4} \u53D1\u9001\u6D88\u606F\u5230\u540E\u7AEF`, "color: #2196F3; font-weight: bold");
      console.log(`%c[ChatManager]   \u5185\u5BB9: "${content.substring(0, 50)}${content.length > 50 ? "..." : ""}"`, "color: #607D8B");
      console.log(`%c[ChatManager]   sessionId: ${sessionId || "NULL"}`, "color: #607D8B");
      if (!sessionId) {
        console.error(`%c[ChatManager] \u274C \u53D1\u9001\u5931\u8D25: sessionId\u4E3A\u7A7A`, "color: #F44336; font-weight: bold");
        return false;
      }
      const result = WSClient.sendMessage(sessionId, content);
      console.log(`%c[ChatManager] \u{1F4CA} \u53D1\u9001\u7ED3\u679C: ${result ? "\u6210\u529F" : "\u5931\u8D25"}`, 'color: result ? "#4CAF50" : "#F44336"');
      return result;
    },
    // ========== 辅助方法（兼容性保持） ==========
    // 重置状态（会话切换时调用）
    resetState(newSessionId) {
      console.log(`%c[ChatManager] \u{1F9F9} \u91CD\u7F6E\u72B6\u6001: ${newSessionId}`, "color: #9E9E9E");
      StateManager.setState("currentResponseBlockId", null);
      StateManager.setState("currentDialogId", null);
      StateManager.setState("currentRoundNumber", null);
      StateManager.setState("currentAssistantMessageId", null);
      StateManager.state.responseBlocks = /* @__PURE__ */ new Map();
      StateManager.state.toolCallIdMap = /* @__PURE__ */ new Map();
      StateManager.state.pendingToolCalls = /* @__PURE__ */ new Map();
    },
    // 终止对话
    stopDialog() {
      const sessionId = StateManager.getState("currentSessionId");
      const dialogId = StateManager.getState("currentDialogId");
      console.log(`%c[ChatManager] \u23F9\uFE0F \u53D1\u9001\u7EC8\u6B62\u5BF9\u8BDD\u8BF7\u6C42`, "color: #FF5722; font-weight: bold");
      console.log(`%c[ChatManager]   sessionId: ${sessionId}`, "color: #607D8B");
      console.log(`%c[ChatManager]   dialogId: ${dialogId}`, "color: #607D8B");
      if (!sessionId) {
        console.error(`%c[ChatManager] \u274C \u7EC8\u6B62\u5931\u8D25: sessionId\u4E3A\u7A7A`, "color: #F44336; font-weight: bold");
        return false;
      }
      const payload = {
        action: "dialog.stop",
        session_id: sessionId,
        dialog_id: dialogId
      };
      const result = WSClient.sendCustomMessage(payload);
      console.log(`%c[ChatManager] \u{1F4CA} \u7EC8\u6B62\u8BF7\u6C42\u53D1\u9001\u7ED3\u679C: ${result ? "\u6210\u529F" : "\u5931\u8D25"}`, 'color: result ? "#4CAF50" : "#F44336"');
      return result;
    }
  };
  window.ChatManager = ChatManager;

  // js/components/services/ComponentSubscriptions.js
  var ComponentSubscriptions = {
    // 订阅管理状态
    subscriptions: /* @__PURE__ */ new Map(),
    // componentId -> [subscriptionIds]
    componentRegistry: /* @__PURE__ */ new Map(),
    // componentType -> componentData
    // 初始化
    init() {
      console.log(`%c[ComponentSubscriptions] \u2705 \u521D\u59CB\u5316\u7EC4\u4EF6\u8BA2\u9605\u7CFB\u7EDF`, "color: #4CAF50; font-weight: bold");
      if (!window.EventBus) {
        console.error(`%c[ComponentSubscriptions] \u274C EventBus \u4E0D\u53EF\u7528!`, "color: #F44336; font-weight: bold");
        return;
      }
      console.log(`%c[ComponentSubscriptions] \u2705 EventBus \u53EF\u7528`, "color: #4CAF50");
      this.setupCreationSubscriptions();
      console.log(`%c[ComponentSubscriptions] \u2705 \u7EC4\u4EF6\u8BA2\u9605\u7CFB\u7EDF\u521D\u59CB\u5316\u5B8C\u6210`, "color: #4CAF50; font-weight: bold");
    },
    // ========== 创建类消息订阅（序号1-8） ==========
    // 这些由父组件订阅，创建子组件
    setupCreationSubscriptions() {
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u8BBE\u7F6E\u521B\u5EFA\u7C7B\u6D88\u606F\u8BA2\u9605\uFF08\u5E8F\u53F71-8\uFF09`, "color: #9C27B0");
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F71: event.session.created \u2192 ChatPanel \u2192 SessionComponent`, "color: #607D8B");
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F72: event.client.message_received \u2192 SessionComponent \u2192 UserMessage`, "color: #607D8B");
      EventBus.onConditional(
        "event.client.message_received",
        (data) => this.matchSession(data),
        (data) => this.handleUserMessageCreated(data),
        "ComponentSubscriptions(UserMessage)"
      );
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F73: event.dialog.created \u2192 UserMessage \u2192 AssistantMessage`, "color: #607D8B");
      EventBus.onConditional(
        "event.dialog.created",
        (data) => this.matchSession(data),
        (data) => this.handleAssistantMessageCreated(data),
        "ComponentSubscriptions(AssistantMessage)"
      );
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F74: event.llm.request_sent \u2192 AssistantMessage \u2192 ResponseBlock`, "color: #607D8B");
      EventBus.onConditional(
        "event.llm.request_sent",
        (data) => this.matchSession(data),
        (data) => this.handleResponseBlockCreated(data),
        "ComponentSubscriptions(ResponseBlock)"
      );
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F75-7: ResponseBlock \u8BA2\u9605\u521B\u5EFA ThinkBlock/ReasonBlock/TextBlock`, "color: #607D8B");
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F78: event.tool.call_started \u2192 ResponseBlock \u2192 ToolCard`, "color: #607D8B");
    },
    // ========== 数据校验函数 ==========
    validateEventData(eventName, data) {
      const requiredFieldsMap = {
        "event.session.created": ["session_id"],
        "event.client.message_received": ["session_id", "content"],
        "event.dialog.created": ["session_id", "dialog_id"],
        "event.llm.request_sent": ["session_id", "request_id", "dialog_id"],
        "event.llm.call_thinking": ["request_id"],
        "event.llm.call_thinking_completed": ["request_id", "thinking"],
        "event.llm.call_reasoning": ["request_id"],
        "event.llm.call_reasoning_completed": ["request_id", "reasoning"],
        "event.llm.call_text": ["request_id", "content"],
        "event.llm.call_text_completed": ["request_id", "content"],
        "event.llm.call_completed": ["request_id"],
        "event.tool.call_started": ["call_id", "tool_name"],
        // request_id 和 parameters 改为可选
        "event.tool.execution_output": ["call_id", "output"],
        "event.tool.execution_output_end": ["call_id"],
        "event.tool.call_completed": ["call_id"]
        // result 和 status 改为可选
      };
      const requiredFields = requiredFieldsMap[eventName];
      if (!requiredFields)
        return true;
      const missingFields = requiredFields.filter((field) => {
        const value = data[field];
        return value === void 0 || value === null || value === "";
      });
      if (missingFields.length > 0) {
        console.error(`%c[ComponentSubscriptions] \u274C [DATA_ERROR] \u7F3A\u5C11\u5FC5\u9700\u5B57\u6BB5: ${missingFields.join(", ")} in ${eventName}`, "color: #F44336; font-weight: bold");
        console.error(`%c[ComponentSubscriptions] \u274C [DATA_ERROR_DETAIL]`, "color: #F44336", {
          eventName,
          missingFields,
          receivedData: data,
          timestamp: Date.now()
        });
        console.warn(`%c[ComponentSubscriptions] \u26A0\uFE0F [FLOW_STOPPED] \u6570\u636E\u6821\u9A8C\u5931\u8D25\uFF0C\u7EC8\u6B62\u5904\u7406\u6D41\u7A0B`, "color: #FF9800; font-weight: bold");
        return false;
      }
      return true;
    },
    // ========== 参数匹配函数 ==========
    matchSession(data) {
      const currentSessionId = StateManager.getState("currentSessionId");
      const replayEnabled = StateManager.getState("replayEnabled");
      console.log(`%c[ComponentSubscriptions] \u{1F50D} matchSession \u68C0\u67E5:`, "color: #FFC107");
      console.log(`%c[ComponentSubscriptions]   \u251C\u2500\u2500 currentSessionId: ${currentSessionId}`, "color: #FFC107");
      console.log(`%c[ComponentSubscriptions]   \u251C\u2500\u2500 replayEnabled: ${replayEnabled}`, "color: #FFC107");
      console.log(`%c[ComponentSubscriptions]   \u2514\u2500\u2500 data.session_id: ${data.session_id}`, "color: #FFC107");
      if (replayEnabled) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F \u56DE\u653E\u6A21\u5F0F\uFF1A\u5141\u8BB8\u6240\u6709\u4F1A\u8BDD\u6D88\u606F \u2192 \u8FD4\u56DE true`, "color: #FF9800");
        return true;
      }
      if (!currentSessionId) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u5F53\u524D\u4F1A\u8BDDID\u4E3A\u7A7A\uFF0C\u8DF3\u8FC7\u6D88\u606F \u2192 \u8FD4\u56DE false`, "color: #9E9E9E");
        return false;
      }
      if (!data.session_id) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F \u6D88\u606F\u4E2D\u6CA1\u6709session_id\uFF0C\u5141\u8BB8\u901A\u8FC7 \u2192 \u8FD4\u56DE true`, "color: #FF9800");
        return true;
      }
      const matches = data.session_id === currentSessionId;
      if (!matches) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u4F1A\u8BDDID\u4E0D\u5339\u914D: expected=${currentSessionId}, actual=${data.session_id} \u2192 \u8FD4\u56DE false`, "color: #9E9E9E");
      } else {
        console.log(`%c[ComponentSubscriptions] \u2705 \u4F1A\u8BDDID\u5339\u914D: ${currentSessionId} \u2192 \u8FD4\u56DE true`, "color: #4CAF50");
      }
      return matches;
    },
    matchDialog(data) {
      const currentSessionId = StateManager.getState("currentSessionId");
      console.log(`%c[ComponentSubscriptions] matchDialog: currentSessionId=${currentSessionId}, data.session_id=${data.session_id}`, "color: #FF9800");
      if (!currentSessionId) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F matchDialog\u5931\u8D25: \u5F53\u524D\u4F1A\u8BDDID\u4E3A\u7A7A`, "color: #9E9E9E");
        return false;
      }
      if (data.session_id && data.session_id !== currentSessionId) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F matchDialog\u5931\u8D25: \u4F1A\u8BDDID\u4E0D\u5339\u914D expected=${currentSessionId}, actual=${data.session_id}`, "color: #9E9E9E");
        return false;
      }
      return true;
    },
    matchRequest(data, requestId) {
      if (!this.matchDialog(data))
        return false;
      if (data.request_id) {
        if (data.request_id !== requestId) {
          console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u8BF7\u6C42ID\u4E0D\u5339\u914D: expected=${requestId}, actual=${data.request_id}`, "color: #9E9E9E");
          return false;
        }
        return true;
      }
      const currentDialogId = StateManager.getState("currentDialogId");
      if (data.dialog_id && data.dialog_id === currentDialogId) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F \u4F7F\u7528 dialog_id \u5339\u914D\u66FF\u4EE3 request_id: dialog_id=${data.dialog_id}`, "color: #FF9800");
        return true;
      }
      console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u65E0\u6CD5\u5339\u914D: request_id=${data.request_id}, dialog_id=${data.dialog_id}, expected_requestId=${requestId}`, "color: #9E9E9E");
      return false;
    },
    matchToolCall(data, toolCallId) {
      if (!this.matchDialog(data))
        return false;
      if (!data.call_id || data.call_id !== toolCallId) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u5DE5\u5177\u8C03\u7528ID\u4E0D\u5339\u914D: expected=${toolCallId}, actual=${data.call_id}`, "color: #9E9E9E");
        return false;
      }
      return true;
    },
    // ========== 组件创建处理函数 ==========
    handleUserMessageCreated(data) {
      console.log(`%c[ComponentSubscriptions] \u{1F504} \u8FDB\u5165 handleUserMessageCreated`, "color: #00BCD4; font-weight: bold");
      console.log(`%c[ComponentSubscriptions] \u{1F4E4} \u6536\u5230\u6570\u636E:`, "color: #00BCD4", JSON.stringify(data, null, 2));
      const actualData = data.data || data;
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u5B9E\u9645\u6570\u636E:`, "color: #00BCD4", JSON.stringify(actualData, null, 2));
      if (!this.validateEventData("event.client.message_received", actualData)) {
        console.log(`%c[ComponentSubscriptions] \u274C \u6570\u636E\u6821\u9A8C\u5931\u8D25\uFF0C\u9000\u51FA`, "color: #F44336");
        return;
      }
      console.log(`%c[ComponentSubscriptions] \u2705 \u6570\u636E\u6821\u9A8C\u901A\u8FC7`, "color: #4CAF50");
      if (data.action !== "client.message_received" && data.action !== "event.client.message_received") {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u8DF3\u8FC7\u975E client.message_received \u6D88\u606F: ${data.action}`, "color: #9E9E9E");
        return;
      }
      console.log(`%c[ComponentSubscriptions] \u2705 \u901A\u8FC7 action \u68C0\u67E5`, "color: #4CAF50");
      const content = actualData.content || "";
      if (!content.trim()) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u8DF3\u8FC7\u7A7A\u6D88\u606F`, "color: #9E9E9E");
        return;
      }
      const currentSessionId = StateManager.getState("currentSessionId");
      const messages = StateManager.getState("messages") || [];
      const existing = messages.find(
        (m) => m.role === "user" && (m.content === content || m.messageId === actualData.message_id)
      );
      if (existing) {
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u7528\u6237\u6D88\u606F\u5DF2\u5B58\u5728\uFF0C\u8DF3\u8FC7`, "color: #9E9E9E");
        return;
      }
      const userMessage = {
        id: "user-" + Date.now(),
        role: "user",
        content,
        sessionId: currentSessionId,
        dialogId: actualData.dialog_id || null,
        messageId: actualData.message_id || null,
        timestamp: Date.now()
      };
      messages.push(userMessage);
      StateManager.setState("messages", messages);
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA UserMessage (${userMessage.id})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("SessionComponent", "UserMessage", {
        messageId: userMessage.id,
        content: content.substring(0, 50) + (content.length > 50 ? "..." : "")
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          userMessage.id,
          "UserMessage",
          {
            sessionId: userMessage.sessionId,
            dialogId: userMessage.dialogId,
            messageId: userMessage.messageId
          }
        );
      }
      EventBus.emit("component:user-message-created", { message: userMessage });
    },
    handleAssistantMessageCreated(data) {
      if (!this.validateEventData("event.dialog.created", data)) {
        return;
      }
      const currentSessionId = StateManager.getState("currentSessionId");
      const messages = StateManager.getState("messages") || [];
      const existing = messages.find(
        (m) => m.role === "assistant" && m.dialogId === data.dialog_id
      );
      if (existing) {
        StateManager.setState("currentAssistantMessageId", existing.id);
        console.log(`%c[ComponentSubscriptions] \u23ED\uFE0F \u52A9\u624B\u6D88\u606F\u5DF2\u5B58\u5728\uFF0C\u8DF3\u8FC7: ${existing.id}`, "color: #9E9E9E");
        return;
      }
      const assistantMessage = {
        id: "assistant-" + Date.now(),
        role: "assistant",
        content: "",
        sessionId: currentSessionId,
        dialogId: data.dialog_id,
        responseBlocks: [],
        status: "streaming",
        timestamp: Date.now()
      };
      messages.push(assistantMessage);
      StateManager.setState("messages", messages);
      StateManager.setState("currentDialogId", data.dialog_id);
      StateManager.setState("currentAssistantMessageId", assistantMessage.id);
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA AssistantMessage (${assistantMessage.id})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("UserMessage", "AssistantMessage", {
        messageId: assistantMessage.id,
        dialogId: data.dialog_id
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          assistantMessage.id,
          "AssistantMessage",
          {
            sessionId: assistantMessage.sessionId,
            dialogId: assistantMessage.dialogId
          }
        );
      }
      EventBus.emit("component:assistant-message-created", { message: assistantMessage });
    },
    handleResponseBlockCreated(data) {
      if (!this.validateEventData("event.llm.request_sent", data)) {
        return;
      }
      const currentSessionId = StateManager.getState("currentSessionId");
      const responseId = "resp-" + (data.request_id || Date.now());
      if (!StateManager.state.responseBlocks) {
        StateManager.state.responseBlocks = /* @__PURE__ */ new Map();
      }
      if (StateManager.state.responseBlocks.has(responseId)) {
        console.warn(`%c[ComponentSubscriptions] \u26A0\uFE0F \u91CD\u590D\u521B\u5EFA ResponseBlock \u88AB\u963B\u6B62: ${responseId}`, "color: #FF9800");
        return;
      }
      const responseBlock = Vue.observable({
        responseId,
        requestId: data.request_id || null,
        sessionId: currentSessionId,
        dialogId: data.dialog_id || null,
        thinkContent: "",
        reasonContent: "",
        textContent: "",
        toolCalls: [],
        status: "streaming",
        timestamp: Date.now(),
        __subscriptions: []
        // 存储此组件的订阅ID
      });
      StateManager.state.responseBlocks.set(responseId, responseBlock);
      StateManager.setState("currentResponseBlockId", responseId);
      const currentAssistantMessageId = StateManager.getState("currentAssistantMessageId");
      if (currentAssistantMessageId) {
        const messages = StateManager.getState("messages") || [];
        const assistantMessage = messages.find((m) => m.id === currentAssistantMessageId);
        if (assistantMessage) {
          assistantMessage.responseBlocks = assistantMessage.responseBlocks || [];
          assistantMessage.responseBlocks.push(responseId);
          StateManager.setState("messages", [...messages]);
        }
      }
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA ResponseBlock (${responseId})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("AssistantMessage", "ResponseBlock", {
        responseId,
        requestId: data.request_id
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          responseId,
          "ResponseBlock",
          {
            responseId,
            dialogId: data.dialog_id,
            messageId: currentAssistantMessageId
          }
        );
      }
      EventBus.emit("component:response-block-created", { responseId, block: responseBlock });
      this.setupResponseBlockSubscriptions(responseId, data.request_id);
    },
    // 设置 ResponseBlock 的子组件订阅
    setupResponseBlockSubscriptions(responseId, requestId) {
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u4E3A ResponseBlock (${responseId}) \u8BBE\u7F6E\u5B50\u7EC4\u4EF6\u8BA2\u9605`, "color: #9C27B0");
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F75: event.llm.call_thinking_completed \u2192 ResponseBlock \u2192 ThinkBlock`, "color: #607D8B");
      const thinkSubId = EventBus.onceConditional(
        "event.llm.call_thinking_completed",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleThinkBlockCreated(responseId, data),
        `ComponentSubscriptions(ThinkBlock_${responseId})`
      );
      block.__subscriptions.push({ type: "think_creation", id: thinkSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F76: event.llm.call_reasoning_completed \u2192 ResponseBlock \u2192 ReasonBlock`, "color: #607D8B");
      const reasonSubId = EventBus.onceConditional(
        "event.llm.call_reasoning_completed",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleReasonBlockCreated(responseId, data),
        `ComponentSubscriptions(ReasonBlock_${responseId})`
      );
      block.__subscriptions.push({ type: "reason_creation", id: reasonSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F77: event.llm.call_text_completed \u2192 ResponseBlock \u2192 TextBlock`, "color: #607D8B");
      const textSubId = EventBus.onceConditional(
        "event.llm.call_text_completed",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleTextBlockCreated(responseId, data),
        `ComponentSubscriptions(TextBlock_${responseId})`
      );
      block.__subscriptions.push({ type: "text_creation", id: textSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F78: event.tool.call_started \u2192 ResponseBlock \u2192 ToolCard`, "color: #607D8B");
      const toolSubId = EventBus.onConditional(
        "event.tool.call_started",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleToolCardCreated(responseId, data),
        `ComponentSubscriptions(ToolCard_${responseId})`
      );
      block.__subscriptions.push({ type: "tool_creation", id: toolSubId });
      this.setupUpdateSubscriptions(responseId, requestId);
      this.setupEndSubscriptions(responseId, requestId);
    },
    // ========== 子组件创建处理函数 ==========
    handleThinkBlockCreated(responseId, data) {
      if (!this.validateEventData("event.llm.call_thinking_completed", data)) {
        return;
      }
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ThinkBlock \u521B\u5EFA\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const thinking = data.thinking || data.content || "";
      if (thinking) {
        block.thinkContent = thinking;
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
      }
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA ThinkBlock (${responseId})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("ResponseBlock", "ThinkBlock", {
        responseId,
        contentLength: thinking.length
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          `think-${responseId}`,
          "ThinkBlock",
          { responseId }
        );
      }
      const requestId = block.requestId;
      this.setupThinkBlockSubscriptions(responseId, requestId);
    },
    handleReasonBlockCreated(responseId, data) {
      if (!this.validateEventData("event.llm.call_reasoning_completed", data)) {
        return;
      }
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ReasonBlock \u521B\u5EFA\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const reasoning = data.reasoning || data.content || "";
      if (reasoning) {
        block.reasonContent = reasoning;
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
      }
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA ReasonBlock (${responseId})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("ResponseBlock", "ReasonBlock", {
        responseId,
        contentLength: reasoning.length
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          `reason-${responseId}`,
          "ReasonBlock",
          { responseId }
        );
      }
      const requestId = block.requestId;
      this.setupReasonBlockSubscriptions(responseId, requestId);
    },
    handleTextBlockCreated(responseId, data) {
      if (!this.validateEventData("event.llm.call_text_completed", data)) {
        return;
      }
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F TextBlock \u521B\u5EFA\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const content = data.content || "";
      if (content) {
        block.textContent = content;
        StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
      }
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA TextBlock (${responseId})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("ResponseBlock", "TextBlock", {
        responseId,
        contentLength: content.length
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          `text-${responseId}`,
          "TextBlock",
          { responseId }
        );
      }
      const requestId = block.requestId;
      this.setupTextBlockSubscriptions(responseId, requestId);
    },
    handleToolCardCreated(responseId, data) {
      console.log(`%c[ComponentSubscriptions] \u{1F6E0}\uFE0F \u6536\u5230\u5DE5\u5177\u8C03\u7528\u5F00\u59CB\u4E8B\u4EF6\uFF0C\u51C6\u5907\u521B\u5EFA ToolCard: responseId=${responseId}`, "color: #00BCD4");
      if (!this.validateEventData("event.tool.call_started", data)) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ToolCard \u521B\u5EFA\u5931\u8D25\uFF1A\u6570\u636E\u6821\u9A8C\u5931\u8D25`, "color: #FF9800");
        return;
      }
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ToolCard \u521B\u5EFA\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const toolCallId = data.call_id || "tool-" + Date.now();
      const toolCard = {
        callId: toolCallId,
        toolName: data.tool_name || "unknown",
        args: data.parameters || data.params || data.args || {},
        // 优先使用 parameters，兼容 params 和 args
        output: "",
        status: "streaming",
        __subscriptions: []
      };
      block.toolCalls.push(toolCard);
      block.toolCalls = [...block.toolCalls];
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
      console.log(`%c[ComponentSubscriptions] \u{1F476} \u521B\u5EFA ToolCard (${toolCallId})`, "color: #00BCD4; font-weight: bold");
      EventBus.trackComponentCreation("ResponseBlock", "ToolCard", {
        responseId,
        toolCallId,
        toolName: data.tool_name
      });
      if (window.ComponentLocationManager) {
        window.ComponentLocationManager.recordCreation(
          toolCallId,
          "ToolCard",
          {
            responseId,
            callId: toolCallId
          }
        );
      }
      this.setupToolCardSubscriptions(responseId, toolCallId);
    },
    // ========== 更新类消息订阅（序号9-12） ==========
    setupUpdateSubscriptions(responseId, requestId) {
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u8BBE\u7F6E\u66F4\u65B0\u7C7B\u6D88\u606F\u8BA2\u9605\uFF08\u5E8F\u53F79-12\uFF09`, "color: #8BC34A");
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F79: event.llm.call_text_streaming \u2192 TextBlock`, "color: #607D8B");
      const textUpdateSubId = EventBus.onConditional(
        "event.llm.call_text_streaming",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleTextBlockUpdate(responseId, data),
        `ComponentSubscriptions(TextUpdate_${responseId})`
      );
      block.__subscriptions.push({ type: "text_update", id: textUpdateSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F710: event.llm.call_thinking_streaming \u2192 ThinkBlock`, "color: #607D8B");
      const thinkUpdateSubId = EventBus.onConditional(
        "event.llm.call_thinking_streaming",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleThinkBlockUpdate(responseId, data),
        `ComponentSubscriptions(ThinkUpdate_${responseId})`
      );
      block.__subscriptions.push({ type: "think_update", id: thinkUpdateSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F711: event.llm.call_reasoning_streaming \u2192 ReasonBlock`, "color: #607D8B");
      const reasonUpdateSubId = EventBus.onConditional(
        "event.llm.call_reasoning_streaming",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleReasonBlockUpdate(responseId, data),
        `ComponentSubscriptions(ReasonUpdate_${responseId})`
      );
      block.__subscriptions.push({ type: "reason_update", id: reasonUpdateSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F712: event.tool.execution_output \u2192 ToolCard (\u5728 ToolCard \u521B\u5EFA\u65F6\u8BBE\u7F6E)`, "color: #607D8B");
    },
    setupThinkBlockSubscriptions(responseId, requestId) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F714: event.llm.call_thinking_completed_end \u2192 ThinkBlock`, "color: #607D8B");
      const thinkEndSubId = EventBus.onceConditional(
        "event.llm.call_thinking_completed_end",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleThinkBlockEnd(responseId, data),
        `ComponentSubscriptions(ThinkEnd_${responseId})`
      );
      block.__subscriptions.push({ type: "think_end", id: thinkEndSubId });
    },
    setupReasonBlockSubscriptions(responseId, requestId) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F715: event.llm.call_reasoning_completed_end \u2192 ReasonBlock`, "color: #607D8B");
      const reasonEndSubId = EventBus.onceConditional(
        "event.llm.call_reasoning_completed_end",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleReasonBlockEnd(responseId, data),
        `ComponentSubscriptions(ReasonEnd_${responseId})`
      );
      block.__subscriptions.push({ type: "reason_end", id: reasonEndSubId });
    },
    setupTextBlockSubscriptions(responseId, requestId) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F713: event.llm.call_text_completed_end \u2192 TextBlock`, "color: #607D8B");
      const textEndSubId = EventBus.onceConditional(
        "event.llm.call_text_completed_end",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleTextBlockEnd(responseId, data),
        `ComponentSubscriptions(TextEnd_${responseId})`
      );
      block.__subscriptions.push({ type: "text_end", id: textEndSubId });
    },
    setupToolCardSubscriptions(responseId, toolCallId) {
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u5C1D\u8BD5\u4E3A ToolCard \u8BBE\u7F6E\u8BA2\u9605: responseId=${responseId}, toolCallId=${toolCallId}`, "color: #9C27B0");
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F setupToolCardSubscriptions: ResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const toolCard = block.toolCalls.find((tc) => tc.callId === toolCallId);
      if (!toolCard) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F setupToolCardSubscriptions: ToolCard \u4E0D\u5B58\u5728: ${toolCallId}`, "color: #FF9800");
        return;
      }
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u4E3A ToolCard (${toolCallId}) \u8BBE\u7F6E\u8BA2\u9605`, "color: #9C27B0");
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F712: event.tool.execution_output \u2192 ToolCard`, "color: #607D8B");
      const toolUpdateSubId = EventBus.onConditional(
        "event.tool.execution_output",
        (data) => this.matchToolCall(data, toolCallId),
        (data) => this.handleToolCardUpdate(responseId, toolCallId, data),
        `ComponentSubscriptions(ToolUpdate_${toolCallId})`
      );
      toolCard.__subscriptions.push({ type: "tool_update", id: toolUpdateSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F717: event.tool.execution_output_end \u2192 ToolCard`, "color: #607D8B");
      const toolOutputEndSubId = EventBus.onceConditional(
        "event.tool.execution_output_end",
        (data) => this.matchToolCall(data, toolCallId),
        (data) => this.handleToolCardOutputEnd(responseId, toolCallId, data),
        `ComponentSubscriptions(ToolOutputEnd_${toolCallId})`
      );
      toolCard.__subscriptions.push({ type: "tool_output_end", id: toolOutputEndSubId });
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F718: event.tool.call_completed \u2192 ToolCard`, "color: #607D8B");
      const toolEndSubId = EventBus.onceConditional(
        "event.tool.call_completed",
        (data) => this.matchToolCall(data, toolCallId),
        (data) => this.handleToolCardEnd(responseId, toolCallId, data),
        `ComponentSubscriptions(ToolEnd_${toolCallId})`
      );
      toolCard.__subscriptions.push({ type: "tool_end", id: toolEndSubId });
    },
    // ========== 结束类消息订阅（序号13-18） ==========
    setupEndSubscriptions(responseId, requestId) {
      console.log(`%c[ComponentSubscriptions] \u{1F4E5} \u8BBE\u7F6E\u7ED3\u675F\u7C7B\u6D88\u606F\u8BA2\u9605\uFF08\u5E8F\u53F713-18\uFF09`, "color: #E91E63");
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log(`%c[ComponentSubscriptions]   \u5E8F\u53F716: event.llm.call_completed_end \u2192 ResponseBlock`, "color: #607D8B");
      const callEndSubId = EventBus.onceConditional(
        "event.llm.call_completed_end",
        (data) => this.matchRequest(data, requestId),
        (data) => this.handleResponseBlockEnd(responseId, data),
        `ComponentSubscriptions(CallEnd_${responseId})`
      );
      block.__subscriptions.push({ type: "call_end", id: callEndSubId });
    },
    // ========== 更新处理函数 ==========
    handleTextBlockUpdate(responseId, data) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F TextBlock \u66F4\u65B0\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const content = data.content || data.thinking || "";
      if (content) {
        block.textContent += content;
        StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
        console.log(`%c[ComponentSubscriptions] \u{1F504} \u66F4\u65B0 TextBlock (${responseId})`, "color: #8BC34A");
        EventBus.trackComponentUpdate("TextBlock", "streaming", {
          responseId,
          addedLength: content.length,
          totalLength: block.textContent.length
        });
      }
    },
    handleThinkBlockUpdate(responseId, data) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ThinkBlock \u66F4\u65B0\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const content = data.thinking || data.content || "";
      if (content) {
        block.thinkContent += content;
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
        console.log(`%c[ComponentSubscriptions] \u{1F504} \u66F4\u65B0 ThinkBlock (${responseId})`, "color: #8BC34A");
        EventBus.trackComponentUpdate("ThinkBlock", "streaming", {
          responseId,
          addedLength: content.length,
          totalLength: block.thinkContent.length
        });
      }
    },
    handleReasonBlockUpdate(responseId, data) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ReasonBlock \u66F4\u65B0\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const content = data.reasoning || data.content || "";
      if (content) {
        block.reasonContent += content;
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
        console.log(`%c[ComponentSubscriptions] \u{1F504} \u66F4\u65B0 ReasonBlock (${responseId})`, "color: #8BC34A");
        EventBus.trackComponentUpdate("ReasonBlock", "streaming", {
          responseId,
          addedLength: content.length,
          totalLength: block.reasonContent.length
        });
      }
    },
    handleToolCardUpdate(responseId, toolCallId, data) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ToolCard \u66F4\u65B0\u5931\u8D25\uFF1AResponseBlock \u4E0D\u5B58\u5728: ${responseId}`, "color: #FF9800");
        return;
      }
      const toolCard = block.toolCalls.find((tc) => tc.callId === toolCallId);
      if (!toolCard) {
        console.log(`%c[ComponentSubscriptions] \u26A0\uFE0F ToolCard \u66F4\u65B0\u5931\u8D25\uFF1AToolCard \u4E0D\u5B58\u5728: ${toolCallId}`, "color: #FF9800");
        return;
      }
      const output = data.output || "";
      if (output) {
        toolCard.output += output;
        StateManager.setState("messages", [...StateManager.getState("messages") || []]);
        console.log(`%c[ComponentSubscriptions] \u{1F504} \u66F4\u65B0 ToolCard (${toolCallId})`, "color: #8BC34A");
        EventBus.trackComponentUpdate("ToolCard", "execution", {
          toolCallId,
          addedLength: output.length,
          totalLength: toolCard.output.length
        });
      }
    },
    // ========== 结束处理函数 ==========
    handleTextBlockEnd(responseId, data) {
      console.log("[ComponentSubscriptions] TextBlock \u7ED3\u675F:", responseId, data);
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      const content = data.content || "";
      if (content) {
        block.textContent = content;
        StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
      }
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
    },
    handleThinkBlockEnd(responseId, data) {
      console.log("[ComponentSubscriptions] ThinkBlock \u7ED3\u675F:", responseId, data);
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      const thinking = data.thinking || data.content || "";
      if (thinking) {
        block.thinkContent = thinking;
      }
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
    },
    handleReasonBlockEnd(responseId, data) {
      console.log("[ComponentSubscriptions] ReasonBlock \u7ED3\u675F:", responseId, data);
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      const reasoning = data.reasoning || data.content || "";
      if (reasoning) {
        block.reasonContent = reasoning;
      }
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
    },
    handleToolCardOutputEnd(responseId, toolCallId, data) {
      console.log("[ComponentSubscriptions] ToolCard \u8F93\u51FA\u7ED3\u675F:", responseId, toolCallId);
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      const toolCard = block.toolCalls.find((tc) => tc.callId === toolCallId);
      if (!toolCard)
        return;
      toolCard.outputEnded = true;
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
    },
    handleToolCardEnd(responseId, toolCallId, data) {
      console.log("[ComponentSubscriptions] ToolCard \u8C03\u7528\u7ED3\u675F:", responseId, toolCallId, "success:", data.success);
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      const toolCard = block.toolCalls.find((tc) => tc.callId === toolCallId);
      if (!toolCard)
        return;
      const isSuccess = data.success !== false;
      toolCard.status = isSuccess ? "completed" : "failed";
      toolCard.success = isSuccess;
      if (isSuccess) {
        toolCard.result = data.result || null;
        toolCard.error = null;
      } else {
        toolCard.result = data.result || null;
        toolCard.error = data.error || "Unknown error";
      }
      console.log("[ComponentSubscriptions] ToolCard \u72B6\u6001\u66F4\u65B0:", toolCard.status, "error:", toolCard.error);
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
      this.cleanupToolCardSubscriptions(responseId, toolCallId);
    },
    handleResponseBlockEnd(responseId, data) {
      console.log("[ComponentSubscriptions] ResponseBlock \u7ED3\u675F:", responseId, data);
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      block.status = "completed";
      if (data.content)
        block.textContent = data.content;
      if (data.thinking)
        block.thinkContent = data.thinking;
      if (data.reasoning)
        block.reasonContent = data.reasoning;
      StateManager.state.responseBlocks = new Map(StateManager.state.responseBlocks);
      StateManager.setState("messages", [...StateManager.getState("messages") || []]);
      this.cleanupResponseBlockSubscriptions(responseId);
    },
    // ========== 订阅清理 ==========
    cleanupResponseBlockSubscriptions(responseId) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      console.log("[ComponentSubscriptions] \u6E05\u7406 ResponseBlock \u8BA2\u9605:", responseId);
      block.__subscriptions.forEach((sub) => {
        EventBus.offConditional("event.llm.call_text_streaming", sub.id);
        EventBus.offConditional("event.llm.call_thinking_streaming", sub.id);
        EventBus.offConditional("event.llm.call_reasoning_streaming", sub.id);
        EventBus.offConditional("event.tool.call_started", sub.id);
      });
      block.toolCalls.forEach((toolCard) => {
        this.cleanupToolCardSubscriptions(responseId, toolCard.callId);
      });
      block.__subscriptions = [];
    },
    cleanupToolCardSubscriptions(responseId, toolCallId) {
      const block = StateManager.state.responseBlocks.get(responseId);
      if (!block)
        return;
      const toolCard = block.toolCalls.find((tc) => tc.callId === toolCallId);
      if (!toolCard)
        return;
      console.log("[ComponentSubscriptions] \u6E05\u7406 ToolCard \u8BA2\u9605:", toolCallId);
      toolCard.__subscriptions.forEach((sub) => {
        EventBus.offConditional("event.tool.execution_output", sub.id);
      });
      toolCard.__subscriptions = [];
    },
    // ========== 清理所有订阅 ==========
    clearAll() {
      console.log(`%c[ComponentSubscriptions] \u{1F9F9} \u6E05\u7406\u6240\u6709\u7EC4\u4EF6\u8BA2\u9605`, "color: #FF9800");
      if (StateManager.state.responseBlocks) {
        StateManager.state.responseBlocks.forEach((block, responseId) => {
          this.cleanupResponseBlockSubscriptions(responseId);
        });
      }
      this.subscriptions.forEach((subIds, componentId) => {
        subIds.forEach((subId) => {
          EventBus.offConditional("event.client.message_received", subId);
          EventBus.offConditional("event.dialog.created", subId);
          EventBus.offConditional("event.llm.request_sent", subId);
        });
      });
      this.subscriptions.clear();
    }
  };
  window.ComponentSubscriptions = ComponentSubscriptions;

  // js/components/services/WorkspaceManager.js
  var WorkspaceManager = {
    api: ApiClient,
    // 获取工作区列表
    async getWorkspaces(params = {}) {
      EventBus.emit("workspace:loading");
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/workspaces" + (query ? "?" + query : ""));
        const rawData = DataNormalizer.parseResponse(result, "workspaces");
        const workspaces = DataNormalizer.normalizeWorkspace(rawData);
        StateManager.setState("workspaces", workspaces);
        StateManager.setState("workspacesLoading", false);
        EventBus.emit("workspace:loaded", { workspaces, total: result.total || workspaces.length });
        return workspaces;
      } catch (error) {
        EventBus.emit("workspace:error", { error: error.message });
        throw error;
      }
    },
    // 创建工作区
    async createWorkspace(data) {
      EventBus.emit("workspace:loading");
      try {
        const result = await this.api.post("/workspaces", data);
        const workspace = DataNormalizer.normalizeWorkspace(result);
        EventBus.emit("workspace:created", { workspace });
        return workspace;
      } catch (error) {
        EventBus.emit("workspace:error", { error: error.message });
        throw error;
      }
    },
    // 更新工作区
    async updateWorkspace(id, data) {
      try {
        const result = await this.api.put(`/workspaces/${id}`, data);
        const workspace = DataNormalizer.normalizeWorkspace(result);
        EventBus.emit("workspace:updated", { workspace });
        return workspace;
      } catch (error) {
        EventBus.emit("workspace:error", { error: error.message });
        throw error;
      }
    },
    // 删除工作区
    async deleteWorkspace(id) {
      try {
        await this.api.delete(`/workspaces/${id}`);
        StateManager.setState("workspaces", StateManager.getState("workspaces").filter((w) => w.id !== id));
        EventBus.emit("workspace:deleted", { id });
      } catch (error) {
        EventBus.emit("workspace:error", { error: error.message });
        throw error;
      }
    },
    // 批量删除
    async batchDelete(ids) {
      try {
        await this.api.post("/workspaces/batch-delete", { ids });
        StateManager.setState("workspaces", StateManager.getState("workspaces").filter((w) => !ids.includes(w.id)));
        EventBus.emit("workspace:deleted", { ids });
      } catch (error) {
        EventBus.emit("workspace:error", { error: error.message });
        throw error;
      }
    }
  };
  window.WorkspaceManager = WorkspaceManager;

  // js/components/services/ModelManager.js
  var ModelManager = {
    api: ApiClient,
    // 获取模型列表
    async getModels(params = {}) {
      EventBus.emit("model:loading", { loading: true });
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/models" + (query ? "?" + query : ""));
        const rawData = DataNormalizer.parseResponse(result, "models");
        const models = DataNormalizer.normalizeModel(rawData);
        StateManager.setState("models", models);
        StateManager.setState("modelsLoading", false);
        EventBus.emit("model:loaded", { models, total: result.total || models.length });
        return models;
      } catch (error) {
        StateManager.setState("modelsLoading", false);
        EventBus.emit("model:error", { error: error.message });
        throw error;
      }
    },
    // 创建模型
    async createModel(data) {
      EventBus.emit("model:loading");
      try {
        const result = await this.api.post("/models", data);
        const model = DataNormalizer.normalizeModel(result);
        EventBus.emit("model:created", { model });
        return model;
      } catch (error) {
        EventBus.emit("model:error", { error: error.message });
        throw error;
      }
    },
    // 更新模型
    async updateModel(id, data) {
      try {
        const result = await this.api.put(`/models/${id}`, data);
        const model = DataNormalizer.normalizeModel(result);
        EventBus.emit("model:updated", { model });
        return model;
      } catch (error) {
        EventBus.emit("model:error", { error: error.message });
        throw error;
      }
    },
    // 删除模型
    async deleteModel(id) {
      try {
        await this.api.delete(`/models/${id}`);
        StateManager.setState("models", StateManager.getState("models").filter((m) => m.id !== id));
        EventBus.emit("model:deleted", { id });
      } catch (error) {
        EventBus.emit("model:error", { error: error.message });
        throw error;
      }
    },
    // 批量删除
    async batchDelete(ids) {
      try {
        await this.api.post("/models/batch-delete", { ids });
        StateManager.setState("models", StateManager.getState("models").filter((m) => !ids.includes(m.id)));
        EventBus.emit("model:deleted", { ids });
      } catch (error) {
        EventBus.emit("model:error", { error: error.message });
        throw error;
      }
    }
  };
  window.ModelManager = ModelManager;

  // js/components/services/ToolManager.js
  var ToolManager = {
    api: ApiClient,
    // 获取工具列表
    async getTools(params = {}) {
      EventBus.emit("tool:loading");
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/tools" + (query ? "?" + query : ""));
        const rawData = DataNormalizer.parseResponse(result, "tools");
        const tools = DataNormalizer.normalizeTool(rawData);
        StateManager.setState("tools", tools);
        StateManager.setState("toolsLoading", false);
        EventBus.emit("tool:loaded", { tools, total: result.total || tools.length });
        return tools;
      } catch (error) {
        EventBus.emit("tool:error", { error: error.message });
        throw error;
      }
    },
    // 创建工具
    async createTool(data) {
      EventBus.emit("tool:loading");
      try {
        const result = await this.api.post("/tools", data);
        const tool = DataNormalizer.normalizeTool(result);
        EventBus.emit("tool:created", { tool });
        return tool;
      } catch (error) {
        EventBus.emit("tool:error", { error: error.message });
        throw error;
      }
    },
    // 更新工具
    async updateTool(id, data) {
      try {
        const result = await this.api.put(`/tools/${id}`, data);
        const tool = DataNormalizer.normalizeTool(result);
        EventBus.emit("tool:updated", { tool });
        return tool;
      } catch (error) {
        EventBus.emit("tool:error", { error: error.message });
        throw error;
      }
    },
    // 删除工具
    async deleteTool(id) {
      try {
        await this.api.delete(`/tools/${id}`);
        StateManager.setState("tools", StateManager.getState("tools").filter((t) => t.id !== id));
        EventBus.emit("tool:deleted", { id });
      } catch (error) {
        EventBus.emit("tool:error", { error: error.message });
        throw error;
      }
    },
    // 批量删除
    async batchDelete(ids) {
      try {
        await this.api.post("/tools/batch-delete", { ids });
        StateManager.setState("tools", StateManager.getState("tools").filter((t) => !ids.includes(t.id)));
        EventBus.emit("tool:deleted", { ids });
      } catch (error) {
        EventBus.emit("tool:error", { error: error.message });
        throw error;
      }
    }
  };
  window.ToolManager = ToolManager;

  // js/components/services/StorageManager.js
  var StorageManager = {
    api: ApiClient,
    // ==================== 实体存储配置 ====================
    // 获取存储配置列表
    async getStorages(params = {}) {
      EventBus.emit("storage:loading");
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/storage-config" + (query ? "?" + query : ""));
        const storages = Array.isArray(result) ? result : [];
        StateManager.setState("storages", storages);
        StateManager.setState("storagesLoading", false);
        EventBus.emit("storage:loaded", { storages, total: storages.length });
        return storages;
      } catch (error) {
        EventBus.emit("storage:error", { error: error.message });
        throw error;
      }
    },
    // 更新存储配置
    async updateStorage(entity_type, data) {
      try {
        const result = await this.api.put(`/storage-config/${entity_type}`, data);
        EventBus.emit("storage:updated", { entity_type, data });
        return result;
      } catch (error) {
        EventBus.emit("storage:error", { error: error.message });
        throw error;
      }
    },
    // 批量更新存储配置
    async batchUpdateStorage(updates) {
      try {
        const result = await this.api.put(`/storage-config/batch`, { updates });
        EventBus.emit("storage:batch_updated", { updates });
        return result;
      } catch (error) {
        EventBus.emit("storage:error", { error: error.message });
        throw error;
      }
    },
    // ==================== 事件存储配置 ====================
    // 获取事件存储配置列表
    async getEventStorages(params = {}) {
      EventBus.emit("eventStorage:loading");
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/event-storage-config" + (query ? "?" + query : ""));
        const eventStorages = Array.isArray(result) ? result : [];
        StateManager.setState("eventStorages", eventStorages);
        StateManager.setState("eventStoragesLoading", false);
        EventBus.emit("eventStorage:loaded", { eventStorages, total: eventStorages.length });
        return eventStorages;
      } catch (error) {
        EventBus.emit("eventStorage:error", { error: error.message });
        throw error;
      }
    },
    // 更新单个事件存储配置
    async updateEventStorage(event_type, data) {
      try {
        const result = await this.api.put(`/event-storage-config/${encodeURIComponent(event_type)}`, data);
        EventBus.emit("eventStorage:updated", { event_type, data });
        return result;
      } catch (error) {
        EventBus.emit("eventStorage:error", { error: error.message });
        throw error;
      }
    },
    // 批量更新事件存储配置
    async batchUpdateEventStorage(updates, projectId = null) {
      try {
        const url = projectId ? `/event-storage-config/batch?project_id=${encodeURIComponent(projectId)}` : "/event-storage-config/batch";
        const result = await this.api.post(url, { updates });
        EventBus.emit("eventStorage:batch_updated", { updates });
        return result;
      } catch (error) {
        EventBus.emit("eventStorage:error", { error: error.message });
        throw error;
      }
    },
    // 重置事件存储配置为默认值
    async resetEventStorage(projectId = null) {
      try {
        const url = projectId ? `/event-storage-config/reset?project_id=${encodeURIComponent(projectId)}` : "/event-storage-config/reset";
        const result = await this.api.post(url);
        EventBus.emit("eventStorage:reset");
        return result;
      } catch (error) {
        EventBus.emit("eventStorage:error", { error: error.message });
        throw error;
      }
    },
    // 检查事件是否应该被存储
    async checkEventPersist(event_type, projectId = null) {
      try {
        const url = projectId ? `/event-storage-config/check/${encodeURIComponent(event_type)}?project_id=${encodeURIComponent(projectId)}` : `/event-storage-config/check/${encodeURIComponent(event_type)}`;
        const result = await this.api.get(url);
        return result;
      } catch (error) {
        EventBus.emit("eventStorage:error", { error: error.message });
        throw error;
      }
    }
  };
  window.StorageManager = StorageManager;

  // js/components/services/PromptManager.js
  var PromptManager = {
    api: ApiClient,
    // 获取提示词列表
    async getPrompts(params = {}) {
      EventBus.emit("prompt:loading", { loading: true });
      try {
        const query = new URLSearchParams(params).toString();
        const result = await this.api.get("/prompts" + (query ? "?" + query : ""));
        const prompts = result || [];
        StateManager.setState("prompts", prompts);
        StateManager.setState("promptsLoading", false);
        EventBus.emit("prompt:loaded", { prompts, total: result.total || prompts.length });
        return prompts;
      } catch (error) {
        StateManager.setState("promptsLoading", false);
        EventBus.emit("prompt:error", { error: error.message });
        throw error;
      }
    },
    // 创建提示词
    async createPrompt(data) {
      EventBus.emit("prompt:loading");
      try {
        const result = await this.api.post("/prompts", data);
        EventBus.emit("prompt:created", { prompt: result });
        return result;
      } catch (error) {
        EventBus.emit("prompt:error", { error: error.message });
        throw error;
      }
    },
    // 更新提示词
    async updatePrompt(promptId, data) {
      try {
        const result = await this.api.put(`/prompts/${promptId}`, data);
        EventBus.emit("prompt:updated", { prompt: result });
        return result;
      } catch (error) {
        EventBus.emit("prompt:error", { error: error.message });
        throw error;
      }
    },
    // 删除提示词
    async deletePrompt(promptId) {
      try {
        await this.api.delete(`/prompts/${promptId}`);
        StateManager.setState("prompts", StateManager.getState("prompts").filter((p) => p.prompt_id !== promptId));
        EventBus.emit("prompt:deleted", { prompt_id: promptId });
      } catch (error) {
        EventBus.emit("prompt:error", { error: error.message });
        throw error;
      }
    },
    // 获取提示词详情
    async getPrompt(promptId) {
      try {
        const result = await this.api.get(`/prompts/${promptId}`);
        return result;
      } catch (error) {
        EventBus.emit("prompt:error", { error: error.message });
        throw error;
      }
    },
    // 渲染提示词（替换变量）
    async renderPrompt(promptId, variables = {}) {
      try {
        const result = await this.api.post(`/prompts/${promptId}/render`, { variables });
        return result;
      } catch (error) {
        EventBus.emit("prompt:error", { error: error.message });
        throw error;
      }
    }
  };
  window.PromptManager = PromptManager;

  // js/components/nav/NavMenuComponent.js
  var NavMenuComponent = {
    name: "NavMenuComponent",
    props: {
      menus: { type: Array, default: () => [] },
      activePage: { type: String, default: "chat" }
    },
    template: `
        <div class="menu-tabs">
            <button
                v-for="menu in sortedMenus"
                :key="menu.id"
                class="menu-tab"
                :class="{ active: activePage === menu.page }"
                @click="handleClick(menu)">
                <span class="menu-icon">{{ menu.icon }}</span>
                <span class="menu-label">{{ menu.label }}</span>
            </button>
        </div>
    `,
    computed: {
      sortedMenus() {
        return this.menus.sort((a, b) => a.sortOrder - b.sortOrder);
      }
    },
    methods: {
      handleClick(menu) {
        EventBus.emit("menu:click", { menu });
      }
    }
  };
  window.NavMenuComponent = NavMenuComponent;

  // js/components/nav/ThemeToggle.js
  var ThemeToggle = {
    name: "ThemeToggle",
    template: `
        <button class="theme-toggle-btn" @click="toggleTheme" :title="theme === 'dark' ? '\u5207\u6362\u5230\u4EAE\u8272\u6A21\u5F0F' : '\u5207\u6362\u5230\u6697\u8272\u6A21\u5F0F'">
            {{ theme === 'dark' ? '\u{1F319}' : '\u2600\uFE0F' }}
        </button>
    `,
    data() {
      return {
        theme: StateManager.getState("theme")
      };
    },
    methods: {
      toggleTheme() {
        const newTheme = this.theme === "dark" ? "light" : "dark";
        StateManager.setState("theme", newTheme);
        document.body.setAttribute("data-theme", newTheme);
        this.theme = newTheme;
      }
    },
    mounted() {
      this.unsubscribe = StateManager.subscribe("theme", (theme) => {
        this.theme = theme;
      });
    },
    destroyed() {
      if (this.unsubscribe)
        this.unsubscribe();
    }
  };
  window.ThemeToggle = ThemeToggle;

  // js/components/nav/ConnectionBadge.js
  var ConnectionBadge = {
    name: "ConnectionBadge",
    template: `
        <div class="connection-badge" :class="statusClass">
            <span class="connection-dot"></span>
            <span class="connection-text">{{ statusText }}</span>
        </div>
    `,
    data() {
      return {
        wsConnected: StateManager.getState("wsConnected")
      };
    },
    computed: {
      statusClass() {
        return this.wsConnected ? "connected" : "disconnected";
      },
      statusText() {
        return this.wsConnected ? "\u5DF2\u8FDE\u63A5" : "\u672A\u8FDE\u63A5";
      }
    },
    mounted() {
      this.unsubscribe = StateManager.subscribe("wsConnected", (connected) => {
        this.wsConnected = connected;
      });
    },
    destroyed() {
      if (this.unsubscribe)
        this.unsubscribe();
    }
  };
  window.ConnectionBadge = ConnectionBadge;

  // js/components/nav/ReplayToggle.js
  var ReplayToggle = {
    name: "ReplayToggle",
    data() {
      return {
        replayEnabled: StateManager.getState("replayEnabled") !== void 0 ? StateManager.getState("replayEnabled") : true,
        replayMode: StateManager.getState("replayMode") || "record"
      };
    },
    async mounted() {
      try {
        const response = await ApiClient.request("GET", "/llm/mode");
        console.log("[ReplayToggle] Fetched mode from backend:", response);
        if (response && response.mode) {
          this.replayMode = response.mode;
          this.replayEnabled = response.mode === "record";
          StateManager.setState("replayMode", response.mode);
          StateManager.setState("replayEnabled", response.mode === "record");
        }
      } catch (error) {
        console.error("[ReplayToggle] Failed to fetch mode from backend:", error);
        this.replayMode = "record";
        this.replayEnabled = true;
      }
    },
    template: `
        <div class="replay-toggle" :class="{ active: replayEnabled }" :title="replayEnabled ? '\u5F55\u5236\u6A21\u5F0F' : '\u56DE\u653E\u6A21\u5F0F'" @click="toggleReplay">
            <span class="toggle-icon">{{ replayEnabled ? '\u{1F4F9}' : '\u{1F504}' }}</span>
            <span class="toggle-label">{{ replayEnabled ? '\u5F55\u5236' : '\u56DE\u653E' }}</span>
        </div>
    `,
    methods: {
      async toggleReplay() {
        const enabled = !this.replayEnabled;
        const newMode = enabled ? "record" : "loopback";
        console.log("[ReplayToggle] Toggling replay mode:", enabled ? "ON (record)" : "OFF (loopback)");
        try {
          const response = await ApiClient.request("POST", "/llm/mode", {
            mode: newMode
          });
          console.log("[ReplayToggle] Backend response:", response);
          this.replayEnabled = enabled;
          this.replayMode = newMode;
          StateManager.setState("replayEnabled", enabled);
          StateManager.setState("replayMode", newMode);
          EventBus.emit("replay:mode-changed", {
            enabled,
            mode: newMode
          });
          console.log("[ReplayToggle] Mode changed:", this.replayEnabled);
        } catch (error) {
          console.error("[ReplayToggle] Failed to set mode:", error);
          this.replayEnabled = enabled;
          this.replayMode = newMode;
          StateManager.setState("replayEnabled", enabled);
          StateManager.setState("replayMode", newMode);
          EventBus.emit("replay:mode-changed", {
            enabled,
            mode: newMode
          });
        }
      }
    }
  };
  window.ReplayToggle = ReplayToggle;

  // js/components/nav/NavBarComponent.js
  var NavBarComponent = {
    name: "NavBarComponent",
    components: {
      NavMenuComponent,
      ThemeToggle,
      ConnectionBadge,
      ReplayToggle
    },
    data() {
      return {
        menus: StateManager.getState("menus"),
        activePage: StateManager.getState("currentPage") || "chat"
      };
    },
    template: `
        <nav class="top-nav">
            <div class="logo">
                <span class="logo-icon">\u{1F916}</span>
                <span class="logo-text">AI \u52A9\u624B</span>
            </div>
            <nav-menu-component
                :menus="menus"
                :activePage="activePage">
            </nav-menu-component>
            <div class="right-section">
                <replay-toggle></replay-toggle>
                <theme-toggle></theme-toggle>
                <connection-badge></connection-badge>
            </div>
        </nav>
    `,
    mounted() {
      console.log("[NavBar] Mounted with menus:", this.menus);
      console.log("[NavBar] Initial activePage:", this.activePage);
      StateManager.subscribe("currentPage", (newPage) => {
        console.log("[NavBar] Page changed to:", newPage);
        this.activePage = newPage;
      });
      EventBus.on("menu:click", ({ menu }) => {
        console.log("[NavBar] Menu clicked:", menu);
      });
    }
  };
  window.NavBarComponent = NavBarComponent;

  // js/components/chat/ChatSidebarComponent.js
  var ChatSidebarComponent = {
    name: "ChatSidebarComponent",
    props: {
      projectId: { type: String, default: null },
      sessions: { type: Array, default: () => [] },
      currentSessionId: { type: String, default: null }
    },
    template: `
        <aside class="chat-sidebar">
            <div class="chat-sidebar-header">
                <select v-model="selectedProject" @change="handleProjectChange" class="project-select">
                    <option value="">\u9009\u62E9\u9879\u76EE</option>
                    <option v-for="p in projects" :key="p.id" :value="p.id">
                        {{ p.name }}
                    </option>
                </select>
                <button 
                    class="btn btn-sm btn-outline" 
                    @click="handleCreateSession"
                    :disabled="!selectedProject"
                    :title="selectedProject ? '\u65B0\u5EFA\u4F1A\u8BDD' : '\u8BF7\u5148\u9009\u62E9\u9879\u76EE'">
                    + \u65B0\u5EFA
                </button>
            </div>
            <div class="chat-sidebar-content">
                <div class="section-title">\u{1F4AC} \u4F1A\u8BDD\u5217\u8868</div>
                <div class="session-list">
                    <div
                        v-for="session in sessions"
                        :key="session.id"
                        class="session-item"
                        :class="{ active: session.id === currentSessionId }"
                        @click="handleSessionSelect(session.id)">
                        <span class="session-title">{{ session.title || '\u672A\u547D\u540D\u4F1A\u8BDD' }}</span>
                        <span class="session-date">{{ formatDate(session.updated_at) }}</span>
                    </div>
                    <div v-if="!sessions.length" class="empty-hint">
                        {{ selectedProject ? '\u6682\u65E0\u4F1A\u8BDD\uFF0C\u70B9\u51FB\u4E0A\u65B9"\u65B0\u5EFA"\u6309\u94AE\u521B\u5EFA' : '\u8BF7\u5148\u9009\u62E9\u9879\u76EE' }}
                    </div>
                </div>
            </div>
        </aside>
    `,
    data() {
      return {
        projects: [],
        selectedProject: this.projectId || ""
      };
    },
    async mounted() {
      console.log("[ChatSidebar] Mounted with props:", {
        projectId: this.projectId,
        sessions: this.sessions,
        currentSessionId: this.currentSessionId
      });
      await this.loadProjects();
      EventBus.on("project:loaded", ({ projects }) => {
        console.log("[ChatSidebar] Projects loaded:", projects);
        this.projects = projects;
      });
      EventBus.on("session:loaded", ({ sessions }) => {
        console.log("[ChatSidebar] Sessions loaded:", sessions);
        this.sessions = sessions;
      });
    },
    methods: {
      async loadProjects() {
        try {
          await ProjectManager.getProjects();
          this.projects = StateManager.getState("projects");
        } catch (e) {
          console.error("Load projects error:", e);
        }
      },
      handleProjectChange() {
        StateManager.setState("currentProjectId", this.selectedProject);
        if (this.selectedProject) {
          SessionManager.getSessions(this.selectedProject);
        }
      },
      handleSessionSelect(sessionId) {
        SessionManager.switchSession(sessionId);
      },
      async handleCreateSession() {
        const projectId = this.selectedProject;
        if (projectId) {
          await SessionManager.createSession(projectId);
        }
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "";
      }
    }
  };
  window.ChatSidebarComponent = ChatSidebarComponent;

  // js/components/chat/UserMessageComponent.js
  var UserMessageComponent = {
    name: "UserMessageComponent",
    props: {
      message: { type: Object, required: true }
    },
    template: `
        <div class="message-item user-message" 
             :data-message-id="message.id"
             :data-message-role="message.role">
            <div class="message-avatar">\u{1F464}</div>
            <div class="message-content">
                <div class="message-bubble">
                    {{ message.content }}
                </div>
                <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
        </div>
    `,
    methods: {
      formatTime(timestamp) {
        return timestamp ? new Date(timestamp).toLocaleTimeString() : "";
      }
    }
  };
  window.UserMessageComponent = UserMessageComponent;

  // js/components/chat/ResponseBlockComponent.js
  var ResponseBlockComponent = {
    name: "ResponseBlockComponent",
    props: {
      block: {
        type: Object,
        required: true,
        validator: (block) => {
          return block && block.responseId && block.requestId;
        }
      }
    },
    data() {
      return {
        debugMode: false
      };
    },
    mounted() {
      if (this.debugMode) {
        console.log("[ResponseBlock] mounted, block:", this.block);
        console.log("[ResponseBlock] block type:", typeof this.block);
        console.log("[ResponseBlock] block.responseId:", this.block.responseId);
        console.log("[ResponseBlock] block.thinkContent:", this.block.thinkContent);
        console.log("[ResponseBlock] block.textContent:", this.block.textContent);
        console.log("[ResponseBlock] block.toolCalls:", this.block.toolCalls);
      }
    },
    template: `
        <div class="response-block" 
             :class="'status-' + (block.status || 'completed')"
             :data-response-id="block.responseId"
             :data-request-id="block.requestId">
            <!-- DEBUG INFO -->
            <div v-if="debugMode" class="debug-info">
                [DEBUG] responseId: {{ block.responseId }}, 
                think: {{ !!block.thinkContent }}, 
                reason: {{ !!block.reasonContent }},
                text: {{ !!block.textContent }}, 
                tools: {{ block.toolCalls ? block.toolCalls.length : 0 }}
            </div>
            
            <!-- thinking \u601D\u8003\u5757 -->
            <think-block-component
                v-if="block.thinkContent"
                :content="block.thinkContent"
                :expanded="false"
                :status="block.status"
                :data-response-id="block.responseId">
            </think-block-component>
            
            <!-- reasoning \u63A8\u7406\u5757 -->
            <reason-block-component
                v-if="block.reasonContent"
                :content="block.reasonContent"
                :expanded="false"
                :status="block.status"
                :data-response-id="block.responseId">
            </reason-block-component>
            
            <!-- \u6587\u672C\u5757 -->
            <text-block-component
                :content="block.textContent"
                :streaming="block.status === 'streaming'"
                :status="block.status"
                :data-response-id="block.responseId">
            </text-block-component>
            
            <!-- \u5DE5\u5177\u8C03\u7528\u5757 -->
            <div class="tool-calls" v-if="block.toolCalls && block.toolCalls.length">
                <tool-card-component
                    v-for="tool in block.toolCalls"
                    :key="tool.callId"
                    :toolCall="tool">
                </tool-card-component>
            </div>
        </div>
    `
  };
  window.ResponseBlockComponent = ResponseBlockComponent;

  // js/components/chat/AssistantMessageComponent.js
  var AssistantMessageComponent = {
    name: "AssistantMessageComponent",
    components: {
      ResponseBlockComponent
    },
    props: {
      message: {
        type: Object,
        required: true,
        validator: (msg) => {
          return msg && msg.id && msg.role === "assistant";
        }
      }
    },
    data() {
      return {
        debugMode: false
      };
    },
    mounted() {
      if (this.debugMode) {
        console.log("[AssistantMessage] mounted, message:", this.message);
        console.log("[AssistantMessage] message.id:", this.message.id);
        console.log("[AssistantMessage] responseBlocks:", this.message.responseBlocks);
        console.log("[AssistantMessage] responseBlocks type:", typeof this.message.responseBlocks);
        console.log("[AssistantMessage] responseBlocks length:", this.message.responseBlocks ? this.message.responseBlocks.length : 0);
        console.log("[AssistantMessage] responseBlocks is Array:", Array.isArray(this.message.responseBlocks));
      }
    },
    computed: {
      blocks() {
        const responseBlockIds = this.message.responseBlocks || [];
        console.log("[AssistantMessage] computed blocks, responseBlockIds:", responseBlockIds.length);
        const result = responseBlockIds.map((id) => {
          const block = window.StateManager.state.responseBlocks.get(id);
          if (!block) {
            console.warn(`[AssistantMessage] ResponseBlock not found for id: ${id}`);
          }
          return block;
        }).filter(Boolean);
        console.log("[AssistantMessage] computed blocks, resolved:", result.length);
        return result;
      }
    },
    template: `
        <div class="message-item assistant-message"
             :data-message-id="message.id"
             :data-message-role="message.role"
             :data-dialog-id="message.dialogId">
            <div class="message-avatar">\u{1F916}</div>
            <div class="message-content">
                <!-- DEBUG INFO -->
                <div v-if="debugMode" class="debug-info">
                    [DEBUG] message.id: {{ message.id }}, 
                    responseBlocks: {{ blocks.length }}
                </div>
                <!-- \u591A\u6B21 LLM \u4EA4\u4E92\uFF0C\u6BCF\u6B21\u4E00\u4E2A\u54CD\u5E94\u5757 -->
                <response-block-component
                    v-for="responseBlock in blocks"
                    :key="responseBlock.responseId"
                    :block="responseBlock">
                </response-block-component>
            </div>
        </div>
    `
  };
  window.AssistantMessageComponent = AssistantMessageComponent;

  // js/components/chat/ThinkBlockComponent.js
  var ThinkBlockComponent = {
    name: "ThinkBlockComponent",
    props: {
      content: { type: String, default: "" },
      expanded: { type: Boolean, default: false },
      dataResponseId: { type: String, default: "" }
    },
    template: `
        <details class="think-block" 
                 :open="expanded"
                 :data-response-id="dataResponseId"
                 :data-think-content="content ? 'true' : 'false'">
            <summary>
                <span class="think-icon">\u{1F9E0}</span>
                <span>\u601D\u8003\u8FC7\u7A0B</span>
            </summary>
            <div class="think-content">{{ content }}</div>
        </details>
    `
  };
  window.ThinkBlockComponent = ThinkBlockComponent;

  // js/components/chat/ReasonBlockComponent.js
  var ReasonBlockComponent = {
    name: "ReasonBlockComponent",
    props: {
      content: { type: String, default: "" },
      expanded: { type: Boolean, default: false },
      dataResponseId: { type: String, default: "" }
    },
    template: `
        <details class="reason-block" 
                 :open="expanded"
                 :data-response-id="dataResponseId"
                 :data-reason-content="content ? 'true' : 'false'">
            <summary>
                <span class="reason-icon">\u{1F4A1}</span>
                <span>\u63A8\u7406\u8FC7\u7A0B</span>
            </summary>
            <div class="reason-content">{{ content }}</div>
        </details>
    `
  };
  window.ReasonBlockComponent = ReasonBlockComponent;

  // js/components/chat/TextBlockComponent.js
  var TextBlockComponent = {
    name: "TextBlockComponent",
    props: {
      content: { type: String, default: "" },
      streaming: { type: Boolean, default: false },
      dataResponseId: { type: String, default: "" }
    },
    template: `
        <div class="text-block" 
             :class="{ streaming }"
             :data-response-id="dataResponseId">
            <span class="text-content" v-html="renderedContent"></span>
            <span v-if="streaming" class="cursor">\u258A</span>
        </div>
    `,
    computed: {
      renderedContent() {
        return this.markdownRender(this.content);
      }
    },
    methods: {
      markdownRender(text) {
        if (!text)
          return "";
        return text.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>').replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/\*([^*]+)\*/g, "<em>$1</em>").replace(/\n/g, "<br>");
      }
    }
  };
  window.TextBlockComponent = TextBlockComponent;

  // js/components/chat/ToolCardComponent.js
  var ToolCardComponent = {
    name: "ToolCardComponent",
    props: {
      toolCall: { type: Object, required: true }
    },
    template: `
        <div class="tool-execution-card" 
             :class="'status-' + toolCall.status"
             :data-tool-call-id="toolCall.callId"
             :data-tool-name="toolCall.toolName">
            <div class="tool-card-header">
                <span class="tool-icon">\u{1F527}</span>
                <span class="tool-name">{{ toolCall.toolName }}</span>
                <span class="tool-status-badge" :class="toolCall.status">
                    {{ statusLabel }}
                </span>
            </div>
            <div class="tool-section">
                <div class="section-header">\u8C03\u7528\u53C2\u6570</div>
                <pre class="section-content">{{ formatArgs(toolCall.args) }}</pre>
            </div>
            <div class="tool-section" v-if="toolCall.output">
                <div class="section-header">\u6267\u884C\u8F93\u51FA</div>
                <pre class="section-content">{{ toolCall.output }}</pre>
            </div>
            <div class="tool-section" v-if="toolCall.error">
                <div class="section-header error-header">\u274C \u9519\u8BEF\u4FE1\u606F</div>
                <pre class="section-content error-content">{{ toolCall.error }}</pre>
            </div>
            <div class="tool-section" v-if="toolCall.result && !toolCall.error">
                <div class="section-header">\u6267\u884C\u7ED3\u679C</div>
                <pre class="section-content">{{ formatResult(toolCall.result) }}</pre>
            </div>
        </div>
    `,
    computed: {
      statusLabel() {
        const labels = {
          pending: "\u23F3 \u6267\u884C\u4E2D",
          running: "\u23F3 \u6267\u884C\u4E2D",
          completed: "\u2705 \u5B8C\u6210",
          failed: "\u274C \u5931\u8D25"
        };
        return labels[this.toolCall.status] || "\u23F3 \u6267\u884C\u4E2D";
      }
    },
    methods: {
      formatArgs(args) {
        try {
          return typeof args === "string" ? args : JSON.stringify(args, null, 2);
        } catch (e) {
          return String(args);
        }
      },
      formatResult(result) {
        try {
          return typeof result === "string" ? result : JSON.stringify(result, null, 2);
        } catch (e) {
          return String(result);
        }
      }
    }
  };
  window.ToolCardComponent = ToolCardComponent;

  // js/components/chat/ChatInputComponent.js
  var ChatInputComponent = {
    name: "ChatInputComponent",
    template: `
        <div class="chat-input-area">
            <div class="chat-input-wrapper">
                <textarea
                    ref="textarea"
                    v-model="inputText"
                    :placeholder="placeholder"
                    rows="1"
                    @keydown="handleKeydown"
                    @input="autoResize"
                    :disabled="isGenerating">
                </textarea>
                <button class="send-btn" @click="handleSend" :disabled="!canSend">
                    <span v-if="isGenerating" class="spinner">\u23F3</span>
                    <span v-else>\u27A4</span>
                </button>
                <!-- \u7EC8\u6B62\u5BF9\u8BDD\u6309\u94AE -->
                <button v-if="isGenerating" class="stop-btn" @click="handleStop">
                    \u2715
                </button>
            </div>
            <!-- \u9519\u8BEF\u63D0\u793A -->
            <div v-if="errorMessage" class="error-message">
                \u274C {{ errorMessage }}
            </div>
        </div>
    `,
    data() {
      return {
        inputText: "",
        placeholder: "\u8F93\u5165\u6D88\u606F... (Enter \u53D1\u9001\uFF0CShift+Enter \u6362\u884C)",
        isGenerating: false,
        errorMessage: ""
      };
    },
    mounted() {
      console.log("[ChatInput] Mounted");
      this.isGenerating = StateManager.getState("isGenerating");
      this.generatingSubscription = StateManager.subscribe("isGenerating", (value) => {
        console.log("[ChatInput] isGenerating changed:", value);
        this.isGenerating = value;
      });
      this.errorSubscription = StateManager.subscribe("lastError", (value) => {
        if (value) {
          this.errorMessage = value.message || "\u672A\u77E5\u9519\u8BEF";
          setTimeout(() => {
            this.errorMessage = "";
          }, 3e3);
        }
      });
      EventBus.on("message:added", () => {
        this.isGenerating = true;
      });
      EventBus.on("event.llm.call_completed_end", () => {
        this.isGenerating = false;
      });
      EventBus.on("event_dialog.completed", () => {
        this.isGenerating = false;
        StateManager.setState("isGenerating", false);
        console.log("[ChatInput] \u6536\u5230\u5BF9\u8BDD\u5B8C\u6210\u4E8B\u4EF6");
      });
      EventBus.on("event.tool.call_completed", () => {
      });
      EventBus.on("event_llm.call_failed", (payload) => {
        console.log("[ChatInput] \u6536\u5230 LLM\u8C03\u7528\u5931\u8D25\u4E8B\u4EF6:", payload);
        this.isGenerating = false;
        StateManager.setState("isGenerating", false);
      });
      EventBus.on("event_llm.response_classified", (payload) => {
        console.log("[ChatInput] \u6536\u5230 LLM\u54CD\u5E94\u5206\u7C7B\u4E8B\u4EF6:", payload);
        const eventData = payload.data || payload;
        const data = eventData.data || eventData;
        console.log("[ChatInput] \u89E3\u6790\u540E\u7684\u6570\u636E:", data);
        console.log("[ChatInput] finish_reason:", data?.finish_reason);
        console.log("[ChatInput] success:", data?.success);
        console.log("[ChatInput] content:", data?.content);
        if (data && (data.finish_reason === "error" || data.success === false)) {
          console.log("[ChatInput] \u68C0\u6D4B\u5230\u9519\u8BEF\uFF0C\u521B\u5EFA\u9519\u8BEF\u54CD\u5E94");
          const errorContent = data.content || data.error || "LLM\u8C03\u7528\u5931\u8D25\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5";
          this.createErrorResponse(errorContent);
        } else {
          console.log("[ChatInput] \u975E\u9519\u8BEF\u60C5\u51B5\uFF0C\u4E0D\u521B\u5EFA\u9519\u8BEF\u54CD\u5E94");
        }
        this.isGenerating = false;
        StateManager.setState("isGenerating", false);
      });
    },
    beforeDestroy() {
      if (this.generatingSubscription) {
        this.generatingSubscription();
      }
      if (this.errorSubscription) {
        this.errorSubscription();
      }
    },
    computed: {
      canSend() {
        return this.inputText.trim() && StateManager.getState("currentSessionId") && !this.isGenerating;
      }
    },
    methods: {
      handleKeydown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.handleSend();
        }
      },
      handleSend() {
        if (!this.canSend)
          return;
        this.errorMessage = "";
        const content = this.inputText.trim();
        const sessionId = StateManager.getState("currentSessionId");
        const userMessage = {
          id: "user-" + Date.now(),
          role: "user",
          content,
          sessionId,
          timestamp: Date.now()
        };
        const messages = [...StateManager.getState("messages") || [], userMessage];
        StateManager.setState("messages", messages);
        StateManager.setState("isGenerating", true);
        EventBus.emit("message:added", { message: userMessage, messages });
        ChatManager.sendMessage(content);
        this.inputText = "";
        this.resetTextarea();
      },
      autoResize() {
        const textarea = this.$refs.textarea;
        if (textarea) {
          textarea.style.height = "auto";
          textarea.style.height = Math.min(textarea.scrollHeight, 150) + "px";
        }
      },
      resetTextarea() {
        const textarea = this.$refs.textarea;
        if (textarea) {
          textarea.style.height = "auto";
        }
      },
      handleStop() {
        if (!this.isGenerating)
          return;
        console.log("[ChatInput] \u7528\u6237\u8BF7\u6C42\u7EC8\u6B62\u5BF9\u8BDD");
        this.isGenerating = false;
        StateManager.setState("isGenerating", false);
        const sessionId = StateManager.getState("currentSessionId");
        const stopMessage = {
          id: "user-" + Date.now(),
          role: "user",
          content: "\u7528\u6237\u7EC8\u6B62\u4E86\u5F53\u524D\u5BF9\u8BDD",
          sessionId,
          timestamp: Date.now(),
          isSystem: true
        };
        const messages = [...StateManager.getState("messages") || [], stopMessage];
        StateManager.setState("messages", messages);
        EventBus.emit("dialog:stopped", { message: stopMessage });
        ChatManager.stopDialog();
      },
      createErrorResponse(errorContent) {
        console.log("[ChatInput] \u521B\u5EFA\u9519\u8BEF\u54CD\u5E94:", errorContent);
        const sessionId = StateManager.getState("currentSessionId");
        const assistantMessageId = StateManager.getState("currentAssistantMessageId");
        const dialogId = StateManager.getState("currentDialogId");
        const timestamp = Date.now();
        const responseId = "error-resp-" + timestamp;
        const responseBlock = {
          responseId,
          dialogId,
          requestId: "error-req-" + timestamp,
          timestamp,
          status: "completed",
          // 已完成状态
          isError: true,
          textContent: errorContent,
          // 直接设置 textContent，供 TextBlockComponent 使用
          thinkContent: "",
          reasonContent: "",
          toolCalls: [],
          __subscriptions: []
        };
        StateManager.state.responseBlocks.set(responseId, responseBlock);
        let messages = StateManager.getState("messages") || [];
        let assistantMessage = messages.find((m) => m.id === assistantMessageId && m.role === "assistant");
        if (assistantMessage) {
          assistantMessage.responseBlocks = assistantMessage.responseBlocks || [];
          assistantMessage.responseBlocks.push(responseId);
          console.log("[ChatInput] \u66F4\u65B0\u73B0\u6709\u52A9\u624B\u6D88\u606F\uFF0C\u6DFB\u52A0 ResponseBlock:", responseId);
        } else {
          assistantMessage = {
            id: assistantMessageId || "assistant-" + timestamp,
            role: "assistant",
            content: errorContent,
            sessionId,
            dialogId,
            timestamp,
            isError: true,
            responseBlocks: [responseId]
          };
          messages = [...messages, assistantMessage];
          console.log("[ChatInput] \u521B\u5EFA\u65B0\u7684\u52A9\u624B\u6D88\u606F:", assistantMessage.id);
        }
        StateManager.setState("messages", messages);
        StateManager.setState("currentResponseBlockId", responseId);
        EventBus.emit("component:response-block-created", { responseId, block: responseBlock });
        EventBus.emit("message:added", { message: assistantMessage, messages });
        console.log("[ChatInput] \u9519\u8BEF\u54CD\u5E94\u521B\u5EFA\u5B8C\u6210");
      }
    }
  };
  window.ChatInputComponent = ChatInputComponent;

  // js/components/chat/ChatPageComponent.js
  var ChatPageComponent = {
    name: "ChatPageComponent",
    components: {
      ChatSidebarComponent,
      UserMessageComponent,
      AssistantMessageComponent,
      ResponseBlockComponent,
      ThinkBlockComponent,
      ReasonBlockComponent,
      TextBlockComponent,
      ToolCardComponent,
      ChatInputComponent
    },
    template: `
        <div class="chat-page">
            <div class="chat-layout">
                <chat-sidebar-component
                    :projectId="currentProjectId"
                    :sessions="sessions"
                    :currentSessionId="currentSessionId">
                </chat-sidebar-component>
                <main class="chat-main">
                    <div class="messages-container" ref="messagesContainer">
                        <div v-if="!messages.length" class="empty-state">
                            <div class="empty-icon">\u{1F4AC}</div>
                            <div class="empty-text">\u9009\u62E9\u6216\u521B\u5EFA\u4E00\u4E2A\u4F1A\u8BDD\u5F00\u59CB\u5BF9\u8BDD</div>
                        </div>
                        <template v-for="msg in messages">
                            <user-message-component v-if="msg.role === 'user'" :key="msg.id" :message="msg"></user-message-component>
                            <assistant-message-component v-else :key="msg.id" :message="msg"></assistant-message-component>
                        </template>
                    </div>
                    <chat-input-component></chat-input-component>
                </main>
            </div>
        </div>
    `,
    data() {
      return {
        messages: [],
        sessions: StateManager.getState("sessions") || []
      };
    },
    computed: {
      currentProjectId() {
        return StateManager.getState("currentProjectId");
      },
      currentSessionId() {
        return StateManager.getState("currentSessionId");
      }
    },
    mounted() {
      console.log("[ChatPage] Mounted, initial sessions:", this.sessions);
      console.log("[ChatPage] Initial projectId:", this.currentProjectId);
      ChatManager.init();
      ComponentSubscriptions.init();
      EventBus.on("session:loaded", ({ sessions }) => {
        console.log("[ChatPage] Sessions loaded:", sessions);
        this.sessions = sessions;
      });
      EventBus.on("session:switching", ({ sessionId }) => {
        console.log("[ChatPage] Session switching to:", sessionId);
        this.messages = [];
        ChatManager.resetState(sessionId);
        ComponentSubscriptions.clearAll();
      });
      EventBus.on("state:updated", ({ key, value }) => {
        if (key === "messages") {
          this.messages = value;
        }
      });
    }
  };
  window.ChatPageComponent = ChatPageComponent;

  // js/components/workspace/FileTreeComponent.js
  var FileTreeComponent = {
    name: "FileTreeComponent",
    props: {
      workspaceId: { type: String, default: null }
    },
    template: `
        <div class="file-tree">
            <div class="tree-header">
                <span class="tree-title">\u{1F4C2} \u5DE5\u4F5C\u533A\u6587\u4EF6</span>
                <button class="btn btn-sm" @click="refresh">\u{1F504}</button>
            </div>
            <div class="tree-content">
                <div v-if="!workspaceId" class="empty-state">
                    \u8BF7\u5148\u9009\u62E9\u9879\u76EE\u548C\u5DE5\u4F5C\u533A
                </div>
                <div v-else-if="loading" class="loading">\u52A0\u8F7D\u4E2D...</div>
                <div v-else class="tree-nodes">
                    <div v-for="node in treeData" :key="node.path" class="tree-node" @click="handleNodeClick(node)">
                        <span class="node-icon">{{ node.type === 'directory' ? '\u{1F4C1}' : '\u{1F4C4}' }}</span>
                        <span class="node-name">{{ node.name }}</span>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        treeData: [],
        loading: false
      };
    },
    watch: {
      workspaceId() {
        this.loadTree();
      }
    },
    methods: {
      async loadTree() {
        if (!this.workspaceId)
          return;
        this.loading = true;
        try {
          const result = await ApiClient.get(`/workspaces/${this.workspaceId}/tree`);
          this.treeData = result.data || result || [];
        } catch (error) {
          console.error("Load tree error:", error);
        } finally {
          this.loading = false;
        }
      },
      handleNodeClick(node) {
        if (node.type === "file") {
          EventBus.emit("file:selected", { file: node });
        }
      },
      refresh() {
        this.loadTree();
      }
    }
  };
  window.FileTreeComponent = FileTreeComponent;

  // js/components/admin/ProjectPageComponent.js
  var ProjectPageComponent = {
    name: "ProjectPageComponent",
    template: `
        <div class="admin-page page-container" id="page-projects">
            <div class="admin-header">
                <h2>\u{1F4C1} \u9879\u76EE\u7BA1\u7406</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + \u65B0\u5EFA\u9879\u76EE
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="\u641C\u7D22\u9879\u76EE..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u9879\u76EE\u540D\u79F0</th>
                                <th>\u63CF\u8FF0</th>
                                <th>\u72B6\u6001</th>
                                <th>\u4F1A\u8BDD\u6570</th>
                                <th>\u5DE5\u4F5C\u533A</th>
                                <th>\u6A21\u578B</th>
                                <th>\u521B\u5EFA\u65F6\u95F4</th>
                                <th>\u64CD\u4F5C</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="project in projects" :key="project.id">
                                <td>{{ project.name }}</td>
                                <td>{{ project.description || '-' }}</td>
                                <td>
                                    <span class="status-badge" :class="project.status">
                                        {{ project.status === 'active' ? '\u6D3B\u8DC3' : '\u505C\u7528' }}
                                    </span>
                                </td>
                                <td>{{ project.session_count || 0 }}</td>
                                <td>{{ getWorkspaceName(project.workspace_config_id) }}</td>
                                <td>{{ getModelName(project.model_config_id) }}</td>
                                <td>{{ formatDate(project.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(project)">\u7F16\u8F91</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(project.id)">\u5220\u9664</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!projects.length" class="empty-table">
                        \u6682\u65E0\u9879\u76EE\u6570\u636E
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '\u7F16\u8F91\u9879\u76EE' : '\u65B0\u5EFA\u9879\u76EE' }}</h3>
                        <button class="modal-close" @click="closeModal">\xD7</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>\u9879\u76EE\u540D\u79F0 *</label>
                            <input type="text" v-model="formData.name" required placeholder="\u8BF7\u8F93\u5165\u9879\u76EE\u540D\u79F0">
                        </div>
                        <div class="form-group">
                            <label>\u63CF\u8FF0</label>
                            <textarea v-model="formData.description" placeholder="\u8BF7\u8F93\u5165\u9879\u76EE\u63CF\u8FF0"></textarea>
                        </div>
                        <div class="form-group">
                            <label>\u5173\u8054\u5DE5\u4F5C\u533A</label>
                            <select v-model="formData.workspace_config_id">
                                <option value="">\u4E0D\u4F7F\u7528\u5DE5\u4F5C\u533A</option>
                                <option v-for="w in workspaces" :key="w.id" :value="w.id">
                                    {{ w.name }}
                                </option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>\u5173\u8054\u6A21\u578B</label>
                            <select v-model="formData.model_config_id">
                                <option value="">\u4E0D\u4F7F\u7528\u6A21\u578B</option>
                                <option v-for="m in models" :key="m.id" :value="m.id">
                                    {{ m.name }} ({{ getModelTypeName(m.type) }})
                                </option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>\u72B6\u6001</label>
                            <select v-model="formData.status">
                                <option value="active">\u6D3B\u8DC3</option>
                                <option value="inactive">\u505C\u7528</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">\u53D6\u6D88</button>
                        <button class="btn btn-primary" @click="handleSave">\u4FDD\u5B58</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        projects: [],
        workspaces: [],
        models: [],
        searchQuery: "",
        showModal: false,
        currentProject: null,
        formData: {
          name: "",
          description: "",
          workspace_config_id: "",
          model_config_id: "",
          tool_config_ids: [],
          status: "active"
        }
      };
    },
    computed: {
      isEdit() {
        return !!this.currentProject;
      }
    },
    async mounted() {
      console.log("[ProjectPage] Mounted, loading projects...");
      EventBus.on("project:loaded", ({ projects }) => {
        console.log("[ProjectPage] project:loaded event received");
        console.log("[ProjectPage] Projects from event:", projects);
        console.log("[ProjectPage] First project from event:", projects[0]);
        console.log("[ProjectPage] First project.id from event:", projects[0]?.id);
        this.projects = projects;
      });
      EventBus.on("project:created", ({ project }) => {
        this.projects.push(project);
      });
      EventBus.on("project:updated", ({ project }) => {
        const index = this.projects.findIndex((p) => p.id === project.id);
        if (index > -1)
          this.projects.splice(index, 1, project);
      });
      EventBus.on("project:deleted", ({ id }) => {
        this.projects = this.projects.filter((p) => p.id !== id);
      });
      await this.loadProjects();
      await this.loadWorkspaces();
      await this.loadModels();
      const stateProjects = StateManager.getState("projects");
      if (stateProjects && stateProjects.length > 0 && this.projects.length === 0) {
        console.log("[ProjectPage] Restoring from StateManager:", stateProjects);
        this.projects = stateProjects;
      }
    },
    methods: {
      async loadProjects() {
        await ProjectManager.getProjects({ search: this.searchQuery });
      },
      async loadWorkspaces() {
        try {
          const workspaces = await WorkspaceManager.getWorkspaces();
          this.workspaces = Array.isArray(workspaces) ? workspaces : [];
        } catch (error) {
          console.error("[ProjectPage] Failed to load workspaces:", error);
          this.workspaces = [];
        }
      },
      async loadModels() {
        try {
          const models = await ModelManager.getModels();
          this.models = Array.isArray(models) ? models : [];
        } catch (error) {
          console.error("[ProjectPage] Failed to load models:", error);
          this.models = [];
        }
      },
      handleSearch() {
        this.loadProjects();
      },
      showCreateModal() {
        this.currentProject = null;
        this.formData = { name: "", description: "", workspace_config_id: "", model_config_id: "", tool_config_ids: [], status: "active" };
        this.showModal = true;
      },
      async handleEdit(project) {
        console.log("[ProjectPage] handleEdit called");
        console.log("[ProjectPage] Project to edit:", project);
        this.currentProject = {
          ...project,
          id: project.id || project.project_id
        };
        await Promise.all([
          this.loadWorkspaces(),
          this.loadModels()
        ]);
        console.log("[ProjectPage] workspaces loaded:", this.workspaces.length);
        console.log("[ProjectPage] models loaded:", this.models.length);
        console.log("[ProjectPage] project workspace_config_id:", project.workspace_config_id);
        console.log("[ProjectPage] project model_config_id:", project.model_config_id);
        this.formData = {
          name: project.name,
          description: project.description || "",
          workspace_config_id: project.workspace_config_id || "",
          model_config_id: project.model_config_id || "",
          tool_config_ids: project.tool_config_ids || [],
          status: project.status || "active"
        };
        console.log("[ProjectPage] formData set:", this.formData);
        this.showModal = true;
      },
      async handleSave() {
        if (!this.formData.name) {
          alert("\u9879\u76EE\u540D\u79F0\u4E0D\u80FD\u4E3A\u7A7A");
          return;
        }
        console.log("[ProjectPage] Saving project with data:", this.formData);
        if (this.currentProject) {
          await ProjectManager.updateProject(this.currentProject.id, this.formData);
        } else {
          await ProjectManager.createProject(this.formData);
        }
        this.closeModal();
      },
      async handleDelete(id) {
        if (confirm("\u786E\u5B9A\u8981\u5220\u9664\u8BE5\u9879\u76EE\u5417\uFF1F")) {
          await ProjectManager.deleteProject(id);
        }
      },
      closeModal() {
        this.showModal = false;
        this.currentProject = null;
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "-";
      },
      getWorkspaceName(workspaceId) {
        if (!workspaceId)
          return "-";
        const workspace = this.workspaces.find((w) => w.id === workspaceId);
        return workspace ? workspace.name : "-";
      },
      getModelName(modelId) {
        if (!modelId)
          return "-";
        const model = this.models.find((m) => m.id === modelId);
        return model ? model.name : "-";
      },
      getModelTypeName(type) {
        const types = { chat: "\u5BF9\u8BDD", tool: "\u5DE5\u5177", embed: "\u5D4C\u5165" };
        return types[type] || type;
      }
    }
  };
  window.ProjectPageComponent = ProjectPageComponent;

  // js/components/admin/WorkspacePageComponent.js
  var WorkspacePageComponent = {
    name: "WorkspacePageComponent",
    template: `
        <div class="admin-page page-container" id="page-workspaces">
            <div class="admin-header">
                <h2>\u{1F4C2} \u5DE5\u4F5C\u533A\u7BA1\u7406</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + \u65B0\u5EFA\u5DE5\u4F5C\u533A
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="\u641C\u7D22\u5DE5\u4F5C\u533A..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u5DE5\u4F5C\u533A\u540D\u79F0</th>
                                <th>\u6839\u8DEF\u5F84</th>
                                <th>\u7C7B\u578B</th>
                                <th>\u7F16\u7801</th>
                                <th>\u521B\u5EFA\u65F6\u95F4</th>
                                <th>\u64CD\u4F5C</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="workspace in workspaces" :key="workspace.id">
                                <td>{{ workspace.name }}</td>
                                <td>{{ workspace.root_path }}</td>
                                <td>{{ workspace.type === 'local' ? '\u672C\u5730' : '\u8FDC\u7A0B' }}</td>
                                <td>{{ workspace.encoding }}</td>
                                <td>{{ formatDate(workspace.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(workspace)">\u7F16\u8F91</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(workspace.id)">\u5220\u9664</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!workspaces.length" class="empty-table">
                        \u6682\u65E0\u5DE5\u4F5C\u533A\u6570\u636E
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '\u7F16\u8F91\u5DE5\u4F5C\u533A' : '\u65B0\u5EFA\u5DE5\u4F5C\u533A' }}</h3>
                        <button class="modal-close" @click="closeModal">\xD7</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>\u5DE5\u4F5C\u533A\u540D\u79F0 *</label>
                            <input type="text" v-model="formData.name" required placeholder="\u8BF7\u8F93\u5165\u5DE5\u4F5C\u533A\u540D\u79F0">
                        </div>
                        <div class="form-group">
                            <label>\u6839\u8DEF\u5F84</label>
                            <input type="text" v-model="formData.root_path" placeholder="\u5DE5\u4F5C\u533A\u6839\u8DEF\u5F84">
                        </div>
                        <div class="form-group">
                            <label>\u7C7B\u578B</label>
                            <select v-model="formData.type">
                                <option value="local">\u672C\u5730</option>
                                <option value="remote">\u8FDC\u7A0B</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>\u7F16\u7801</label>
                            <input type="text" v-model="formData.encoding" placeholder="utf-8">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">\u53D6\u6D88</button>
                        <button class="btn btn-primary" @click="handleSave">\u4FDD\u5B58</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        workspaces: [],
        searchQuery: "",
        showModal: false,
        currentWorkspace: null,
        formData: {
          name: "",
          root_path: "",
          type: "local",
          encoding: "utf-8",
          excluded_patterns: []
        }
      };
    },
    computed: {
      isEdit() {
        return !!this.currentWorkspace;
      }
    },
    async mounted() {
      console.log("[WorkspacePage] Mounted, loading workspaces...");
      EventBus.on("workspace:loaded", ({ workspaces }) => {
        console.log("[WorkspacePage] Workspaces loaded:", workspaces);
        this.workspaces = workspaces;
      });
      EventBus.on("workspace:created", ({ workspace }) => {
        this.workspaces.push(workspace);
      });
      EventBus.on("workspace:updated", ({ workspace }) => {
        const index = this.workspaces.findIndex((w) => w.id === workspace.id);
        if (index > -1)
          this.workspaces.splice(index, 1, workspace);
      });
      EventBus.on("workspace:deleted", ({ id }) => {
        this.workspaces = this.workspaces.filter((w) => w.id !== id);
      });
      await this.loadWorkspaces();
      await this.loadProjects();
      const stateWorkspaces = StateManager.getState("workspaces");
      if (stateWorkspaces && stateWorkspaces.length > 0 && this.workspaces.length === 0) {
        console.log("[WorkspacePage] Restoring from StateManager:", stateWorkspaces);
        this.workspaces = stateWorkspaces;
      }
    },
    methods: {
      async loadWorkspaces() {
        await WorkspaceManager.getWorkspaces({ search: this.searchQuery });
      },
      handleSearch() {
        this.loadWorkspaces();
      },
      showCreateModal() {
        this.currentWorkspace = null;
        this.formData = {
          name: "",
          root_path: "",
          type: "local",
          encoding: "utf-8",
          excluded_patterns: []
        };
        this.showModal = true;
      },
      handleEdit(workspace) {
        this.currentWorkspace = workspace;
        this.formData = {
          name: workspace.name || "",
          root_path: workspace.root_path || "",
          type: workspace.type || "local",
          encoding: workspace.encoding || "utf-8",
          excluded_patterns: workspace.excluded_patterns || []
        };
        this.showModal = true;
      },
      async handleSave() {
        if (!this.formData.name) {
          alert("\u5DE5\u4F5C\u533A\u540D\u79F0\u4E0D\u80FD\u4E3A\u7A7A");
          return;
        }
        if (this.currentWorkspace) {
          await WorkspaceManager.updateWorkspace(this.currentWorkspace.id, this.formData);
        } else {
          await WorkspaceManager.createWorkspace(this.formData);
        }
        this.closeModal();
      },
      async handleDelete(id) {
        if (confirm("\u786E\u5B9A\u8981\u5220\u9664\u8BE5\u5DE5\u4F5C\u533A\u5417\uFF1F")) {
          await WorkspaceManager.deleteWorkspace(id);
        }
      },
      closeModal() {
        this.showModal = false;
        this.currentWorkspace = null;
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "-";
      }
    }
  };
  window.WorkspacePageComponent = WorkspacePageComponent;

  // js/components/admin/ModelPageComponent.js
  var ModelPageComponent = {
    name: "ModelPageComponent",
    template: `
        <div class="admin-page page-container" id="page-models">
            <div class="admin-header">
                <h2>\u{1F916} \u6A21\u578B\u7BA1\u7406</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + \u65B0\u5EFA\u6A21\u578B
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="\u641C\u7D22\u6A21\u578B..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u6A21\u578B\u540D\u79F0</th>
                                <th>\u6A21\u578B\u7C7B\u578B</th>
                                <th>API\u5730\u5740</th>
                                <th>\u72B6\u6001</th>
                                <th>\u521B\u5EFA\u65F6\u95F4</th>
                                <th>\u64CD\u4F5C</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="model in models" :key="model.id">
                                <td>{{ model.name }}</td>
                                <td>{{ getModelTypeName(model.type) }}</td>
                                <td>{{ model.apiUrl }}</td>
                                <td>
                                    <span class="status-badge" :class="model.status">
                                        {{ model.status === 'active' ? '\u542F\u7528' : '\u505C\u7528' }}
                                    </span>
                                </td>
                                <td>{{ formatDate(model.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(model)">\u7F16\u8F91</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(model.id)">\u5220\u9664</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!models.length" class="empty-table">
                        \u6682\u65E0\u6A21\u578B\u6570\u636E
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '\u7F16\u8F91\u6A21\u578B' : '\u65B0\u5EFA\u6A21\u578B' }}</h3>
                        <button class="modal-close" @click="closeModal">\xD7</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>\u6A21\u578B\u540D\u79F0 *</label>
                            <input type="text" v-model="formData.name" required placeholder="\u8BF7\u8F93\u5165\u6A21\u578B\u540D\u79F0">
                        </div>
                        <div class="form-group">
                            <label>\u6A21\u578B\u7C7B\u578B</label>
                            <select v-model="formData.api_type">
                                <option value="chat">\u5BF9\u8BDD\u6A21\u578B</option>
                                <option value="embedding">\u5D4C\u5165\u6A21\u578B</option>
                                <option value="image">\u56FE\u50CF\u6A21\u578B</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>API\u5730\u5740</label>
                            <input type="text" v-model="formData.api_address" placeholder="https://api.example.com/v1">
                        </div>
                        <div class="form-group">
                            <label>API\u5BC6\u94A5</label>
                            <input type="password" v-model="formData.api_key" placeholder="API\u5BC6\u94A5">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">\u53D6\u6D88</button>
                        <button class="btn btn-primary" @click="handleSave">\u4FDD\u5B58</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        models: [],
        searchQuery: "",
        showModal: false,
        currentModel: null,
        formData: {
          name: "",
          type: "chat",
          apiUrl: "",
          apiKey: "",
          status: "active"
        }
      };
    },
    computed: {
      isEdit() {
        return !!this.currentModel;
      }
    },
    async mounted() {
      console.log("[ModelPage] Mounted, loading models...");
      EventBus.on("model:loaded", ({ models }) => {
        console.log("[ModelPage] Models loaded:", models);
        this.models = models;
      });
      EventBus.on("model:created", ({ model }) => {
        this.models.push(model);
      });
      EventBus.on("model:updated", ({ model }) => {
        const index = this.models.findIndex((m) => m.id === model.id);
        if (index > -1)
          this.models.splice(index, 1, model);
      });
      EventBus.on("model:deleted", ({ id }) => {
        this.models = this.models.filter((m) => m.id !== id);
      });
      await this.loadModels();
      const stateModels = StateManager.getState("models");
      if (stateModels && stateModels.length > 0 && this.models.length === 0) {
        console.log("[ModelPage] Restoring from StateManager:", stateModels);
        this.models = stateModels;
      }
    },
    methods: {
      async loadModels() {
        await ModelManager.getModels({ search: this.searchQuery });
      },
      handleSearch() {
        this.loadModels();
      },
      getModelTypeName(type) {
        const types = {
          chat: "\u5BF9\u8BDD\u6A21\u578B",
          embedding: "\u5D4C\u5165\u6A21\u578B",
          image: "\u56FE\u50CF\u6A21\u578B"
        };
        return types[type] || type;
      },
      showCreateModal() {
        this.currentModel = null;
        this.formData = {
          name: "",
          model_name: "",
          api_type: "chat",
          api_address: "",
          api_key: "",
          parameters: {}
        };
        this.showModal = true;
      },
      handleEdit(model) {
        this.currentModel = model;
        this.formData = {
          name: model.name || "",
          model_name: model.model_name || "",
          api_type: model.api_type || "chat",
          api_address: model.api_address || "",
          api_key: model.api_key || "",
          parameters: model.parameters || {}
        };
        this.showModal = true;
      },
      async handleSave() {
        if (!this.formData.name) {
          alert("\u6A21\u578B\u540D\u79F0\u4E0D\u80FD\u4E3A\u7A7A");
          return;
        }
        if (this.currentModel) {
          await ModelManager.updateModel(this.currentModel.id, this.formData);
        } else {
          await ModelManager.createModel(this.formData);
        }
        this.closeModal();
      },
      async handleDelete(id) {
        if (confirm("\u786E\u5B9A\u8981\u5220\u9664\u8BE5\u6A21\u578B\u5417\uFF1F")) {
          await ModelManager.deleteModel(id);
        }
      },
      closeModal() {
        this.showModal = false;
        this.currentModel = null;
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "-";
      }
    }
  };
  window.ModelPageComponent = ModelPageComponent;

  // js/components/admin/ToolPageComponent.js
  var ToolPageComponent = {
    name: "ToolPageComponent",
    template: `
        <div class="admin-page page-container" id="page-tools">
            <div class="admin-header">
                <h2>\u{1F527} \u5DE5\u5177\u7BA1\u7406</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + \u65B0\u5EFA\u5DE5\u5177
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="\u641C\u7D22\u5DE5\u5177..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u5DE5\u5177\u540D\u79F0</th>
                                <th>\u5DE5\u5177\u7C7B\u578B</th>
                                <th>\u652F\u6301\u64CD\u4F5C\u7CFB\u7EDF</th>
                                <th>\u652F\u6301\u7EC8\u7AEF</th>
                                <th>\u63CF\u8FF0</th>
                                <th>\u72B6\u6001</th>
                                <th>\u521B\u5EFA\u65F6\u95F4</th>
                                <th>\u64CD\u4F5C</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="tool in tools" :key="tool.tool_id || tool.id">
                                <td>{{ tool.tool_name || tool.name || '-' }}</td>
                                <td>{{ getToolTypeName(tool.category || tool.type) || '-' }}</td>
                                <td>{{ getPlatformLabels(tool.supported_os) || '-' }}</td>
                                <td>{{ getTerminalLabels(tool.supported_terminals) || '-' }}</td>
                                <td>{{ tool.description || '-' }}</td>
                                <td>
                                    <span class="status-badge" :class="getToolStatus(tool)">
                                        {{ getToolStatus(tool) === 'active' ? '\u542F\u7528' : '\u505C\u7528' }}
                                    </span>
                                </td>
                                <td>{{ formatDate(tool.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(tool)">\u7F16\u8F91</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(tool.tool_id || tool.id)">\u5220\u9664</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!tools.length" class="empty-table">
                        \u6682\u65E0\u5DE5\u5177\u6570\u636E
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '\u7F16\u8F91\u5DE5\u5177' : '\u65B0\u5EFA\u5DE5\u5177' }}</h3>
                        <button class="modal-close" @click="closeModal">\xD7</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>\u5DE5\u5177\u540D\u79F0 *</label>
                            <input type="text" v-model="formData.name" required placeholder="\u8BF7\u8F93\u5165\u5DE5\u5177\u540D\u79F0">
                        </div>
                        <div class="form-group">
                            <label>\u5DE5\u5177\u7C7B\u578B</label>
                            <select v-model="formData.type">
                                <option value="websearch">\u7F51\u9875\u641C\u7D22</option>
                                <option value="file">\u6587\u4EF6\u64CD\u4F5C</option>
                                <option value="api">API\u8C03\u7528</option>
                                <option value="calculator">\u8BA1\u7B97\u5668</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>\u652F\u6301\u64CD\u4F5C\u7CFB\u7EDF</label>
                            <div class="checkbox-group">
                                <label v-for="os in osOptions" :key="os.value" class="checkbox-label">
                                    <input type="checkbox" :value="os.value" v-model="formData.supported_os">
                                    {{ os.label }}
                                </label>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>\u652F\u6301\u7EC8\u7AEF</label>
                            <div class="checkbox-group">
                                <label v-for="terminal in terminalOptions" :key="terminal.value" class="checkbox-label">
                                    <input type="checkbox" :value="terminal.value" v-model="formData.supported_terminals">
                                    {{ terminal.label }}
                                </label>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>\u63CF\u8FF0</label>
                            <textarea v-model="formData.description" placeholder="\u5DE5\u5177\u63CF\u8FF0"></textarea>
                        </div>
                        <div class="form-group">
                            <label>\u914D\u7F6E\u53C2\u6570\uFF08JSON\uFF09</label>
                            <textarea v-model="formData.config" placeholder='{"key": "value"}'></textarea>
                        </div>
                        <div class="form-group">
                            <label>\u72B6\u6001</label>
                            <select v-model="formData.status">
                                <option value="active">\u542F\u7528</option>
                                <option value="inactive">\u505C\u7528</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">\u53D6\u6D88</button>
                        <button class="btn btn-primary" @click="handleSave">\u4FDD\u5B58</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        tools: [],
        searchQuery: "",
        showModal: false,
        currentTool: null,
        osOptions: [
          { value: "windows", label: "Windows" },
          { value: "linux", label: "Linux" },
          { value: "macos", label: "macOS" }
        ],
        terminalOptions: [
          { value: "powershell", label: "PowerShell" },
          { value: "cmd", label: "CMD" },
          { value: "bash", label: "Bash" },
          { value: "zsh", label: "Zsh" }
        ],
        formData: {
          name: "",
          type: "websearch",
          supported_os: ["windows", "linux", "macos"],
          supported_terminals: ["powershell", "cmd", "bash", "zsh"],
          description: "",
          config: "{}",
          status: "active"
        }
      };
    },
    computed: {
      isEdit() {
        return !!this.currentTool;
      }
    },
    async mounted() {
      console.log("[ToolPage] Mounted, loading tools...");
      EventBus.on("tool:loaded", ({ tools }) => {
        console.log("[ToolPage] Tools loaded:", tools);
        this.tools = tools;
      });
      EventBus.on("tool:created", ({ tool }) => {
        this.tools.push(tool);
      });
      EventBus.on("tool:updated", ({ tool }) => {
        const index = this.tools.findIndex((t) => t.id === tool.id);
        if (index > -1)
          this.tools.splice(index, 1, tool);
      });
      EventBus.on("tool:deleted", ({ id }) => {
        this.tools = this.tools.filter((t) => t.id !== id);
      });
      await this.loadTools();
      const stateTools = StateManager.getState("tools");
      if (stateTools && stateTools.length > 0 && this.tools.length === 0) {
        console.log("[ToolPage] Restoring from StateManager:", stateTools);
        this.tools = stateTools;
      }
    },
    methods: {
      async loadTools() {
        await ToolManager.getTools({ search: this.searchQuery });
      },
      handleSearch() {
        this.loadTools();
      },
      getToolTypeName(type) {
        const types = {
          websearch: "\u7F51\u9875\u641C\u7D22",
          file: "\u6587\u4EF6\u64CD\u4F5C",
          api: "API\u8C03\u7528",
          calculator: "\u8BA1\u7B97\u5668"
        };
        return types[type] || type;
      },
      getPlatformLabels(osArray) {
        if (!osArray || !Array.isArray(osArray) || osArray.length === 0) {
          return "\u5168\u90E8\u5E73\u53F0";
        }
        return osArray.map((os) => {
          const option = this.osOptions.find((o) => o.value === os);
          return option ? option.label : os;
        }).join(", ");
      },
      getTerminalLabels(terminalArray) {
        if (!terminalArray || !Array.isArray(terminalArray) || terminalArray.length === 0) {
          return "\u5168\u90E8\u7EC8\u7AEF";
        }
        return terminalArray.map((terminal) => {
          const option = this.terminalOptions.find((t) => t.value === terminal);
          return option ? option.label : terminal;
        }).join(", ");
      },
      getToolStatus(tool) {
        if (tool.status) {
          return tool.status;
        } else if (tool.is_active !== void 0) {
          return tool.is_active ? "active" : "inactive";
        }
        return "inactive";
      },
      showCreateModal() {
        this.currentTool = null;
        this.formData = {
          name: "",
          type: "websearch",
          supported_os: ["windows", "linux", "macos"],
          supported_terminals: ["powershell", "cmd", "bash", "zsh"],
          description: "",
          config: "{}",
          status: "active"
        };
        this.showModal = true;
      },
      handleEdit(tool) {
        this.currentTool = tool;
        this.formData = {
          ...tool,
          name: tool.tool_name || tool.name || "",
          type: tool.category || tool.type || "websearch",
          supported_os: tool.supported_os || ["windows", "linux", "macos"],
          supported_terminals: tool.supported_terminals || ["powershell", "cmd", "bash", "zsh"],
          status: this.getToolStatus(tool)
        };
        this.showModal = true;
      },
      async handleSave() {
        if (!this.formData.name) {
          alert("\u5DE5\u5177\u540D\u79F0\u4E0D\u80FD\u4E3A\u7A7A");
          return;
        }
        if (this.currentTool) {
          await ToolManager.updateTool(this.currentTool.id, this.formData);
        } else {
          await ToolManager.createTool(this.formData);
        }
        this.closeModal();
      },
      async handleDelete(id) {
        if (confirm("\u786E\u5B9A\u8981\u5220\u9664\u8BE5\u5DE5\u5177\u5417\uFF1F")) {
          await ToolManager.deleteTool(id);
        }
      },
      closeModal() {
        this.showModal = false;
        this.currentTool = null;
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "-";
      }
    }
  };
  window.ToolPageComponent = ToolPageComponent;

  // js/components/admin/StoragePageComponent.js
  var StoragePageComponent = {
    name: "StoragePageComponent",
    template: `
        <div class="admin-page page-container" id="page-storage">
            <div class="admin-header">
                <h2>\u{1F4BE} \u5B58\u50A8\u914D\u7F6E</h2>
            </div>
            
            <!-- \u6807\u7B7E\u9875\u5207\u6362 -->
            <div class="tabs">
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'entity' }"
                    @click="switchTab('entity')">
                    \u{1F4E6} \u5B9E\u4F53\u5B58\u50A8\u914D\u7F6E
                </button>
                <button 
                    class="tab-btn" 
                    :class="{ active: activeTab === 'event' }"
                    @click="switchTab('event')">
                    \u26A1 \u4E8B\u4EF6\u5B58\u50A8\u914D\u7F6E
                </button>
            </div>
            
            <!-- \u5B9E\u4F53\u5B58\u50A8\u914D\u7F6E -->
            <div v-if="activeTab === 'entity'" class="tab-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="\u641C\u7D22\u5B58\u50A8\u914D\u7F6E..."
                        @input="handleEntitySearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u5B9E\u4F53\u7C7B\u578B</th>
                                <th>\u63CF\u8FF0</th>
                                <th>\u6301\u4E45\u5316</th>
                                <th>\u66F4\u65B0\u65F6\u95F4</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="storage in filteredEntityStorages" :key="storage.entity_type">
                                <td><code>{{ storage.entity_type }}</code></td>
                                <td>{{ storage.description }}</td>
                                <td>
                                    <label class="switch">
                                        <input 
                                            type="checkbox" 
                                            :checked="storage.persist"
                                            @change="toggleEntityPersist(storage)">
                                        <span class="slider"></span>
                                    </label>
                                    <span class="switch-label">{{ storage.persist ? '\u662F' : '\u5426' }}</span>
                                </td>
                                <td>{{ formatDate(storage.updated_at) }}</td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!filteredEntityStorages.length" class="empty-table">
                        \u6682\u65E0\u5B9E\u4F53\u5B58\u50A8\u914D\u7F6E\u6570\u636E
                    </div>
                </div>
                <div class="batch-actions" v-if="pendingEntityChanges.length">
                    <span>\u5F85\u4FDD\u5B58\u7684\u66F4\u6539: {{ pendingEntityChanges.length }} \u9879</span>
                    <button class="btn btn-primary" @click="saveEntityChanges">\u4FDD\u5B58\u66F4\u6539</button>
                    <button class="btn btn-secondary" @click="discardEntityChanges">\u653E\u5F03</button>
                </div>
            </div>
            
            <!-- \u4E8B\u4EF6\u5B58\u50A8\u914D\u7F6E -->
            <div v-if="activeTab === 'event'" class="tab-content">
                <div class="event-filter-bar">
                    <div class="filter-group">
                        <label>\u4E8B\u4EF6\u7C7B\u578B\u7B5B\u9009:</label>
                        <select v-model="eventTypeFilter" @change="filterEvents">
                            <option value="">\u5168\u90E8</option>
                            <option value="project">\u9879\u76EE\u4E8B\u4EF6</option>
                            <option value="session">\u4F1A\u8BDD\u4E8B\u4EF6</option>
                            <option value="dialog">\u5BF9\u8BDD\u4E8B\u4EF6</option>
                            <option value="message">\u6D88\u606F\u4E8B\u4EF6</option>
                            <option value="llm">LLM\u4E8B\u4EF6</option>
                            <option value="tool">\u5DE5\u5177\u4E8B\u4EF6</option>
                            <option value="task">\u4EFB\u52A1\u4E8B\u4EF6</option>
                            <option value="round">\u8F6E\u6B21\u4E8B\u4EF6</option>
                            <option value="client">\u5BA2\u6237\u7AEF\u4E8B\u4EF6</option>
                            <option value="system">\u7CFB\u7EDF\u4E8B\u4EF6</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>
                            <input type="checkbox" v-model="showOnlyDisabled" @change="filterEvents">
                            \u4EC5\u663E\u793A\u505C\u7528\u9879
                        </label>
                    </div>
                    <div class="filter-actions">
                        <button class="btn btn-secondary" @click="resetEventStorage">\u91CD\u7F6E\u4E3A\u9ED8\u8BA4</button>
                        <button class="btn btn-primary" @click="toggleAllEvents">
                            {{ allEventsEnabled ? '\u7981\u7528\u5168\u90E8' : '\u542F\u7528\u5168\u90E8' }}
                        </button>
                    </div>
                </div>
                
                <div class="data-table event-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u4E8B\u4EF6\u7C7B\u578B</th>
                                <th>\u63CF\u8FF0</th>
                                <th>\u5B58\u50A8</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="(events, category) in groupedEvents" :key="category">
                                <tr class="category-header">
                                    <td colspan="3">
                                        <strong>{{ getCategoryName(category) }}</strong>
                                        <span class="category-count">
                                            ({{ events.filter(e => e.persist).length }}/{{ events.length }})
                                        </span>
                                    </td>
                                </tr>
                                <tr v-for="event in events" :key="event.event_type" :class="{ 'disabled-row': !event.persist }">
                                    <td><code>{{ event.event_type }}</code></td>
                                    <td>{{ event.description }}</td>
                                    <td>
                                        <label class="switch">
                                            <input 
                                                type="checkbox" 
                                                :checked="event.persist"
                                                @change="toggleEventPersist(event)">
                                            <span class="slider"></span>
                                        </label>
                                        <span class="switch-label">{{ event.persist ? '\u662F' : '\u5426' }}</span>
                                    </td>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                    <div v-if="!Object.keys(groupedEvents).length" class="empty-table">
                        \u6682\u65E0\u4E8B\u4EF6\u5B58\u50A8\u914D\u7F6E\u6570\u636E
                    </div>
                </div>
                
                <div class="batch-actions" v-if="pendingEventChanges.length">
                    <span>\u5F85\u4FDD\u5B58\u7684\u66F4\u6539: {{ pendingEventChanges.length }} \u9879</span>
                    <button class="btn btn-primary" @click="saveEventChanges">\u4FDD\u5B58\u66F4\u6539</button>
                    <button class="btn btn-secondary" @click="discardEventChanges">\u653E\u5F03</button>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        activeTab: "event",
        searchQuery: "",
        entityStorages: [],
        eventStorages: [],
        pendingEntityChanges: [],
        pendingEventChanges: [],
        eventTypeFilter: "",
        showOnlyDisabled: false
      };
    },
    computed: {
      filteredEntityStorages() {
        if (!this.searchQuery)
          return this.entityStorages;
        const query = this.searchQuery.toLowerCase();
        return this.entityStorages.filter(
          (s) => s.entity_type.toLowerCase().includes(query) || s.description && s.description.toLowerCase().includes(query)
        );
      },
      filteredEvents() {
        let events = this.eventStorages;
        if (this.eventTypeFilter) {
          events = events.filter((e) => e.event_type.startsWith(this.eventTypeFilter));
        }
        if (this.showOnlyDisabled) {
          events = events.filter((e) => !e.persist);
        }
        return events;
      },
      groupedEvents() {
        const groups = {};
        for (const event of this.filteredEvents) {
          const parts = event.event_type.split(".");
          const category = parts[0];
          if (!groups[category]) {
            groups[category] = [];
          }
          groups[category].push(event);
        }
        return groups;
      },
      allEventsEnabled() {
        return this.eventStorages.length > 0 && this.eventStorages.every((e) => e.persist);
      }
    },
    async mounted() {
      console.log("[StoragePage] Mounted");
      EventBus.on("storage:loaded", ({ storages }) => {
        console.log("[StoragePage] Entity storages loaded:", storages);
        this.entityStorages = storages;
      });
      EventBus.on("storage:error", ({ error }) => {
        console.error("[StoragePage] Storage error:", error);
      });
      EventBus.on("eventStorage:loaded", ({ eventStorages }) => {
        console.log("[StoragePage] Event storages loaded:", eventStorages);
        this.eventStorages = eventStorages;
      });
      EventBus.on("eventStorage:updated", () => {
        this.loadEventStorages();
      });
      EventBus.on("eventStorage:batch_updated", () => {
        this.loadEventStorages();
        this.pendingEventChanges = [];
      });
      EventBus.on("eventStorage:reset", () => {
        this.loadEventStorages();
        this.pendingEventChanges = [];
      });
      EventBus.on("eventStorage:error", ({ error }) => {
        console.error("[StoragePage] Event storage error:", error);
      });
      this.loadEntityStorages();
      this.loadEventStorages();
    },
    methods: {
      switchTab(tab) {
        this.activeTab = tab;
      },
      // 实体存储配置方法
      async loadEntityStorages() {
        await StorageManager.getStorages();
      },
      handleEntitySearch() {
      },
      toggleEntityPersist(storage) {
        const newValue = !storage.persist;
        storage.persist = newValue;
        const existingIndex = this.pendingEntityChanges.findIndex(
          (c) => c.entity_type === storage.entity_type
        );
        if (existingIndex >= 0) {
          this.pendingEntityChanges.splice(existingIndex, 1);
        }
        this.pendingEntityChanges.push({
          entity_type: storage.entity_type,
          persist: newValue
        });
      },
      async saveEntityChanges() {
        try {
          await StorageManager.batchUpdateStorage(this.pendingEntityChanges);
          this.pendingEntityChanges = [];
          await this.loadEntityStorages();
        } catch (error) {
          console.error("\u4FDD\u5B58\u5931\u8D25:", error);
        }
      },
      discardEntityChanges() {
        this.pendingEntityChanges = [];
        this.loadEntityStorages();
      },
      // 事件存储配置方法
      async loadEventStorages() {
        await StorageManager.getEventStorages();
      },
      filterEvents() {
      },
      toggleEventPersist(event) {
        const newValue = !event.persist;
        event.persist = newValue;
        const existingIndex = this.pendingEventChanges.findIndex(
          (c) => c.event_type === event.event_type
        );
        if (existingIndex >= 0) {
          this.pendingEventChanges.splice(existingIndex, 1);
        }
        this.pendingEventChanges.push({
          event_type: event.event_type,
          persist: newValue
        });
      },
      async saveEventChanges() {
        try {
          await StorageManager.batchUpdateEventStorage(this.pendingEventChanges);
          this.pendingEventChanges = [];
          await this.loadEventStorages();
        } catch (error) {
          console.error("\u4FDD\u5B58\u5931\u8D25:", error);
        }
      },
      discardEventChanges() {
        this.pendingEventChanges = [];
        this.loadEventStorages();
      },
      async resetEventStorage() {
        if (confirm("\u786E\u5B9A\u8981\u91CD\u7F6E\u6240\u6709\u4E8B\u4EF6\u5B58\u50A8\u914D\u7F6E\u4E3A\u9ED8\u8BA4\u503C\u5417\uFF1F")) {
          await StorageManager.resetEventStorage();
        }
      },
      toggleAllEvents() {
        const newValue = !this.allEventsEnabled;
        for (const event of this.eventStorages) {
          if (event.persist !== newValue) {
            event.persist = newValue;
            const existingIndex = this.pendingEventChanges.findIndex(
              (c) => c.event_type === event.event_type
            );
            if (existingIndex >= 0) {
              this.pendingEventChanges.splice(existingIndex, 1);
            }
            this.pendingEventChanges.push({
              event_type: event.event_type,
              persist: newValue
            });
          }
        }
      },
      getCategoryName(category) {
        const names = {
          "project": "\u9879\u76EE\u4E8B\u4EF6",
          "session": "\u4F1A\u8BDD\u4E8B\u4EF6",
          "dialog": "\u5BF9\u8BDD\u4E8B\u4EF6",
          "message": "\u6D88\u606F\u4E8B\u4EF6",
          "llm": "LLM\u4E8B\u4EF6",
          "tool": "\u5DE5\u5177\u4E8B\u4EF6",
          "task": "\u4EFB\u52A1\u4E8B\u4EF6",
          "task_group": "\u4EFB\u52A1\u7EC4\u4E8B\u4EF6",
          "round": "\u8F6E\u6B21\u4E8B\u4EF6",
          "client": "\u5BA2\u6237\u7AEF\u4E8B\u4EF6",
          "system": "\u7CFB\u7EDF\u4E8B\u4EF6",
          "history": "\u5386\u53F2\u56DE\u653E\u4E8B\u4EF6"
        };
        return names[category] || category;
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "-";
      }
    }
  };
  window.StoragePageComponent = StoragePageComponent;

  // js/components/admin/PromptPageComponent.js
  var PromptPageComponent = {
    name: "PromptPageComponent",
    template: `
        <div class="admin-page page-container" id="page-prompts">
            <div class="admin-header">
                <h2>\u{1F4DD} \u63D0\u793A\u8BCD\u7BA1\u7406</h2>
                <div class="admin-actions">
                    <button class="btn btn-primary" @click="showCreateModal">
                        + \u65B0\u5EFA\u63D0\u793A\u8BCD
                    </button>
                </div>
            </div>
            <div class="admin-content">
                <div class="search-box">
                    <input
                        type="text"
                        v-model="searchQuery"
                        placeholder="\u641C\u7D22\u63D0\u793A\u8BCD..."
                        @input="handleSearch">
                </div>
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                <th>\u63D0\u793A\u8BCD\u540D\u79F0</th>
                                <th>\u5206\u7C7B</th>
                                <th>\u53D8\u91CF</th>
                                <th>\u72B6\u6001</th>
                                <th>\u521B\u5EFA\u65F6\u95F4</th>
                                <th>\u64CD\u4F5C</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr v-for="prompt in prompts" :key="prompt.prompt_id">
                                <td>{{ prompt.name }}</td>
                                <td>{{ getCategoryLabel(prompt.category) }}</td>
                                <td>{{ prompt.variables?.join(', ') || '-' }}</td>
                                <td>
                                    <span class="status-badge" :class="prompt.is_active ? 'active' : 'disabled'">
                                        {{ prompt.is_active ? '\u542F\u7528' : '\u505C\u7528' }}
                                    </span>
                                </td>
                                <td>{{ formatDate(prompt.created_at) }}</td>
                                <td>
                                    <button class="btn btn-sm" @click="handleEdit(prompt)">\u7F16\u8F91</button>
                                    <button class="btn btn-sm btn-danger" @click="handleDelete(prompt.prompt_id)">\u5220\u9664</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    <div v-if="!prompts.length" class="empty-table">
                        \u6682\u65E0\u63D0\u793A\u8BCD\u6570\u636E
                    </div>
                </div>
            </div>
            <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
                <div class="modal">
                    <div class="modal-header">
                        <h3>{{ isEdit ? '\u7F16\u8F91\u63D0\u793A\u8BCD' : '\u65B0\u5EFA\u63D0\u793A\u8BCD' }}</h3>
                        <button class="modal-close" @click="closeModal">\xD7</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label>\u63D0\u793A\u8BCD\u540D\u79F0 *</label>
                            <input type="text" v-model="formData.name" required placeholder="\u8BF7\u8F93\u5165\u63D0\u793A\u8BCD\u540D\u79F0">
                        </div>
                        <div class="form-group">
                            <label>\u5206\u7C7B *</label>
                            <select v-model="formData.category" required>
                                <option value="" disabled>\u8BF7\u9009\u62E9\u5206\u7C7B</option>
                                <option value="system_prompt">system_prompt (\u7CFB\u7EDF\u63D0\u793A\u8BCD)</option>
                                <option value="user_prompt">user_prompt (\u7528\u6237\u63D0\u793A\u8BCD)</option>
                                <option value="assistant_prompt">assistant_prompt (\u52A9\u624B\u63D0\u793A\u8BCD)</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>\u63D0\u793A\u8BCD\u5185\u5BB9 *</label>
                            <textarea v-model="formData.content" required rows="8" placeholder="\u63D0\u793A\u8BCD\u5185\u5BB9\uFF0C\u652F\u6301 {{variable}} \u683C\u5F0F\u7684\u53D8\u91CF"></textarea>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" v-model="formData.is_active">
                                \u542F\u7528\u72B6\u6001
                            </label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" @click="closeModal">\u53D6\u6D88</button>
                        <button class="btn btn-primary" @click="handleSave">\u4FDD\u5B58</button>
                    </div>
                </div>
            </div>
        </div>
    `,
    data() {
      return {
        prompts: [],
        searchQuery: "",
        showModal: false,
        currentPrompt: null,
        formData: {
          name: "",
          category: "",
          content: "",
          is_active: true
        },
        categories: [
          { value: "system_prompt", label: "system_prompt (\u7CFB\u7EDF\u63D0\u793A\u8BCD)" },
          { value: "user_prompt", label: "user_prompt (\u7528\u6237\u63D0\u793A\u8BCD)" },
          { value: "assistant_prompt", label: "assistant_prompt (\u52A9\u624B\u63D0\u793A\u8BCD)" }
        ]
      };
    },
    computed: {
      isEdit() {
        return !!this.currentPrompt;
      }
    },
    async mounted() {
      console.log("[PromptPage] Mounted, loading prompts...");
      EventBus.on("prompt:loaded", ({ prompts }) => {
        console.log("[PromptPage] Prompts loaded:", prompts);
        this.prompts = prompts;
      });
      EventBus.on("prompt:created", ({ prompt }) => {
        this.prompts.push(prompt);
      });
      EventBus.on("prompt:updated", ({ prompt }) => {
        const index = this.prompts.findIndex((p) => p.prompt_id === prompt.prompt_id);
        if (index > -1)
          this.prompts.splice(index, 1, prompt);
      });
      EventBus.on("prompt:deleted", ({ prompt_id }) => {
        this.prompts = this.prompts.filter((p) => p.prompt_id !== prompt_id);
      });
      await this.loadPrompts();
      const statePrompts = StateManager.getState("prompts");
      if (statePrompts && statePrompts.length > 0 && this.prompts.length === 0) {
        console.log("[PromptPage] Restoring from StateManager:", statePrompts);
        this.prompts = statePrompts;
      }
    },
    methods: {
      getCategoryLabel(category) {
        const cat = this.categories.find((c) => c.value === category);
        return cat ? cat.label : category || "-";
      },
      async loadPrompts() {
        await PromptManager.getPrompts({ search: this.searchQuery });
      },
      handleSearch() {
        this.loadPrompts();
      },
      showCreateModal() {
        this.currentPrompt = null;
        this.formData = {
          name: "",
          category: "",
          content: "",
          is_active: true
        };
        this.showModal = true;
      },
      handleEdit(prompt) {
        this.currentPrompt = prompt;
        this.formData = {
          name: prompt.name || "",
          category: prompt.category || "",
          content: prompt.content || "",
          is_active: prompt.is_active || true
        };
        this.showModal = true;
      },
      async handleSave() {
        if (!this.formData.name) {
          alert("\u63D0\u793A\u8BCD\u540D\u79F0\u4E0D\u80FD\u4E3A\u7A7A");
          return;
        }
        if (!this.formData.category) {
          alert("\u8BF7\u9009\u62E9\u63D0\u793A\u8BCD\u5206\u7C7B");
          return;
        }
        if (!this.formData.content) {
          alert("\u63D0\u793A\u8BCD\u5185\u5BB9\u4E0D\u80FD\u4E3A\u7A7A");
          return;
        }
        if (this.currentPrompt) {
          await PromptManager.updatePrompt(this.currentPrompt.prompt_id, this.formData);
        } else {
          await PromptManager.createPrompt(this.formData);
        }
        this.closeModal();
      },
      async handleDelete(prompt_id) {
        if (confirm("\u786E\u5B9A\u8981\u5220\u9664\u8BE5\u63D0\u793A\u8BCD\u5417\uFF1F")) {
          await PromptManager.deletePrompt(prompt_id);
        }
      },
      closeModal() {
        this.showModal = false;
        this.currentPrompt = null;
      },
      formatDate(dateStr) {
        return dateStr ? new Date(dateStr).toLocaleDateString() : "-";
      }
    }
  };
  window.PromptPageComponent = PromptPageComponent;

  // main.js
  var components = {
    // Nav
    NavBarComponent: window.NavBarComponent,
    NavMenuComponent: window.NavMenuComponent,
    ThemeToggle: window.ThemeToggle,
    ConnectionBadge: window.ConnectionBadge,
    ReplayToggle: window.ReplayToggle,
    // Chat
    ChatPageComponent: window.ChatPageComponent,
    ChatSidebarComponent: window.ChatSidebarComponent,
    ChatInputComponent: window.ChatInputComponent,
    UserMessageComponent: window.UserMessageComponent,
    AssistantMessageComponent: window.AssistantMessageComponent,
    ThinkBlockComponent: window.ThinkBlockComponent,
    TextBlockComponent: window.TextBlockComponent,
    ToolCardComponent: window.ToolCardComponent,
    // Workspace
    FileTreeComponent: window.FileTreeComponent,
    // Admin
    ProjectPageComponent: window.ProjectPageComponent,
    WorkspacePageComponent: window.WorkspacePageComponent,
    ModelPageComponent: window.ModelPageComponent,
    ToolPageComponent: window.ToolPageComponent,
    StoragePageComponent: window.StoragePageComponent,
    PromptPageComponent: window.PromptPageComponent
  };
  function initServices() {
    console.log("[App] Initializing services...");
    window.ChatManager.init();
    window.ComponentSubscriptions.init();
    console.log("[App] Services initialized");
  }
  async function initApp() {
    console.log("[App] Initializing...");
    console.log("[App] Components to register:", Object.keys(components));
    Object.entries(components).forEach(([name, component]) => {
      if (component && component.name) {
        Vue.component(component.name, component);
        console.log(`[App] Registered: ${component.name}`);
      } else {
        console.warn(`[App] Component ${name} is invalid!`);
      }
    });
    initServices();
    new Vue({
      el: "#app",
      components,
      data() {
        return {
          currentPage: window.StateManager.getState("currentPage") || "chat"
        };
      },
      template: `
            <div id="app">
                <nav-bar-component></nav-bar-component>
                <div class="page-content">
                    <chat-page-component v-if="currentPage === 'chat'"></chat-page-component>
                    <project-page-component v-if="currentPage === 'projects'"></project-page-component>
                    <workspace-page-component v-if="currentPage === 'workspaces'"></workspace-page-component>
                    <model-page-component v-if="currentPage === 'models'"></model-page-component>
                    <tool-page-component v-if="currentPage === 'tools'"></tool-page-component>
                    <prompt-page-component v-if="currentPage === 'prompts'"></prompt-page-component>
                    <storage-page-component v-if="currentPage === 'storage'"></storage-page-component>
                </div>
            </div>
        `,
      mounted() {
        console.log("[App] Mounted");
        console.log("[App] Initial currentPage:", this.currentPage);
        console.log("[App] StateManager currentPage:", window.StateManager.getState("currentPage"));
        console.log("[App] Vue version:", Vue.version);
        window.PageRouter.init();
        window.EventBus.on("page:change", ({ page }) => {
          console.log("[App] Page changed to:", page);
          this.currentPage = page;
        });
        this.connectWebSocket();
      },
      methods: {
        async connectWebSocket() {
          try {
            await window.WSClient.connect();
            console.log("[App] WebSocket connected");
            if (!window.ChatManager.initialized) {
              window.ChatManager.init();
            }
          } catch (e) {
            console.warn("[App] WebSocket connection failed:", e.message);
          }
        }
      }
    });
  }
  document.addEventListener("DOMContentLoaded", initApp);
})();
//# sourceMappingURL=bundle.js.map
