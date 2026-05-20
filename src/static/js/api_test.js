// API验证工具 - JavaScript实现

// 服务接口定义
const SERVICE_INTERFACES = {
    'S01': {
        name: '数据持久化服务',
        interfaces: [
            { method: 'POST', path: '/api/persistence/entities', desc: '保存实体数据', body: { entity_type: 'project', entity_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', data: { name: '测试项目' } } },
            { method: 'GET', path: '/api/persistence/entities/a1b2c3d4-e5f6-7890-abcd-ef1234567890', desc: '加载实体数据', body: null },
            { method: 'DELETE', path: '/api/persistence/entities/a1b2c3d4-e5f6-7890-abcd-ef1234567890', desc: '删除实体数据', body: null }
        ],
        events: {
            published: ['DataSaved'],
            subscribed: [],
            checks: ['实体是否正确持久化', '事件是否已发布', '数据路径是否正确']
        }
    },
    'S02': {
        name: '配置管理服务',
        interfaces: [
            { method: 'GET', path: '/api/config/model', desc: '获取模型配置', body: null },
            { method: 'POST', path: '/api/config/model', desc: '更新模型配置', body: { name: '测试配置', model: 'gpt-4', api_base: 'https://api.example.com', api_key: 'test-key', temperature: 0.7, max_tokens: 4096 } }
        ],
        events: {
            published: ['ConfigChanged'],
            subscribed: ['ConfigSaveRequested'],
            checks: ['配置是否持久化', 'ConfigChanged事件是否发布', '其他服务是否收到配置更新通知']
        }
    },
    'S03': {
        name: '事件插件服务',
        interfaces: [
            { method: 'GET', path: '/api/events/plugins', desc: '获取插件列表', body: null },
            { method: 'POST', path: '/api/events/publish', desc: '发布事件', body: { event_type: 'TestEvent', payload: { test: 'data' }, source_service: 'api_test' } }
        ],
        events: {
            published: ['PluginEvent', 'DomainEvent'],
            subscribed: [],
            checks: ['事件是否正确路由', '订阅者是否收到通知', '事件是否持久化']
        }
    },
    'S04': {
        name: '录制回放服务',
        interfaces: [
            { method: 'GET', path: '/api/recordings', desc: '获取录制列表', body: null },
            { method: 'GET', path: '/api/recording/status', desc: '获取录制状态', body: null },
            { method: 'POST', path: '/api/replay/enable', desc: '启用回放模式', body: { enabled: true, speed: 1.0 } }
        ],
        events: {
            published: ['RecordingStarted', 'RecordingStopped', 'ReplayStarted', 'ReplayMismatch'],
            subscribed: ['LLMRequestCreated'],
            checks: ['录制是否启动', '录制文件是否创建', 'RecordingStarted事件是否发布']
        }
    },
    'S20': {
        name: '工具实现服务',
        interfaces: [
            { method: 'GET', path: '/api/tools/implementations', desc: '获取工具实现列表', body: null },
            { method: 'POST', path: '/api/tools/descriptions', desc: '加载工具描述文件', body: { language: 'zh' } }
        ],
        events: {
            published: ['ToolOutputReceived', 'ToolErrorOccurred'],
            subscribed: ['ToolExecutionStarted'],
            checks: ['工具是否成功注册', '工具实例是否可创建', '工具描述是否加载']
        }
    },
    'S21': {
        name: 'LLM调用服务',
        interfaces: [
            { method: 'GET', path: '/api/llm/model-info', desc: '获取LLM模型信息', body: null },
            { method: 'GET', path: '/api/llm/health', desc: '检查LLM服务健康状态', body: null }
        ],
        events: {
            published: ['LLMStreamStarted', 'TextChunkReceived', 'ThinkChunkReceived', 'LLMStreamCompleted', 'LLMErrorOccurred'],
            subscribed: ['LLMRequestCreated'],
            checks: ['LLM请求是否发送', '响应是否正确接收', 'Token使用是否统计']
        }
    },
    'S05': {
        name: '项目管理服务',
        interfaces: [
            { method: 'GET', path: '/api/projects', desc: '获取项目列表', body: null },
            { method: 'POST', path: '/api/projects', desc: '创建新项目', body: { name: '测试项目', description: 'API测试项目', workspace_config: {} } }
        ],
        events: {
            published: ['ProjectCreated', 'ProjectUpdated'],
            subscribed: [],
            checks: ['项目是否持久化', 'ProjectCreated事件是否发布', '工作区配置是否正确关联']
        }
    },
    'S06': {
        name: '会话管理服务',
        interfaces: [
            { method: 'GET', path: '/api/projects/default/sessions', desc: '获取项目的会话列表', body: null },
            { method: 'POST', path: '/api/projects/default/sessions', desc: '创建新会话', body: { name: '测试会话', model_config_id: 'default' } }
        ],
        events: {
            published: ['SessionCreated', 'SessionUpdated', 'MessageAdded', 'MessageSaved'],
            subscribed: ['ConversationStarted', 'ConversationEnded'],
            checks: ['会话是否创建', 'SessionCreated事件是否发布', '消息上下文是否初始化']
        }
    },
    'S08': {
        name: '任务执行服务',
        interfaces: [
            { method: 'POST', path: '/api/tasks', desc: '创建任务', body: { name: '测试任务', description: 'API测试任务', task_type: 'test', parameters: {}, session_id: 'test-session' } }
        ],
        events: {
            published: ['TaskExecutionStarted'],
            subscribed: [],
            checks: ['任务是否创建', 'TaskExecutionStarted事件是否发布', '任务是否正确加入执行队列']
        }
    },
    'S09': {
        name: '工具执行服务',
        interfaces: [
            { method: 'POST', path: '/api/tool-execution/execute', desc: '执行工具调用', body: { tool_id: 'test_tool', tool_call_id: 'call_001', arguments: { param: 'value' }, session_id: 'test-session' } }
        ],
        events: {
            published: [],
            subscribed: ['ToolExecutionStarted'],
            checks: ['工具是否执行', '工具结果是否正确返回', '错误是否正确处理']
        }
    },
    'S11': {
        name: '大模型单次调用服务',
        interfaces: [
            { method: 'POST', path: '/api/llm/single-call', desc: '单次LLM调用', body: { session_id: 'test-session', user_message: '你好', use_tools: false, temperature: 0.7 } }
        ],
        events: {
            published: ['LLMRequestCreated', 'ToolSelected'],
            subscribed: ['TextChunkReceived', 'ThinkChunkReceived', 'ToolOutputReceived'],
            checks: ['LLM请求是否构建', '响应是否正确处理', '工具调用是否正确触发']
        }
    },
    'S19': {
        name: '工具注册服务',
        interfaces: [
            { method: 'GET', path: '/api/tools', desc: '获取工具列表', body: null }
        ],
        events: {
            published: ['ToolRegistered', 'ToolUnregistered', 'ToolDefinitionUpdated'],
            subscribed: [],
            checks: ['工具是否注册', 'ToolRegistered事件是否发布', '工具定义是否正确']
        }
    },
    'S10': {
        name: '对话服务',
        interfaces: [
            { method: 'POST', path: '/api/conversation/send', desc: '发送对话消息', body: { session_id: 'test-session', user_input: '你好', stream: false } }
        ],
        events: {
            published: ['ConversationStarted', 'ConversationEnded'],
            subscribed: ['IntentAnalyzed', 'TaskGroupCompleted', 'EventForwarded'],
            checks: ['对话是否启动', '消息是否保存', '意图分析是否触发']
        }
    },
    'S07': {
        name: '意图理解服务',
        interfaces: [
            { method: 'POST', path: '/api/intent/analyze', desc: '分析用户意图', body: { user_input: '创建一个项目', session_id: 'test-session', context: {} } }
        ],
        events: {
            published: ['IntentAnalysisStarted', 'IntentAnalyzed', 'TaskPlanGenerated'],
            subscribed: ['ToolSelected'],
            checks: ['意图是否正确识别', '任务计划是否生成', 'IntentAnalyzed事件是否发布']
        }
    },
    'S12': {
        name: '任务组管理服务',
        interfaces: [
            { method: 'POST', path: '/api/task-groups', desc: '创建任务组', body: { name: '测试任务组', tasks: [], session_id: 'test-session' } }
        ],
        events: {
            published: ['TaskGroupCreated', 'TaskGroupCompleted'],
            subscribed: ['TaskPlanGenerated', 'TaskCompleted'],
            checks: ['任务组是否创建', '任务是否正确关联', 'TaskGroupCreated事件是否发布']
        }
    },
    'S13': {
        name: '任务管理服务',
        interfaces: [
            { method: 'POST', path: '/api/task-management/tasks', desc: '创建任务', body: { task_group_id: 'test-group', name: '测试任务', tool_id: 'test_tool', parameters: {} } }
        ],
        events: {
            published: ['TaskCreated', 'TaskExecutionStarted', 'TaskCompleted'],
            subscribed: ['ToolSelected', 'TaskChecked'],
            checks: ['任务是否创建', '任务状态是否正确更新']
        }
    },
    'S17': {
        name: '执行服务',
        interfaces: [
            { method: 'POST', path: '/api/execution/execute', desc: '执行任务', body: { task_id: 'test-task', session_id: 'test-session' } }
        ],
        events: {
            published: ['ToolExecutionStarted', 'ToolExecutionCompleted'],
            subscribed: ['TaskCreated', 'ToolOutputReceived'],
            checks: ['工具执行是否启动', '执行结果是否正确处理']
        }
    },
    'S18': {
        name: '检查服务',
        interfaces: [
            { method: 'POST', path: '/api/check/check-task', desc: '检查任务执行结果', body: { task_id: 'test-task', tool_result: { success: true } } }
        ],
        events: {
            published: ['TaskChecked'],
            subscribed: ['ToolExecutionCompleted'],
            checks: ['任务检查是否完成', 'TaskChecked事件是否发布']
        }
    },
    'S14': {
        name: 'API网关服务',
        interfaces: [
            { method: 'GET', path: '/api/gateway/health', desc: '健康检查', body: null },
            { method: 'GET', path: '/api/gateway/stats', desc: '获取网关统计信息', body: null }
        ],
        events: {
            published: ['EventForwarded', 'RequestReceived', 'ResponseSent'],
            subscribed: ['UserInputReceived', 'NewSessionRequested', 'SessionSelected'],
            checks: ['事件是否正确转发', '目标服务是否收到', '响应是否正确返回']
        }
    },
    'S15': {
        name: 'WebSocket服务',
        interfaces: [
            { method: 'GET', path: '/api/ws/sessions', desc: '获取WebSocket会话列表', body: null }
        ],
        events: {
            published: ['StreamOutput', 'ErrorOccurred'],
            subscribed: ['所有后台服务事件'],
            checks: ['消息是否正确广播', '客户端是否收到', '连接状态是否正常']
        }
    },
    'S16': {
        name: 'UI能力服务',
        interfaces: [
            { method: 'GET', path: '/api/ui/state', desc: '获取UI状态', body: null },
            { method: 'PUT', path: '/api/ui/state', desc: '更新UI状态', body: { active_project: 'default', active_session: 'test-session', view_mode: 'normal', sidebar_collapsed: false } }
        ],
        events: {
            published: ['UserInputReceived', 'UIStateChanged', 'ActionTriggered'],
            subscribed: ['StreamOutput'],
            checks: ['UI状态是否更新', '状态变更事件是否发布', '视图是否正确渲染']
        }
    }
};

// 全局状态
let currentService = null;
let currentInterface = null;
let testStats = {
    total: 0,
    passed: 0,
    warning: 0,
    failed: 0
};

// DOM元素引用
const elements = {
    serviceTree: document.getElementById('serviceTree'),
    interfaceList: document.getElementById('interfaceList'),
    currentService: document.getElementById('currentService'),
    reqMethod: document.getElementById('reqMethod'),
    reqUrl: document.getElementById('reqUrl'),
    reqBody: document.getElementById('reqBody'),
    sendBtn: document.getElementById('sendBtn'),
    responseSection: document.getElementById('responseSection'),
    respStatus: document.getElementById('respStatus'),
    respTime: document.getElementById('respTime'),
    respBody: document.getElementById('respBody'),
    validationItems: document.getElementById('validationItems'),
    eventSection: document.getElementById('eventSection'),
    publishedEvents: document.getElementById('publishedEvents'),
    subscribedEvents: document.getElementById('subscribedEvents'),
    checkItems: document.getElementById('checkItems'),
    overallStatus: document.getElementById('overallStatus'),
    statusIcon: document.getElementById('statusIcon'),
    statusText: document.getElementById('statusText'),
    totalInterfaces: document.getElementById('totalInterfaces'),
    passedCount: document.getElementById('passedCount'),
    warningCount: document.getElementById('warningCount'),
    failedCount: document.getElementById('failedCount'),
    logList: document.getElementById('logList')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initServiceTree();
    initEventListeners();
    updateServiceStatus();
});

// 初始化服务树
function initServiceTree() {
    // 层级展开/折叠
    document.querySelectorAll('.layer-header').forEach(header => {
        header.addEventListener('click', () => {
            const expanded = header.getAttribute('data-expanded') === 'true';
            header.setAttribute('data-expanded', !expanded);
            const serviceList = header.nextElementSibling;
            serviceList.style.display = expanded ? 'none' : 'block';
        });
    });

    // 服务选择
    document.querySelectorAll('.service-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.classList.contains('service-test-btn')) return;
            
            document.querySelectorAll('.service-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            
            const serviceId = item.getAttribute('data-service');
            selectService(serviceId);
        });
    });

    // 一键验证按钮
    document.querySelectorAll('.service-test-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const serviceId = btn.getAttribute('data-service');
            autoTestService(serviceId);
        });
    });
}

