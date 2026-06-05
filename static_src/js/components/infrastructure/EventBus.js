/**
 * EventBus - 事件总线
 * 组件间通信的中心调度器
 * 支持带参数条件的订阅和自动取消订阅
 * 提供详细的消息追踪和日志打印
 */
export const EventBus = {
    listeners: new Map(),
    conditionalListeners: new Map(),
    
    // 事件缓存 - 用于处理时序问题：事件可能在订阅者订阅之前到达
    _eventCache: new Map(),
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
    _subscribers: new Map(),

    // 已配置为抛弃的事件列表（这些事件不需要处理）
    droppedMessages: [
        'round.created', 'event.round.created',
        'round.started',
        'round.completed', 'event.round.completed',
        'project:loaded',
        'project:loading',
        'ws:connected',
        'llm.request_prepared',
        'llm.response_received',
        'component:user-message-created',
        'component:assistant-message-created',
        'component:response-block-created',
        'session:loading',
        'event.session.created'
    ],

    // 规定要订阅的事件列表（订阅关系表中定义的事件）
    subscribedEvents: [
        'event.session.created',
        'event.client.message_received',
        'event.dialog.created',
        'event.llm.request_sent',
        'event.llm.call_thinking_completed',
        'event.llm.call_reasoning_completed',
        'event.llm.call_text_completed',
        'event.tool.call_started',
        'event.llm.call_text_streaming',
        'event.llm.call_thinking_streaming',
        'event.llm.call_reasoning_streaming',
        'event.tool.execution_output',
        'event.llm.call_text_completed_end',
        'event.llm.call_thinking_completed_end',
        'event.llm.call_reasoning_completed_end',
        'event.llm.call_completed_end',
        'event.tool.execution_output_end',
        'event.tool.call_completed_end'
    ],

    // 发布事件
    emit(eventType, payload) {
        this._stats.emitted++;
        const startTime = Date.now();
        const action = payload?.action || payload?.type || '';
        
        const normalCount = this.listeners.has(eventType) ? this.listeners.get(eventType).length : 0;
        const conditionalCount = this.conditionalListeners.has(eventType) ? this.conditionalListeners.get(eventType).length : 0;
        
        console.log(`%c[EventBus] 📤 发布事件: ${eventType} action=${action}`, 'color: #2196F3; font-weight: bold');
        console.log(`%c[EventBus]   ├── 普通订阅者数: ${normalCount}`, 'color: #2196F3');
        console.log(`%c[EventBus]   └── 条件订阅者数: ${conditionalCount}`, 'color: #2196F3');

        let totalConsumed = 0;
        let consumers = [];

        // 处理普通监听器
        if (this.listeners.has(eventType)) {
            const handlers = this.listeners.get(eventType);
            handlers.forEach((handler, index) => {
                const subscriberInfo = this._getSubscriberInfo(eventType, index, 'normal');
                const subscriberName = subscriberInfo.name;
                try {
                    // 只打印非匿名订阅者的日志
                    if (subscriberName !== '匿名订阅者') {
                        console.log(`%c[EventBus]   └── 🔄 消费中: ${subscriberName} action=${action}`, 'color: #4CAF50');
                    }
                    handler(payload);
                    totalConsumed++;
                    consumers.push(subscriberName || '匿名订阅者');
                    // 只打印非匿名订阅者的日志
                    if (subscriberName !== '匿名订阅者') {
                        console.log(`%c[EventBus]   └── ✅ 已消费: ${subscriberName} action=${action}`, 'color: #4CAF50');
                    }
                } catch (e) {
                    console.error(`%c[EventBus]   └── ❌ 消费失败: ${subscriberName || '匿名订阅者'} action=${action}`, 'color: #F44336', e);
                }
            });
        }

        // 处理带条件的监听器
        if (this.conditionalListeners.has(eventType)) {
            this.conditionalListeners.get(eventType).forEach((listener, index) => {
                const subscriberInfo = this._getSubscriberInfo(eventType, index, 'conditional');
                const subscriberName = subscriberInfo.name;
                try {
                    if (listener.condition(payload)) {
                        // 只打印非匿名订阅者的日志
                        if (subscriberName !== '匿名订阅者') {
                            console.log(`%c[EventBus]   └── 🔄 条件消费中: ${subscriberName} action=${action}`, 'color: #FF9800');
                        }
                        listener.handler(payload);
                        totalConsumed++;
                        consumers.push(subscriberName || '匿名订阅者');
                        // 只打印非匿名订阅者的日志
                        if (subscriberName !== '匿名订阅者') {
                            console.log(`%c[EventBus]   └── ✅ 条件匹配并消费: ${subscriberName} action=${action}`, 'color: #FF9800');
                        }
                    } else {
                        // 只打印非匿名订阅者的日志
                        if (subscriberName !== '匿名订阅者') {
                            console.log(`%c[EventBus]   └── ⏭️ 条件不匹配跳过: ${subscriberName} action=${action}`, 'color: #9E9E9E');
                        }
                    }
                } catch (e) {
                    console.error(`%c[EventBus]   └── ❌ 条件消费失败: ${subscriberName || '匿名订阅者'} action=${action}`, 'color: #F44336', e);
                }
            });
        }

        // 记录消费统计
        this._stats.consumed += totalConsumed;

        // 如果没有任何订阅者消费，尝试缓存事件
        if (totalConsumed === 0) {
            // 只有订阅关系表中的事件才缓存
            if (this.subscribedEvents.includes(eventType)) {
                this._cacheEvent(eventType, payload);
                console.log(`%c[EventBus] 📦 事件 ${eventType} action=${action} 暂存到缓存`, 'color: #FF9800');
            } else {
                this._stats.dropped++;
                if (this.droppedMessages.includes(eventType)) {
                    console.log(`[EventBus] 事件 ${eventType} action=${action} 无人订阅，已抛弃`);
                } else {
                    console.warn(`%c[EventBus] ⚠️ 事件 ${eventType} action=${action} 无人订阅，已抛弃（可能需要添加到订阅关系表）`, 'color: #FFC107; font-weight: bold');
                }
            }
        } else {
            // 过滤匿名订阅者，只显示有名称的订阅者
            const namedConsumers = consumers.filter(c => c !== '匿名订阅者');
            // 只有当有非匿名订阅者时才打印汇总日志
            if (namedConsumers.length > 0) {
                console.log(`%c[EventBus] ✅ 事件 ${eventType} action=${action} 已被 ${namedConsumers.join(', ')} 消费 (耗时: ${Date.now() - startTime}ms)`, 'color: #4CAF50');
            }
        }
    },

    // 订阅事件
    on(eventType, handler, subscriberName = '匿名订阅者') {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, []);
        }
        this.listeners.get(eventType).push(handler);
        
        // 记录订阅者信息
        if (!this._subscribers.has(eventType)) {
            this._subscribers.set(eventType, []);
        }
        this._subscribers.get(eventType).push({
            type: 'normal',
            name: subscriberName,
            handler: handler
        });
        
        console.log(`%c[EventBus] 📥 订阅事件: ${eventType} (订阅者: ${subscriberName}, 当前订阅者数: ${this.listeners.get(eventType).length})`, 'color: #9C27B0');
    
    // 检查并处理缓存的事件
    this._processCachedEvents(eventType, (payload) => handler(payload));
    },

    // 带条件的订阅
    onConditional(eventType, condition, handler, subscriberName = '匿名订阅者') {
        if (!this.conditionalListeners.has(eventType)) {
            this.conditionalListeners.set(eventType, []);
        }
        const listener = {
            condition,
            handler,
            id: Date.now() + Math.random(),
            subscriberName: subscriberName
        };
        this.conditionalListeners.get(eventType).push(listener);
        
        // 记录订阅者信息
        if (!this._subscribers.has(eventType)) {
            this._subscribers.set(eventType, []);
        }
        this._subscribers.get(eventType).push({
            type: 'conditional',
            name: subscriberName,
            handler: handler,
            id: listener.id
        });
        
        console.log(`%c[EventBus] 📥 条件订阅事件: ${eventType} (订阅者: ${subscriberName}, 当前订阅者数: ${this.conditionalListeners.get(eventType).length})`, 'color: #FF9800');
    
    // 检查并处理缓存的事件
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
            const filtered = subscribers.filter(s => s.type === type);
            if (filtered[index]) {
                return filtered[index];
            }
        }
        return { name: `匿名${type === 'conditional' ? '条件' : ''}订阅者_${index}` };
    },

    // 取消订阅
    off(eventType, handler) {
        if (this.listeners.has(eventType)) {
            const handlers = this.listeners.get(eventType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
                
                // 同时从订阅者信息中移除
                if (this._subscribers.has(eventType)) {
                    const subscribers = this._subscribers.get(eventType);
                    const subIndex = subscribers.findIndex(s => s.handler === handler);
                    if (subIndex > -1) {
                        console.log(`%c[EventBus] 🚫 取消订阅: ${eventType} (订阅者: ${subscribers[subIndex].name})`, 'color: #F44336');
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
            const filtered = listeners.filter(listener => {
                if (typeof handlerOrId === 'function') {
                    if (listener.handler === handlerOrId) {
                        console.log(`%c[EventBus] 🚫 取消条件订阅: ${eventType} (订阅者: ${listener.subscriberName})`, 'color: #F44336');
                    }
                    return listener.handler !== handlerOrId;
                } else {
                    if (listener.id === handlerOrId) {
                        console.log(`%c[EventBus] 🚫 取消条件订阅: ${eventType} (订阅者: ${listener.subscriberName})`, 'color: #F44336');
                    }
                    return listener.id !== handlerOrId;
                }
            });
            this.conditionalListeners.set(eventType, filtered);
        }
    },

    // 一次性订阅
    once(eventType, handler, subscriberName = '匿名订阅者') {
        const wrappedHandler = (payload) => {
            handler(payload);
            this.off(eventType, wrappedHandler);
        };
        this.on(eventType, wrappedHandler, subscriberName);
    },

    // 一次性带条件订阅（处理完后自动取消订阅）
    onceConditional(eventType, condition, handler, subscriberName = '匿名订阅者') {
        const listener = {
            condition,
            handler,
            id: Date.now() + Math.random(),
            subscriberName: subscriberName
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
        
        // 记录订阅者信息
        if (!this._subscribers.has(eventType)) {
            this._subscribers.set(eventType, []);
        }
        this._subscribers.get(eventType).push({
            type: 'conditional_once',
            name: subscriberName,
            handler: wrappedHandler,
            id: listener.id
        });
        
        if (this.subscribedEvents.includes(eventType)) {
            console.log(`%c[EventBus] 📥 一次性条件订阅: ${eventType} (订阅者: ${subscriberName})`, 'color: #9C27B0');
        } else {
            console.log(`[EventBus] 📥 一次性条件订阅: ${eventType} (订阅者: ${subscriberName}) [非订阅关系表定义]`);
        }
        
        return listener.id;
    },

    // 记录组件创建
    trackComponentCreation(parentName, childName, details = {}) {
        this._stats.componentCreations++;
        console.log(`%c[EventBus] 👶 组件创建: ${parentName} → ${childName}`, 'color: #00BCD4; font-weight: bold', details);
    },

    // 记录组件更新
    trackComponentUpdate(componentName, updateType, details = {}) {
        this._stats.componentUpdates++;
        console.log(`%c[EventBus] 🔄 组件更新: ${componentName} (${updateType})`, 'color: #8BC34A', details);
    },

    // 记录异常抛弃（设计应该被消费但没有被消费）
    trackUnexpectedDrop(eventType, expectedConsumers, payload) {
        console.error(`%c[EventBus] ❌ 异常抛弃: ${eventType}`, 'color: #F44336; font-weight: bold');
        console.error(`   期望消费者: ${expectedConsumers.join(', ')}`);
        console.error(`   实际消费者: 无`);
        console.error(`   消息内容:`, payload);
    },

    // 获取统计信息
    getStats() {
        return { ...this._stats };
    },

    // 打印统计摘要
    printStats() {
        console.log(`%c[EventBus] 📊 消息统计摘要`, 'color: #333; font-weight: bold; font-size: 14px');
        console.log(`   发布事件: ${this._stats.emitted}`);
        console.log(`   消费事件: ${this._stats.consumed}`);
        console.log(`   抛弃事件: ${this._stats.dropped}`);
        console.log(`   创建组件: ${this._stats.componentCreations}`);
        console.log(`   更新组件: ${this._stats.componentUpdates}`);
    },

    // 缓存事件（用于处理时序问题）
    _cacheEvent(eventType, payload) {
        if (!this._eventCache.has(eventType)) {
            this._eventCache.set(eventType, []);
        }
        
        // 限制缓存大小
        const cache = this._eventCache.get(eventType);
        if (cache.length >= this._maxCacheSize) {
            cache.shift(); // 移除最旧的事件
        }
        
        cache.push({
            payload: payload,
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
                console.log(`%c[EventBus] 🎯 处理缓存事件: ${eventType}`, 'color: #8BC34A');
            } catch (e) {
                console.error(`%c[EventBus] ❌ 处理缓存事件失败: ${eventType}`, 'color: #F44336', e);
            }
        }
        
        // 移除已处理的事件
        for (let i = processedIndices.length - 1; i >= 0; i--) {
            cache.splice(processedIndices[i], 1);
        }
    },
    
    // 清空所有监听器
    clear() {
        console.log(`%c[EventBus] 🧹 清空所有监听器`, 'color: #9E9E9E');
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