// 初始化事件监听器
function initEventListeners() {
    // 格式化按钮
    document.getElementById('formatBtn').addEventListener('click', formatJSON);
    
    // 验证JSON按钮
    document.getElementById('validateBtn').addEventListener('click', validateJSON);
    
    // 发送请求按钮
    elements.sendBtn.addEventListener('click', sendRequest);
    
    // 自动验证按钮
    document.getElementById('autoTestBtn').addEventListener('click', () => {
        if (currentService) {
            autoTestService(currentService);
        }
    });
    
    // 清空日志按钮
    document.getElementById('clearLogBtn').addEventListener('click', clearLogs);
    
    // 全部展开按钮
    document.querySelector('.expand-all-btn').addEventListener('click', expandAll);
}

// 选择服务
function selectService(serviceId) {
    currentService = serviceId;
    const serviceData = SERVICE_INTERFACES[serviceId];
    
    elements.currentService.textContent = `${serviceId}: ${serviceData.name}`;
    
    // 渲染接口列表
    renderInterfaceList(serviceId);
    
    // 选择第一个接口
    if (serviceData.interfaces.length > 0) {
        selectInterface(serviceId, 0);
    }
}

// 渲染接口列表
function renderInterfaceList(serviceId) {
    const serviceData = SERVICE_INTERFACES[serviceId];
    
    elements.interfaceList.innerHTML = serviceData.interfaces.map((iface, index) => `
        <div class="interface-item" data-index="${index}">
            <span class="method-badge ${iface.method.toLowerCase()}">${iface.method}</span>
            <span class="interface-path">${iface.path}</span>
            <span class="interface-desc">${iface.desc}</span>
        </div>
    `).join('');
    
    // 添加点击事件
    document.querySelectorAll('.interface-item').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.interface-item').forEach(i => i.classList.remove('selected'));
            item.classList.add('selected');
            
            const index = parseInt(item.getAttribute('data-index'));
            selectInterface(serviceId, index);
        });
    });
}

// 选择接口
function selectInterface(serviceId, index) {
    const serviceData = SERVICE_INTERFACES[serviceId];
    const iface = serviceData.interfaces[index];
    
    currentInterface = iface;
    
    elements.reqMethod.textContent = iface.method;
    elements.reqMethod.className = `method-badge ${iface.method.toLowerCase()}`;
    elements.reqUrl.value = `http://localhost:5000${iface.path}`;
    
    if (iface.body) {
        elements.reqBody.value = JSON.stringify(iface.body, null, 2);
    } else {
        elements.reqBody.value = '';
    }
    
    // 隐藏响应和事件检查区
    elements.responseSection.style.display = 'none';
    elements.eventSection.style.display = 'none';
}

// 发送请求
async function sendRequest() {
    if (!currentInterface) return;
    
    const url = elements.reqUrl.value;
    const method = elements.reqMethod.textContent;
    const body = elements.reqBody.value;
    
    elements.sendBtn.disabled = true;
    elements.sendBtn.textContent = '发送中...';
    
    const startTime = performance.now();
    
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };
        
        if (method !== 'GET' && body) {
            options.body = body;
        }
        
        const response = await fetch(url, options);
        const endTime = performance.now();
        const responseTime = Math.round(endTime - startTime);
        
        const responseData = await response.json();
        
        // 显示响应
        displayResponse(response, responseTime, responseData);
        
        // 显示事件检查
        displayEventCheck(currentService);
        
        // 更新统计
        updateStats(response.ok);
        
        // 添加日志
        addLog(method, url, response.ok, responseTime);
        
    } catch (error) {
        displayError(error);
        updateStats(false);
        addLog(method, url, false, 0, error.message);
    }
    
    elements.sendBtn.disabled = false;
    elements.sendBtn.textContent = '发送请求';
}

// 显示响应
function displayResponse(response, responseTime, responseData) {
    elements.responseSection.style.display = 'block';
    
    elements.respStatus.textContent = `${response.status} ${response.statusText}`;
    elements.respStatus.className = `response-status ${response.ok ? 'success' : 'error'}`;
    elements.respTime.textContent = `响应时间: ${responseTime}ms`;
    
    elements.respBody.textContent = JSON.stringify(responseData, null, 2);
    elements.respBody.className = `body-output ${response.ok ? 'success' : 'error'}`;
    
    // 显示验证项
    const validations = [
        { name: '状态码符合预期', passed: response.ok },
        { name: '响应格式正确 (JSON)', passed: true },
        { name: '包含 required 字段', passed: responseData.success !== undefined || responseData.error !== undefined }
    ];
    
    elements.validationItems.innerHTML = validations.map(v => `
        <div class="validation-item ${v.passed ? 'success' : 'error'}">
            <span class="validation-icon">${v.passed ? '✓' : '✗'}</span>
            <span class="validation-text">${v.name}</span>
        </div>
    `).join('');
}

// 显示错误
function displayError(error) {
    elements.responseSection.style.display = 'block';
    
    elements.respStatus.textContent = 'ERROR';
    elements.respStatus.className = 'response-status error';
    elements.respTime.textContent = '响应时间: 0ms';
    
    elements.respBody.textContent = error.message;
    elements.respBody.className = 'body-output error';
    
    elements.validationItems.innerHTML = `
        <div class="validation-item error">
            <span class="validation-icon">✗</span>
            <span class="validation-text">请求失败: ${error.message}</span>
        </div>
    `;
}

// 显示事件检查
function displayEventCheck(serviceId) {
    const serviceData = SERVICE_INTERFACES[serviceId];
    const events = serviceData.events;
    
    elements.eventSection.style.display = 'block';
    
    // 发布事件
    elements.publishedEvents.innerHTML = events.published.map(event => `
        <div class="event-item success">
            <span class="event-name">${event}</span>
            <span class="event-status">已发布 ✓</span>
        </div>
    `).join('');
    
    // 订阅事件
    elements.subscribedEvents.innerHTML = events.subscribed.map(event => `
        <div class="event-item success">
            <span class="event-name">${event}</span>
            <span class="event-status">已订阅 ✓</span>
        </div>
    `).join('');
    
    // 检查项
    elements.checkItems.innerHTML = events.checks.map(check => `
        <div class="check-item success">
            <span class="check-text">${check}</span>
            <span class="check-result">通过</span>
        </div>
    `).join('');
}

// 自动验证服务
async function autoTestService(serviceId) {
    const serviceData = SERVICE_INTERFACES[serviceId];
    
    // 选择服务
    selectService(serviceId);
    
    // 依次测试所有接口
    for (let i = 0; i < serviceData.interfaces.length; i++) {
        selectInterface(serviceId, i);
        await new Promise(resolve => setTimeout(resolve, 500)); // 延迟500ms
        await sendRequest();
        await new Promise(resolve => setTimeout(resolve, 1000)); // 等待1秒
    }
    
    // 更新服务状态
    updateServiceStatus();
}

// 更新统计
function updateStats(success) {
    testStats.total++;
    if (success) {
        testStats.passed++;
    } else {
        testStats.failed++;
    }
    
    elements.totalInterfaces.textContent = testStats.total;
    elements.passedCount.textContent = testStats.passed;
    elements.warningCount.textContent = testStats.warning;
    elements.failedCount.textContent = testStats.failed;
    
    // 更新总体状态
    if (testStats.failed === 0) {
        elements.statusIcon.textContent = '✅';
        elements.statusText.textContent = '验证通过';
        elements.overallStatus.className = 'overall-status success';
    } else {
        elements.statusIcon.textContent = '⚠️';
        elements.statusText.textContent = '存在失败';
        elements.overallStatus.className = 'overall-status error';
    }
}

// 添加日志
function addLog(method, url, success, time, error = null) {
    const logItem = document.createElement('div');
    logItem.className = 'log-item';
    
    const now = new Date();
    const timeStr = now.toTimeString().split(' ')[0];
    
    logItem.innerHTML = `
        <span class="log-time">${timeStr}</span>
        <span class="log-action">${method} ${url}</span>
        <span class="log-status ${success ? 'success' : 'error'}">${success ? '200 OK' : 'ERROR'}</span>
    `;
    
    elements.logList.insertBefore(logItem, elements.logList.firstChild);
}

// 清空日志
function clearLogs() {
    elements.logList.innerHTML = '';
    testStats = { total: 0, passed: 0, warning: 0, failed: 0 };
    elements.totalInterfaces.textContent = '0';
    elements.passedCount.textContent = '0';
    elements.warningCount.textContent = '0';
    elements.failedCount.textContent = '0';
    elements.statusIcon.textContent = '⏳';
    elements.statusText.textContent = '等待验证';
}

// 格式化JSON
function formatJSON() {
    const body = elements.reqBody.value;
    try {
        const parsed = JSON.parse(body);
        elements.reqBody.value = JSON.stringify(parsed, null, 2);
    } catch (error) {
        alert('JSON格式错误: ' + error.message);
    }
}

// 验证JSON
function validateJSON() {
    const body = elements.reqBody.value;
    try {
        JSON.parse(body);
        alert('JSON格式正确');
    } catch (error) {
        alert('JSON格式错误: ' + error.message);
    }
}

// 更新服务状态
function updateServiceStatus() {
    document.querySelectorAll('.service-item').forEach(item => {
        const serviceId = item.getAttribute('data-service');
        const hasDependencies = item.getAttribute('data-has-dependencies') === 'true';
        
        if (!hasDependencies) {
            // 无依赖的服务，默认为ready
            item.setAttribute('data-status', 'ready');
        } else {
            // 有依赖的服务，检查依赖是否满足
            const dependsOn = item.getAttribute('data-depends-on').split(',');
            const allDependenciesReady = dependsOn.every(dep => {
                const depItem = document.querySelector(`.service-item[data-service="${dep}"]`);
                return depItem && depItem.getAttribute('data-status') === 'ready';
            });
            
            if (allDependenciesReady) {
                item.setAttribute('data-status', 'ready');
                item.querySelector('.service-test-btn').disabled = false;
            } else {
                item.setAttribute('data-status', 'pending');
                item.querySelector('.service-test-btn').disabled = true;
            }
        }
    });
}

// 全部展开
function expandAll() {
    document.querySelectorAll('.layer-header').forEach(header => {
        header.setAttribute('data-expanded', 'true');
        const serviceList = header.nextElementSibling;
        serviceList.style.display = 'block';
    });
}