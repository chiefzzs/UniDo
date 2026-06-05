import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// 辅助函数：计算两个字符串的公共前缀长度
function findCommonPrefixLength(a: string, b: string): number {
  let i = 0;
  while (i < a.length && i < b.length && a[i] === b[i]) {
    i++;
  }
  return i;
}

// 读取 llm_calls.json 并解析详细交互过程
function getExpectedInteractions(): any {
  const llmCallsPath = path.join('d:', 'learnning', '260521', 'src', 'bak', 'llm_calls3.json');
  if (!fs.existsSync(llmCallsPath)) {
    return null;
  }

  const content = fs.readFileSync(llmCallsPath, 'utf-8');
  const calls = JSON.parse(content);

  // 按 dialog_id 分组
  const dialogs: Map<string, {
    userInput: string,
    llmInteractions: Array<{
      text: string,
      thinking: string,
      toolCalls: Array<{name: string, args: any}>,
    }>
  }> = new Map();

  for (const call of calls) {
    const did = call.dialog_id;
    if (!dialogs.has(did)) {
      const msgs = call.request?.messages || [];
      const userMsg = msgs.find((m: any) => m.role === 'user');
      // 处理 content 可能是数组的情况（统一使用数组格式）
      let userInput = userMsg?.content || '';
      if (Array.isArray(userInput)) {
        userInput = userInput.map((item: any) => {
          if (typeof item === 'object' && item.type === 'text') {
            return item.text;
          }
          return String(item);
        }).join('');
      }
      dialogs.set(did, {
        userInput,
        llmInteractions: []
      });
    }

    const dialog = dialogs.get(did)!;
    const resp = call.response || {};
    const toolCalls = resp.tool_calls || [];

    // 解析工具调用参数
    const parsedToolCalls = toolCalls.map((tc: any) => {
      const args = tc.function?.arguments || '{}';
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(args);
      } catch {}
      return {
        name: tc.function?.name || 'unknown',
        args: parsedArgs
      };
    });

    dialog.llmInteractions.push({
      text: resp.content || '',
      thinking: resp.thinking || '',
      toolCalls: parsedToolCalls
    });
  }

  // 转换为数组并计算统计
  const result: any[] = [];
  for (const [dialogId, data] of dialogs.entries()) {
    const textReplies = data.llmInteractions.filter(i => i.text && i.text.trim().length > 0);

    result.push({
      dialogId,
      userInput: data.userInput,
      interactions: data.llmInteractions,
      // 统计
      textReplyCount: textReplies.length,
      textReplies: textReplies.map(t => t.text),
      toolCallCount: data.llmInteractions.reduce((sum, i) => sum + i.toolCalls.length, 0),
      toolCalls: data.llmInteractions.flatMap(i => i.toolCalls),
    });
  }

  // 返回包含原始calls数组和分组数据的结果
  return {
    rawCalls: calls,  // 原始LLM调用数组
    dialogs: result   // 按dialog_id分组的数据
  };
}

test.describe('回放模式一致性测试 - 基于 llm_calls.json 详细检查点', () => {
  // 测试前清理环境（模拟 clean_test_data.bat 的逻辑）
  test.beforeAll(() => {
    console.log('[Test] ======== 开始环境清理 ========');

    const testDataDir = path.join('d:', 'learnning', '260521', 'src', 'data', 'test');
    const keepFiles = ['projects.json', 'model_configs.json', 'workspace_configs.json'];

    // 删除所有 JSON 文件，除了需要保留的
    if (fs.existsSync(testDataDir)) {
      const files = fs.readdirSync(testDataDir);
      for (const file of files) {
        if (file.endsWith('.json')) {
          const filePath = path.join(testDataDir, file);
          if (!keepFiles.includes(file)) {
            fs.unlinkSync(filePath);
            console.log(`[Test] 删除: ${file}`);
          } else {
            console.log(`[Test] 保留: ${file}`);
          }
        }
      }
    }

    // 复制 llm_calls.json 到测试目录
    const srcLlmcalls = path.join('d:', 'learnning', '260521', 'src', 'bak', 'llm_calls.json');
    const destLlmcalls = path.join(testDataDir, 'llm_calls.json');
    
    if (fs.existsSync(srcLlmcalls)) {
      fs.copyFileSync(srcLlmcalls, destLlmcalls);
      console.log(`[Test] 复制: ${srcLlmcalls} -> ${destLlmcalls}`);
    } else {
      console.log(`[Test] ❌ 警告: 源文件不存在 - ${srcLlmcalls}`);
    }

    console.log('[Test] ======== 环境清理完成 ========');
  });

  test('验证界面显示与 llm_calls.json 详细交互过程一致', async ({ page }) => {
    // 设置测试超时时间为 3 分钟
    test.setTimeout(180000);
    
    // 1. 读取预期结果
    const expected = getExpectedInteractions();
    if (!expected) {
      throw new Error('无法读取 llm_calls.json');
    }
    const rawCalls = expected.rawCalls;  // 原始LLM调用数组
    const dialogs = expected.dialogs;    // 按dialog_id分组的数据

    console.log('[Test] ========== 预期交互过程 (llm_calls.json) ==========');
    for (const dialog of dialogs) {
      console.log(`\n--- 对话: ${dialog.dialogId} ---`);
      console.log(`用户输入: ${dialog.userInput.substring(0, 80)}...`);
      console.log(`文本回复数: ${dialog.textReplyCount}`);
      console.log(`工具调用总数: ${dialog.toolCallCount}`);
      dialog.toolCalls.forEach((tc: any, i: number) => {
        console.log(`  工具${i+1}: ${tc.name}()`);
      });
    }

    // ========== 2. 准备：注入插件式事件捕获系统 ==========
    await page.addInitScript(() => {
      // 事件捕获插件系统
      (window as any).eventCapture = {
        events: [],
        handlers: new Map(),
        initialized: false,
        
        // 注册事件处理器
        on(eventType: string, handler: (data: any) => void) {
          if (!this.handlers.has(eventType)) {
            this.handlers.set(eventType, []);
          }
          this.handlers.get(eventType).push(handler);
        },
        
        // 触发事件
        emit(eventType: string, data: any) {
          // 保存所有事件（包含完整的data对象）
          this.events.push({ 
            type: eventType, 
            timestamp: Date.now(), 
            data: JSON.parse(JSON.stringify(data))  // 深拷贝
          });
          
          // 触发所有注册的处理器
          if (this.handlers.has(eventType)) {
            this.handlers.get(eventType).forEach(handler => {
              try {
                handler(data);
              } catch (e) {
                console.error('[EventCapture] Handler error:', e);
              }
            });
          }
        },
        
        // 获取所有事件
        getAllEvents() {
          return [...this.events];
        },
        
        // 按类型过滤事件
        getEventsByType(eventType: string) {
          return this.events.filter(e => e.type === eventType);
        },
        
        // 按类型前缀过滤事件
        getEventsByTypePrefix(prefix: string) {
          return this.events.filter(e => e.type.startsWith(prefix));
        },
        
        // 清空事件
        clear() {
          this.events = [];
        },
        
        // 获取事件统计
        getStats() {
          const stats: any = {
            total: this.events.length,
            byType: {}
          };
          this.events.forEach(e => {
            stats.byType[e.type] = (stats.byType[e.type] || 0) + 1;
          });
          return stats;
        },
        
        // 获取所有request_id
        getRequestIds() {
          const ids = new Set<string>();
          this.events.forEach(e => {
            if (e.data?.request_id) ids.add(e.data.request_id);
            if (e.data?.data?.request_id) ids.add(e.data.data.request_id);
          });
          return Array.from(ids);
        },
        
        // 获取所有dialog_id
        getDialogIds() {
          const ids = new Set<string>();
          this.events.forEach(e => {
            if (e.data?.dialog_id) ids.add(e.data.dialog_id);
            if (e.data?.data?.dialog_id) ids.add(e.data.data.dialog_id);
          });
          return Array.from(ids);
        },
        
        // 初始化WebSocket消息捕获
        initWsCapture() {
          if (this.initialized) return;
          if (!window.EventBus || !window.EventBus.on) {
            console.warn('[EventCapture] EventBus not available, retrying...');
            setTimeout(() => this.initWsCapture(), 100);
            return;
          }
          
          console.log('[EventCapture] Initializing WebSocket capture');
          window.EventBus.on('ws:message', (data: any) => {
            const eventType = data.action || data.type || 'unknown';
            window.eventCapture.emit(eventType, data);
          });
          this.initialized = true;
        }
      };
      
      // 捕获console.log输出
      (window as any).consoleLogs = [];
      const originalLog = console.log;
      const originalWarn = console.warn;
      const originalError = console.error;
      
      console.log = function(...args: any[]) {
        window.consoleLogs.push({
          type: 'log',
          timestamp: Date.now(),
          args: args.map(arg => {
            try {
              if (typeof arg === 'object') {
                return JSON.parse(JSON.stringify(arg));
              }
              return arg;
            } catch {
              return String(arg);
            }
          })
        });
        originalLog.apply(console, args);
      };
      
      console.warn = function(...args: any[]) {
        window.consoleLogs.push({
          type: 'warn',
          timestamp: Date.now(),
          args: args.map(arg => {
            try {
              if (typeof arg === 'object') {
                return JSON.parse(JSON.stringify(arg));
              }
              return arg;
            } catch {
              return String(arg);
            }
          })
        });
        originalWarn.apply(console, args);
      };
      
      console.error = function(...args: any[]) {
        window.consoleLogs.push({
          type: 'error',
          timestamp: Date.now(),
          args: args.map(arg => {
            try {
              if (typeof arg === 'object') {
                return JSON.parse(JSON.stringify(arg));
              }
              return arg;
            } catch {
              return String(arg);
            }
          })
        });
        originalError.apply(console, args);
      };
      
      // 捕获ChatManager处理记录
      if (window.ChatManager) {
        const originalHandleWSMessage = window.ChatManager.handleWSMessage;
        window.ChatManager._messageProcessingRecords = [];
        window.ChatManager._processingStats = {
          processed: 0,
          modified: 0,
          attached: 0,
          abandoned: 0,
          byAction: {}
        };
        
        window.ChatManager.handleWSMessage = function(data: any) {
          const startTime = Date.now();
          const action = data.action || data.type || 'unknown';
          const messageId = data.message_id || data.data?.message_id || 'unknown';
          
          let result = 'processed';
          const details: any = { action, messageId };
          
          try {
            originalHandleWSMessage.call(this, data);
            
            // 检查是否被抛弃
            if (data.action === 'round.completed') {
              result = 'abandoned';
              details.reason = 'round.completed is configured to be abandoned';
            }
          } catch (error: any) {
            result = 'error';
            details.error = error.message;
          }
          
          const duration = Date.now() - startTime;
          
          window.ChatManager._messageProcessingRecords.push({
            action,
            messageId,
            result,
            details,
            duration,
            timestamp: Date.now(),
            rawData: JSON.parse(JSON.stringify(data))
          });
          
          window.ChatManager._processingStats.processed++;
          window.ChatManager._processingStats[result + 'd'] = 
            (window.ChatManager._processingStats[result + 'd'] || 0) + 1;
          window.ChatManager._processingStats.byAction[action] = 
            (window.ChatManager._processingStats.byAction[action] || 0) + 1;
        };
      }
    });

    // 3. 打开页面
    await page.goto('http://localhost:8000/');
    await page.waitForLoadState('networkidle');
    
    // ========== 初始化插件式事件捕获系统 ==========
    await page.waitForFunction('window.eventCapture !== undefined', { timeout: 10000 });
    await page.evaluate(() => {
      window.eventCapture.initWsCapture();
    });
    
    await page.waitForTimeout(2000);

    // 4. 关键步骤：切换模式确保回放计数器复位
    // 无论当前是什么模式，都执行完整的"录制->回放"切换流程
    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();

    let currentModeText = await toggle.textContent();
    console.log('[Test] 当前模式:', currentModeText);

    // 判断当前模式：录制模式显示"📹 录制"，回放模式显示"🔄 回放"
    const isReplayMode = currentModeText.includes('回放') || currentModeText.includes('🔄');
    
    // 确保先切换到录制模式（复位计数器的关键步骤）
    if (isReplayMode) {
      // 当前是回放模式，先切换到录制模式
      await toggle.click();
      await page.waitForTimeout(3000);
      console.log('[Test] 已从回放模式切换到录制模式');
    }
    
    // 再切换到回放模式（这是第二次切换，确保计数器完全复位）
    await toggle.click();
    await page.waitForTimeout(3000);
    console.log('[Test] 已切换到回放模式（计数器已复位）');

    // 确认最终处于回放模式
    currentModeText = await toggle.textContent();
    console.log('[Test] 最终模式:', currentModeText);
    const isFinalReplayMode = currentModeText.includes('回放') || currentModeText.includes('🔄');
    expect(isFinalReplayMode).toBe(true);

    // 5. 选择第一个项目
    const projectSelect = page.locator('.project-select');
    await projectSelect.waitFor();
    await page.waitForTimeout(2000);

    const projectOptions = await projectSelect.locator('option').all();
    if (projectOptions.length > 1) {
      await projectSelect.selectOption({ index: 1 });
    }
    await page.waitForTimeout(1500);

    // 6. 创建新 session（点击"+ 新建"按钮）
    console.log('[Test] 点击"+ 新建"按钮创建会话...');
    const newBtn = page.locator('button:has-text("+ 新建")');
    await newBtn.waitFor({ timeout: 5000 });
    await newBtn.click();
    await page.waitForTimeout(3000);
    console.log('[Test] 会话创建完成');

    // 7. 发送消息触发回放
    console.log('\n[Test] ========== 发送消息触发回放 ==========');
    
    const textarea = page.locator('textarea').first();
    await textarea.waitFor({ timeout: 5000 });

    await textarea.fill('xxx');
    await textarea.press('Enter');
    console.log('[Test] 已发送第一条消息');
    // 等待第一条消息完全处理完成（包括所有工具调用）
    await page.waitForTimeout(30000);

    await textarea.fill('yyy');
    await textarea.press('Enter');
    console.log('[Test] 已发送第二条消息');
    await page.waitForTimeout(30000);

    // 8. 收集页面上的消息详情（包括思考内容和文本内容）
    const messageDetails = await page.evaluate(() => {
      const items: any[] = [];
      document.querySelectorAll('.message-item').forEach((item) => {
        const isUser = item.classList.contains('user-message');
        const isAssistant = item.classList.contains('assistant-message');

        if (!isUser && !isAssistant) return;

        const role = isUser ? 'user' : 'assistant';
        const contentEl = item.querySelector('.message-content, .message-text');
        const content = contentEl?.textContent?.trim() || '';

        // 收集思考内容
        const thinkingEl = item.querySelector('.thinking, .thought, .reasoning');
        const thinking = thinkingEl?.textContent?.trim() || '';

        // 收集工具调用
        const toolCards = item.querySelectorAll('.tool-execution-card');
        const tools: string[] = [];
        toolCards.forEach(card => {
          const nameEl = card.querySelector('.tool-name, .tool-call-name');
          if (nameEl) {
            tools.push(nameEl.textContent?.trim() || '');
          }
        });

        // 收集工具执行结果
        const toolResults: string[] = [];
        const resultEls = item.querySelectorAll('.tool-result, .execution-result');
        resultEls.forEach(el => {
          toolResults.push(el.textContent?.trim().substring(0, 100) || '');
        });

        items.push({
          role,
          contentLength: content.length,
          contentPreview: content.substring(0, 200),
          contentFull: content,
          thinkingLength: thinking.length,
          thinkingPreview: thinking.substring(0, 200),
          thinkingFull: thinking,
          toolCalls: tools,
          toolCallCount: tools.length,
          toolResults: toolResults
        });
      });
      return items;
    });

    // 记录第一个会话的消息数量（用于后续切换测试验证）
    const firstSessionMessageCount = messageDetails.length;
    console.log(`[Test] 第一个会话消息数: ${firstSessionMessageCount}`);
    
    // 9. 创建第二个会话（用于后续切换测试）
    console.log('\n[Test] ========== 创建第二个会话 ==========');
    
    // 点击新建会话按钮创建第二个会话
    const newSessionBtn = page.locator('.btn.btn-sm.btn-outline');
    await newSessionBtn.waitFor();
    await newSessionBtn.click();
    await page.waitForTimeout(3000);
    console.log('[Test] 已创建第二个会话');

    // ========== 获取捕获的事件（使用插件系统） ==========
    const capturedEvents = await page.evaluate(() => {
      return (window as any).eventCapture?.getAllEvents() || [];
    });
    
    // 转换为测试需要的格式
    const receivedEvents = capturedEvents.map(e => e.data);
    
    // ========== 获取控制台日志 ==========
    const consoleLogs = await page.evaluate(() => {
      return (window as any).consoleLogs || [];
    });
    
    // ========== 获取事件统计 ==========
    const eventStats = await page.evaluate(() => {
      return (window as any).eventCapture?.getStats() || {};
    });
    
    // ========== 获取request_id列表 ==========
    const requestIds = await page.evaluate(() => {
      return (window as any).eventCapture?.getRequestIds() || [];
    });
    
    // ========== 获取dialog_id列表 ==========
    const dialogIds = await page.evaluate(() => {
      return (window as any).eventCapture?.getDialogIds() || [];
    });

    // 8. 输出实际结果对比
    console.log('\n[Test] ========== 实际显示结果 (UI) ==========');
    for (let i = 0; i < messageDetails.length; i++) {
      const msg = messageDetails[i];
      console.log(`\n--- 消息 ${i+1} ---`);
      console.log(`角色: ${msg.role}`);
      console.log(`内容长度: ${msg.contentLength} 字符`);
      console.log(`内容预览: ${msg.contentPreview}...`);
      console.log(`思考内容长度: ${msg.thinkingLength} 字符`);
      console.log(`思考内容预览: ${msg.thinkingPreview || '(空)'}`);
      console.log(`工具调用数: ${msg.toolCallCount}`);
      msg.toolCalls.forEach((tool: string, j: number) => {
        console.log(`  工具${j+1}: ${tool}`);
      });
      if (msg.toolResults.length > 0) {
        console.log(`工具执行结果数: ${msg.toolResults.length}`);
        msg.toolResults.forEach((result: string, j: number) => {
          console.log(`  结果${j+1}: ${result}...`);
        });
      }
    }

    // ========== 新增：打印收到的报文 ==========
    console.log('\n[Test] ========== 收到的WebSocket事件报文 ==========');
    console.log(`总共收到 ${receivedEvents.length} 个事件\n`);
    
    for (let i = 0; i < receivedEvents.length; i++) {
      const event = receivedEvents[i];
      console.log(`--- 报文 ${i+1} ---`);
      console.log(`  action: ${event.action || event.type || 'unknown'}`);
      console.log(`  dialog_id: ${event.data?.dialog_id || event.dialog_id || 'N/A'}`);
      console.log(`  request_id: ${event.data?.request_id || event.request_id || 'N/A'}`);
      if (event.data?.content) {
        console.log(`  content: "${event.data.content.substring(0, 50)}..."`);
      }
      console.log('');
    }
    
    // ========== 分析控制台日志 ==========
    console.log('\n[Test] ========== 控制台日志分析 ==========');
    console.log(`总共捕获 ${consoleLogs.length} 条日志\n`);
    
    // 过滤关键警告和错误
    const warnings = consoleLogs.filter(log => log.type === 'warn');
    const errors = consoleLogs.filter(log => log.type === 'error');
    const chatManagerLogs = consoleLogs.filter(log => 
      log.args.some(arg => typeof arg === 'string' && arg.includes('[ChatManager]'))
    );
    const eventBusLogs = consoleLogs.filter(log => 
      log.args.some(arg => typeof arg === 'string' && arg.includes('[EventBus]'))
    );
    
    console.log(`⚠️ 警告数: ${warnings.length}`);
    console.log(`❌ 错误数: ${errors.length}`);
    console.log(`📬 ChatManager日志数: ${chatManagerLogs.length}`);
    console.log(`📡 EventBus日志数: ${eventBusLogs.length}`);
    
    // 输出所有警告
    if (warnings.length > 0) {
      console.log('\n--- 警告详情 ---');
      warnings.forEach((log, i) => {
        console.log(`${i+1}. ${log.args.map(a => typeof a === 'string' ? a : JSON.stringify(a)).join(' ')}`);
      });
    }
    
    // 输出所有错误
    if (errors.length > 0) {
      console.log('\n--- 错误详情 ---');
      errors.forEach((log, i) => {
        console.log(`${i+1}. ${log.args.map(a => typeof a === 'string' ? a : JSON.stringify(a)).join(' ')}`);
      });
    }
    
    // 分析ChatManager处理日志
    console.log('\n--- ChatManager处理日志分析 ---');
    const processedActions: {action: string, count: number}[] = [];
    const abandonedActions: {action: string, count: number}[] = [];
    const unhandledActions: {action: string, count: number}[] = [];
    
    chatManagerLogs.forEach(log => {
      const logStr = log.args.find((a: any) => typeof a === 'string') || '';
      if (logStr.includes('未处理的消息')) {
        const match = logStr.match(/未处理的消息.*: (\w+\.\w+)/);
        if (match) {
          const action = match[1];
          const existing = unhandledActions.find(a => a.action === action);
          if (existing) {
            existing.count++;
          } else {
            unhandledActions.push({action, count: 1});
          }
        }
      } else if (logStr.includes('已配置为抛弃')) {
        const match = logStr.match(/消息已配置为抛弃: (\w+\.\w+)/);
        if (match) {
          const action = match[1];
          const existing = abandonedActions.find(a => a.action === action);
          if (existing) {
            existing.count++;
          } else {
            abandonedActions.push({action, count: 1});
          }
        }
      } else if (logStr.includes('条件不匹配跳过')) {
        const match = logStr.match(/条件不匹配跳过:.*(\w+\.\w+)/);
        if (match) {
          const action = match[1];
          const existing = unhandledActions.find(a => a.action === action);
          if (existing) {
            existing.count++;
          } else {
            unhandledActions.push({action, count: 1});
          }
        }
      }
    });
    
    console.log('\n📊 事件处理统计:');
    console.log('| 状态 | 事件类型 | 数量 |');
    console.log('|------|---------|------|');
    
    unhandledActions.forEach(a => {
      console.log(`| ⚠️ 未处理 | ${a.action} | ${a.count} |`);
    });
    
    abandonedActions.forEach(a => {
      console.log(`| 🚮 抛弃 | ${a.action} | ${a.count} |`);
    });
    
    // 分析EventBus日志中的订阅情况
    console.log('\n--- EventBus订阅情况分析 ---');
    const subscribedEvents: Set<string> = new Set();
    const unsubscribedEvents: Set<string> = new Set();
    
    eventBusLogs.forEach(log => {
      const logStr = log.args.find((a: any) => typeof a === 'string') || '';
      if (logStr.includes('无人订阅')) {
        const match = logStr.match(/事件 (\w+\.\w+) 无人订阅/);
        if (match) {
          unsubscribedEvents.add(match[1]);
        }
      } else if (logStr.includes('消费中')) {
        const match = logStr.match(/消费中: (\w+)/);
        if (match) {
          subscribedEvents.add(match[1]);
        }
      }
    });
    
    console.log(`\n✅ 有订阅者的事件: ${subscribedEvents.size}个`);
    subscribedEvents.forEach(e => console.log(`  - ${e}`));
    
    console.log(`\n❌ 无人订阅的事件: ${unsubscribedEvents.size}个`);
    unsubscribedEvents.forEach(e => console.log(`  - ${e}`));
    
    // 检查关键事件是否收到
    console.log('\n--- 关键事件检查 ---');
    const keyEvents = [
      'llm.request_sent',
      'llm.call_text_completed',
      'llm.response_received',
      'llm.thinking',
      'llm.reasoning',
      'tool.call_started',
      'tool.execution_output',
      'tool.call_completed',
      'round.started',
      'round.completed'
    ];
    
    console.log('| 事件类型 | 是否收到 | 收到次数 |');
    console.log('|---------|---------|---------|');
    
    keyEvents.forEach(eventType => {
      const count = receivedEvents.filter(e => e.action === eventType || e.type === eventType).length;
      const status = count > 0 ? '✅' : '❌';
      console.log(`| ${eventType} | ${status} | ${count} |`);
    });
    
    // 分析request_id一致性
    console.log('\n--- Request ID分析 ---');
    console.log(`收到的request_id数量: ${requestIds.length}`);
    console.log(`request_id列表: ${requestIds.join(', ')}`);
    
    // 检查是否有request_id不匹配的情况
    const llmEvents = receivedEvents.filter(e => e.action?.startsWith('llm.') || e.type?.startsWith('llm.'));
    const requestSentIds = new Set<string>();
    const responseReceivedIds = new Set<string>();
    
    llmEvents.forEach(e => {
      const data = e.data || e;
      if (e.action === 'llm.request_sent' && data.request_id) {
        requestSentIds.add(data.request_id);
      }
      if (e.action === 'llm.response_received' && data.request_id) {
        responseReceivedIds.add(data.request_id);
      }
    });
    
    console.log(`\nllm.request_sent的request_id: ${Array.from(requestSentIds).join(', ')}`);
    console.log(`llm.response_received的request_id: ${Array.from(responseReceivedIds).join(', ')}`);
    
    const missingInResponse = Array.from(requestSentIds).filter(id => !responseReceivedIds.has(id));
    const missingInRequest = Array.from(responseReceivedIds).filter(id => !requestSentIds.has(id));
    
    if (missingInResponse.length > 0) {
      console.log(`\n⚠️ request_sent中有但response_received中没有的request_id:`);
      missingInResponse.forEach(id => console.log(`  - ${id}`));
    }
    
    if (missingInRequest.length > 0) {
      console.log(`\n⚠️ response_received中有但request_sent中没有的request_id:`);
      missingInRequest.forEach(id => console.log(`  - ${id}`));
    }

    // ========== 分析websocket报文 ==========
    const wsLlmEvents = receivedEvents.filter(e => (e.action?.startsWith('llm.') || e.type?.startsWith('llm.')));
    const wsToolEvents = receivedEvents.filter(e => (e.action?.startsWith('tool.') || e.type?.startsWith('tool.')));
    const wsRequestIds: Set<string> = new Set();
    const wsDialogIds: Set<string> = new Set();
    const wsTextChunks: string[] = [];
    const wsThinkingChunks: string[] = [];
    const wsToolCalls: string[] = [];
    
    console.log('\n[Test] ========== LLM事件详情分析 ==========');
    for (const event of wsLlmEvents) {
      const data = event.data || event;
      const action = event.action || event.type;
      
      if (data?.request_id) {
        wsRequestIds.add(data.request_id);
      }
      if (data?.dialog_id) {
        wsDialogIds.add(data.dialog_id);
      }
      
      // 解析 llm.response_received 事件（包含完整响应）
      if (action === 'llm.response_received') {
        console.log(`  [${action}] request_id=${data.request_id}, dialog_id=${data.dialog_id}`);
        console.log(`    content长度: ${(data.content || '').length}字符`);
        console.log(`    has_tool_calls: ${!!data.tool_calls && data.tool_calls.length > 0}`);
        
        if (data.content && data.content.trim().length > 0) {
          wsTextChunks.push(data.content);
        }
      }
      
      // 解析 llm.response_classified 事件（包含思考内容）
      if (action === 'llm.response_classified') {
        if (data.thinking && data.thinking.trim().length > 0) {
          wsThinkingChunks.push(data.thinking);
        }
      }
    }
    
    // 从 tool.call_started 事件中提取工具调用信息
    console.log('\n[Test] ========== Tool事件详情分析 ==========');
    for (const event of wsToolEvents) {
      const data = event.data || event;
      const action = event.action || event.type;
      
      if (action === 'tool.call_started') {
        console.log(`  [${action}] tool_name=${data.tool_name}, dialog_id=${data.dialog_id}, call_id=${data.call_id}`);
        if (data.tool_name) {
          wsToolCalls.push(data.tool_name);
        }
      }
    }
    console.log(`\n[Test] 从WebSocket解析结果:`);
    console.log(`  文本块数: ${wsTextChunks.length}`);
    console.log(`  思考块数: ${wsThinkingChunks.length}`);
    console.log(`  工具调用数: ${wsToolCalls.length}`);

    // 9. 详细对比并生成表格
    console.log('\n[Test] ========== 对比表 ==========');
    console.log('| 项目 | llm_calls内容（预期） | websocket内容 | 网页内容 | websocket对比状态 | 网页对比状态 |');
    console.log('|------|---------------------|---------------|----------|------------------|--------------|');

    const userMessages = messageDetails.filter(m => m.role === 'user');
    const assistantMessages = messageDetails.filter(m => m.role === 'assistant');

    // 对话数
    console.log(`| 对话数 | ${dialogs.length} | ${wsDialogIds.size} | ${userMessages.length} | ${wsDialogIds.size === dialogs.length ? '✅' : '❌'} | ${userMessages.length === dialogs.length ? '✅' : '❌'} |`);

    // 用户消息数
    console.log(`| 用户消息数 | ${dialogs.length} | ${wsDialogIds.size} | ${userMessages.length} | - | ${userMessages.length === dialogs.length ? '✅' : '❌'} |`);

    // 助手消息数
    console.log(`| 助手消息数 | ${dialogs.length} | ${wsDialogIds.size} | ${assistantMessages.length} | - | - |`);

    // LLM调用数
    const expectedLlmCalls = dialogs.reduce((sum, d) => sum + d.interactions.length, 0);
    console.log(`| LLM调用数 | ${expectedLlmCalls} | ${wsRequestIds.size} | - | - | - |`);

    // 文本回复数
    const expectedTextCount = dialogs.reduce((sum, d) => sum + d.textReplyCount, 0);
    const actualTextCount = assistantMessages.filter(m => m.contentLength > 0).length;
    console.log(`| 文本回复数 | ${expectedTextCount} | ${wsTextChunks.length} | ${actualTextCount} | - | - |`);

    // 思考内容数
    const expectedThinkingCount = dialogs.reduce((sum, d) => {
      return sum + d.interactions.filter(i => i.thinking && i.thinking.trim().length > 0).length;
    }, 0);
    const actualThinkingCount = assistantMessages.filter(m => m.thinkingLength > 0).length;
    console.log(`| 思考内容数 | ${expectedThinkingCount} | ${wsThinkingChunks.length} | ${actualThinkingCount} | - | ${actualThinkingCount === expectedThinkingCount ? '✅' : '❌'} |`);

    // 工具调用数
    const expectedToolCount = dialogs.reduce((sum, d) => sum + d.toolCallCount, 0);
    const actualToolCount = assistantMessages.reduce((sum, m) => sum + m.toolCallCount, 0);
    console.log(`| 工具调用数 | ${expectedToolCount} | ${wsToolCalls.length} | ${actualToolCount} | - | - |`);

    // 工具类型
    const expectedTools = dialogs.flatMap(d => d.toolCalls.map(t => t.name));
    const actualTools = assistantMessages.flatMap(m => m.toolCalls);
    console.log(`| 工具类型 | ${expectedTools.join(',')} | ${wsToolCalls.join(',')} | ${actualTools.join(',')} | - | - |`);

    // 逐个对话详细对比（包含思考和文本内容）
    console.log('\n[Test] ========== 逐个对话详细对比 ==========');
    for (let i = 0; i < dialogs.length; i++) {
      const dialog = dialogs[i];
      const assistantMsg = assistantMessages[i];

      console.log(`\n--- 对话 ${i+1} (${dialog.dialogId}) ---`);
      console.log(`用户输入: ${dialog.userInput.substring(0, 50)}...`);
      
      // 工具调用对比
      const expectedTools = dialog.toolCalls.map((t: any) => t.name);
      const actualTools = assistantMsg?.toolCalls || [];
      console.log(`工具调用: 预期=${expectedTools.length}个(${expectedTools.join(',')}), 实际=${actualTools.length}个(${actualTools.join(',')})`);
      
      // 文本内容对比
      const expectedTexts = dialog.interactions.filter(i => i.text && i.text.trim().length > 0).map(i => i.text);
      const actualContent = assistantMsg?.contentFull || '';
      console.log(`文本回复: 预期${expectedTexts.length}个`);
      expectedTexts.forEach((txt, j) => {
        console.log(`  预期文本${j+1}: ${txt.substring(0, 80)}...`);
      });
      console.log(`  实际文本: ${actualContent.substring(0, 80)}...`);
      
      // 思考内容对比
      const expectedThinkings = dialog.interactions.filter(i => i.thinking && i.thinking.trim().length > 0).map(i => i.thinking);
      const actualThinking = assistantMsg?.thinkingFull || '';
      console.log(`思考内容: 预期${expectedThinkings.length}个`);
      expectedThinkings.forEach((th, j) => {
        console.log(`  预期思考${j+1}: ${th.substring(0, 80)}...`);
      });
      console.log(`  实际思考: ${actualThinking.substring(0, 80)}...${actualThinking.length > 80 ? '' : '(空)'}`);
      
      // 匹配状态
      const isToolMatch = JSON.stringify(expectedTools.sort()) === JSON.stringify(actualTools.sort());
      const hasTextContent = actualContent.length > 0;
      const hasThinking = actualThinking.length > 0;
      console.log(`状态: 工具${isToolMatch ? '✅匹配' : '❌不匹配'}, 文本${hasTextContent ? '✅有内容' : '❌无内容'}, 思考${hasThinking ? '✅有内容' : '❌无内容'}`);
    }

    // 10. 验证断言
    console.log('\n[Test] ========== 验证结果 ==========');
    
    // 验证用户消息数
    expect(userMessages.length).toBe(dialogs.length);
    console.log(`✅ 用户消息数: ${userMessages.length} = ${dialogs.length}`);

    console.log('\n[Test] ✅ 测试完成');
    
    console.log('\n[Test] ========== 按action分组统计 ==========');
    const actionCounts: Map<string, number> = new Map();
    for (const event of receivedEvents) {
      const count = actionCounts.get(event.action) || 0;
      actionCounts.set(event.action, count + 1);
    }
    for (const [action, count] of actionCounts.entries()) {
      console.log(`${action}: ${count}次`);
    }
    
    console.log('\n[Test] ========== LLM相关事件分析 ==========');
    const llmEventsAnalysis = receivedEvents.filter(e => e.action?.startsWith('llm.'));
    console.log(`LLM事件总数: ${llmEventsAnalysis.length}`);
    
    const requestIdsAnalysis: Set<string> = new Set();
    const dialogIdsAnalysis: Set<string> = new Set();
    for (const event of llmEventsAnalysis) {
      if (event.data?.request_id) {
        requestIdsAnalysis.add(event.data.request_id);
      }
      if (event.data?.dialog_id) {
        dialogIdsAnalysis.add(event.data.dialog_id);
      }
    }
    console.log(`唯一request_id数量: ${requestIdsAnalysis.size}`);
    console.log(`唯一dialog_id数量: ${dialogIdsAnalysis.size}`);
    console.log('request_id列表:', Array.from(requestIdsAnalysis));
    console.log('dialog_id列表:', Array.from(dialogIdsAnalysis));

    // ========== WebSocket消息处理追踪 ==========
    console.log('\n[Test] ========== WebSocket消息处理追踪 ==========');
    try {
      const messageProcessing = await page.evaluate(() => {
        if (window.ChatManager && window.ChatManager._messageProcessingRecords) {
          return {
            records: window.ChatManager._messageProcessingRecords,
            stats: window.ChatManager._processingStats
          };
        }
        return null;
      });

      if (messageProcessing) {
        console.log(`📊 消息处理统计:`);
        console.log(`  总处理数: ${messageProcessing.stats.processed}`);
        console.log(`  ✏️  修改组件: ${messageProcessing.stats.modified}`);
        console.log(`  🔗 挂接组件: ${messageProcessing.stats.attached}`);
        console.log(`  🗑️  被抛弃: ${messageProcessing.stats.abandoned}`);
        
        console.log('\n📈 按Action分类统计:');
        for (const [action, count] of Object.entries(messageProcessing.stats.byAction)) {
          console.log(`  ${action}: ${count}次`);
        }
        
        // 详细列出每个消息的处理情况
        console.log('\n📋 消息处理详情列表:');
        messageProcessing.records.forEach((record, index) => {
          const statusColor = record.result === 'abandoned' ? '\x1b[31m' : 
                             record.result === 'modified' ? '\x1b[34m' : 
                             record.result === 'attached' ? '\x1b[32m' : '\x1b[33m';
          console.log(`\n${index + 1}. ${statusColor}${record.result.toUpperCase()}\x1b[0m`);
          console.log(`   MessageID: ${record.messageId}`);
          console.log(`   Action: ${record.action}`);
          console.log(`   Details: ${JSON.stringify(record.details)}`);
        });
        
        // 找出被抛弃的消息
        const abandonedRecords = messageProcessing.records.filter(r => r.result === 'abandoned');
        if (abandonedRecords.length > 0) {
          console.log('\n❌ 被抛弃的消息详情:');
          abandonedRecords.forEach((record, index) => {
            console.log(`\n${index + 1}. MessageID: ${record.messageId}`);
            console.log(`   Action: ${record.action}`);
            console.log(`   Reason: ${record.details?.reason || 'Unknown'}`);
            console.log(`   Details: ${JSON.stringify(record.details)}`);
          });
        }
      } else {
        console.log('ChatManager消息处理记录不可用');
      }
    } catch (error) {
      console.log('消息处理追踪失败:', error);
    }

    // ========== 组件位置验证 ==========
    console.log('\n[Test] ========== 组件位置验证 ==========');
    try {
      const locationValidation = await page.evaluate(() => {
        if (window.ComponentLocationManager) {
          const result = window.ComponentLocationManager.validateAll();
          const tree = window.ComponentLocationManager.getComponentTree();
          return {
            validation: result,
            tree: tree,
            records: window.ComponentLocationManager.getAllRecords()
          };
        }
        return null;
      });

      if (locationValidation) {
        console.log(`组件位置验证结果:`);
        console.log(`  ✅ 有效组件: ${locationValidation.validation.valid.length}`);
        console.log(`  ⚠️ 警告: ${locationValidation.validation.warnings.length}`);
        console.log(`  ❌ 无效: ${locationValidation.validation.invalid.length}`);
        console.log(`  🗑️ 被抛弃: ${locationValidation.validation.abandoned.length}`);
        
        if (locationValidation.validation.warnings.length > 0) {
          console.log('\n警告详情:');
          locationValidation.validation.warnings.forEach(w => {
            console.log(`  - ${w.componentType}(${w.componentId}): ${w.reason}`);
          });
        }
        
        if (locationValidation.validation.invalid.length > 0) {
          console.log('\n无效详情:');
          locationValidation.validation.invalid.forEach(i => {
            console.log(`  - ${i.componentType}(${i.componentId}): ${i.reason}`);
            console.log(`    选择条件: ${JSON.stringify(i.criteria)}`);
          });
        }
        
        if (locationValidation.validation.abandoned.length > 0) {
          console.log('\n被抛弃组件详情:');
          locationValidation.validation.abandoned.forEach(a => {
            console.log(`  - ${a.componentType}(${a.componentId}): ${a.reason}`);
            console.log(`    选择条件: ${JSON.stringify(a.criteria)}`);
          });
        }
        
        console.log('\n组件树结构:');
        console.log(JSON.stringify(locationValidation.tree, null, 2));
      } else {
        console.log('ComponentLocationManager 不可用');
      }
    } catch (error) {
      console.log('组件位置验证失败:', error);
    }

    // ========== 约定事件检查 ==========
    console.log('\n[Test] ========== 约定事件检查 ==========');
    
    // 文档约定的LLM事件类型
    const expectedLlmEvents = [
      'llm.stream_chunk',      // 流式文本片段
      'llm.thinking',          // 思考片段
      'llm.reasoning',         // 推理片段
      'llm.call_text_completed',   // 文本聚合完成
      'llm.call_thinking_completed', // 思考聚合完成
      'llm.call_reasoning_completed', // 推理聚合完成
      'llm.response_received',     // 完整响应
      'llm.call_completed',        // 调用完成
      'llm.request_sent',         // 请求发送
    ];
    
    // 统计实际收到的事件
    const actualEvents: Set<string> = new Set();
    const eventCounts: Map<string, number> = new Map();
    for (const event of receivedEvents) {
      const action = event.action;
      if (action) {
        actualEvents.add(action);
        eventCounts.set(action, (eventCounts.get(action) || 0) + 1);
      }
    }
    
    console.log('📋 文档约定的LLM事件 vs 实际收到的WebSocket事件:');
    console.log('| 约定事件 | 预期? | 实际次数 | 状态 |');
    console.log('|---------|-------|----------|------|');
    
    const missingEvents: string[] = [];
    const presentEvents: string[] = [];
    
    for (const expected of expectedLlmEvents) {
      const count = eventCounts.get(expected) || 0;
      const isPresent = count > 0;
      if (isPresent) {
        presentEvents.push(expected);
      } else {
        missingEvents.push(expected);
      }
      const status = isPresent ? '✅' : '❌ 缺失';
      console.log(`| ${expected} | 是 | ${count} | ${status} |`);
    }
    
    // 统计其他实际收到的事件（不在约定列表中的）
    console.log('\n📋 实际收到的其他事件:');
    const otherEvents: string[] = [];
    for (const action of actualEvents) {
      if (!expectedLlmEvents.includes(action)) {
        const count = eventCounts.get(action) || 0;
        otherEvents.push(action);
        console.log(`  - ${action}: ${count}次`);
      }
    }
    if (otherEvents.length === 0) {
      console.log('  (无其他事件)');
    }
    
    // ========== 对比llm_calls中的LLM调用与websocket事件 ==========
    console.log('\n[Test] ========== LLM调用 vs WebSocket事件详细对比 ==========');
    
    // 使用rawCalls（原始LLM调用数组）
    const llmCallsList = rawCalls || [];
    console.log(`\nllm_calls中共有 ${llmCallsList.length} 个LLM调用`);
    
    // 建立llm_calls中的response与websocket事件的映射
    for (let i = 0; i < llmCallsList.length; i++) {
      const call = llmCallsList[i];
      const resp = call.response || {};
      
      console.log(`\n--- LLM调用 ${i + 1} ---`);
      console.log(`  call_id: ${call.call_id}`);
      console.log(`  dialog_id: ${call.dialog_id}`);
      
      // llm_calls中的数据
      const hasContent = resp.content && resp.content.trim().length > 0;
      const hasThinking = resp.thinking && resp.thinking.trim().length > 0;
      const hasToolCalls = resp.tool_calls && resp.tool_calls.length > 0;
      const contentPreview = (resp.content || '').substring(0, 50).replace(/\n/g, ' ');
      
      console.log(`  llm_calls数据:`);
      console.log(`    - content长度: ${(resp.content || '').length}`);
      console.log(`    - content预览: ${contentPreview}...`);
      console.log(`    - thinking长度: ${(resp.thinking || '').length}`);
      console.log(`    - tool_calls数: ${resp.tool_calls?.length || 0}`);
      
      // 通过content内容在websocket事件中查找匹配
      const matchedEvents: any[] = [];
      let bestMatch: {event: any, matchLen: number} | null = null;
      
      for (const event of receivedEvents) {
        const data = event.data || event;
        // llm.response_received包含content字段
        if (data.content) {
          const matchLen = findCommonPrefixLength(data.content, resp.content || '');
          if (matchLen > 10 && (!bestMatch || matchLen > bestMatch.matchLen)) {
            bestMatch = {event, matchLen};
          }
        }
      }
      
      if (bestMatch) {
        console.log(`  WebSocket事件 (通过content匹配):`);
        console.log(`    - 匹配事件: ${bestMatch.event.action}`);
        console.log(`    - 匹配长度: ${bestMatch.matchLen}字符`);
        console.log(`    - dialog_id: ${bestMatch.event.data?.dialog_id}`);
        
        // 检查该事件附近的约定事件
        const eventIdx = receivedEvents.indexOf(bestMatch.event);
        const nearbyEvents = receivedEvents.slice(Math.max(0, eventIdx - 5), eventIdx + 5);
        const nearbyLlmEvents = nearbyEvents.filter(e => e.action?.startsWith('llm.') || e.action?.startsWith('tool.'));
        
        console.log(`    - 附近LLM事件 (前后5个):`);
        for (const ne of nearbyLlmEvents) {
          console.log(`      * ${ne.action} (dialog_id=${ne.data?.dialog_id?.substring(0, 8)}...)`);
        }
        
        // 检查是否有约定事件
        const hasStreamChunk = receivedEvents.some(e => {
          const idx = receivedEvents.indexOf(e);
          return Math.abs(idx - eventIdx) < 10 && e.action === 'llm.stream_chunk';
        });
        const hasThinking = receivedEvents.some(e => {
          const idx = receivedEvents.indexOf(e);
          return Math.abs(idx - eventIdx) < 10 && e.action === 'llm.thinking';
        });
        const hasReasoning = receivedEvents.some(e => {
          const idx = receivedEvents.indexOf(e);
          return Math.abs(idx - eventIdx) < 10 && e.action === 'llm.reasoning';
        });
        
        if (hasStreamChunk || hasThinking || hasReasoning) {
          console.log(`  ✅ 找到约定事件`);
        } else {
          console.log(`  ❌ 缺失约定事件 (llm.stream_chunk/llm.thinking/llm.reasoning)`);
        }
      } else {
        console.log(`  WebSocket事件: ❌ 未找到匹配的事件`);
        
        // 分析缺失原因
        const missingForCall: string[] = [];
        if (hasContent) {
          missingForCall.push('❌ 有content但无匹配的llm.response_received');
        }
        if (hasThinking) {
          missingForCall.push('❌ 有thinking但无llm.thinking事件');
        }
        
        if (missingForCall.length > 0) {
          console.log(`  ⚠️ 问题分析:`);
          missingForCall.forEach(m => console.log(`    ${m}`));
        }
      }
    }
    
    // 总结
    console.log('\n[Test] ========== 约定事件检查总结 ==========');
    console.log(`约定事件总数: ${expectedLlmEvents.length}`);
    console.log(`实际收到的事件数: ${presentEvents.length}`);
    console.log(`缺失的事件数: ${missingEvents.length}`);
    
    if (missingEvents.length > 0) {
      console.log('\n❌ 缺失的约定事件:');
      missingEvents.forEach(e => console.log(`  - ${e}`));
    }
    
    // 分析llm_calls中thinking为空的原因
    const callsWithThinking = llmCallsList.filter(c => c.response?.thinking && c.response.thinking.trim().length > 0);
    const callsWithoutThinking = llmCallsList.filter(c => !c.response?.thinking || c.response.thinking.trim().length === 0);
    console.log(`\nllm_calls数据统计:`);
    console.log(`  - 有thinking的LLM调用: ${callsWithThinking.length}`);
    console.log(`  - 无thinking的LLM调用: ${callsWithoutThinking.length}`);
    
    if (callsWithThinking.length === 0 && callsWithoutThinking.length > 0) {
      console.log('\n⚠️ 分析: llm_calls中的thinking字段全部为空');
      console.log('   可能原因:');
      console.log('   1. LLM执行服务未正确提取thinking内容');
      console.log('   2. LLM响应中本身没有thinking字段');
      console.log('   3. 后台代码未按约定发布llm.thinking事件');
    }
    
    // ========== 切换Session测试 ==========
    console.log('\n[Test] ========== 切换Session测试 ==========');
    
    // 获取当前会话列表
    const sessionList = page.locator('.session-item');
    await sessionList.first().waitFor();
    const sessionCount = await sessionList.count();
    console.log(`[Test] 当前会话数量: ${sessionCount}`);
    
    if (sessionCount >= 2) {
      // ========== 验证历史消息回放 ==========
      // 在创建第二个会话后，切换回第一个会话，验证历史消息是否正确回放
      console.log('\n[Test] ========== 验证历史消息回放 ==========');
      
      // 记录切换前的状态
      const eventsBeforeReplay = await page.evaluate(() => {
        return (window as any).eventCapture?.getAllEvents()?.length || 0;
      });
      console.log(`[Test] 切换前WebSocket事件数: ${eventsBeforeReplay}`);
      
      // 切换回第一个会话（应该触发历史消息回放）
      console.log('\n[Test] --- 切换回第一个会话（验证历史消息回放）---');
      await sessionList.nth(0).click();
      await page.waitForTimeout(5000); // 等待历史消息回放完成
      
      // 记录切换后的状态
      const eventsAfterReplay = await page.evaluate(() => {
        return (window as any).eventCapture?.getAllEvents()?.length || 0;
      });
      console.log(`[Test] 切换后WebSocket事件数: ${eventsAfterReplay}`);
      
      // 检查是否有新的历史消息被推送
      const newEventsCount = eventsAfterReplay - eventsBeforeReplay;
      console.log(`[Test] 新推送的事件数: ${newEventsCount}`);
      
      // 验证历史消息是否正确显示
      const historyMessages = page.locator('.message-item');
      const historyMessageCount = await historyMessages.count();
      console.log(`[Test] 回放后消息数: ${historyMessageCount}`);
      
      // 检查是否有历史消息被回放
      if (newEventsCount > 0) {
        console.log(`[Test] ✅ 历史消息回放成功！推送了 ${newEventsCount} 个事件`);
      } else {
        console.log('[Test] ⚠️ 警告: 没有新事件被推送，可能历史消息回放有问题');
      }
      
      // 获取第一个会话的名称
      const firstSessionName = await sessionList.nth(0).textContent();
      console.log(`[Test] 当前会话: ${firstSessionName}`);
      
      // 记录切换前的消息数（用于后续验证）
      const messagesBeforeSwitch = page.locator('.message-item');
      const messageCountBefore = await messagesBeforeSwitch.count();
      console.log(`[Test] 切换前消息数: ${messageCountBefore}`);
      
      // 第一次切换：切换到第二个会话
      console.log('\n[Test] --- 第1次切换：会话1 -> 会话2 ---');
      await sessionList.nth(1).click();
      await page.waitForTimeout(3000);
      const secondSessionName = await sessionList.nth(1).textContent();
      console.log(`[Test] 已切换到会话: ${secondSessionName}`);
      
      // 验证第二个会话的消息列表
      const secondSessionMessages = page.locator('.message-item');
      const secondMessageCount = await secondSessionMessages.count();
      console.log(`[Test] 第二个会话消息数: ${secondMessageCount}`);
      
      // 第二次切换：切换回第一个会话
      console.log('\n[Test] --- 第2次切换：会话2 -> 会话1 ---');
      await sessionList.nth(0).click();
      await page.waitForTimeout(3000);
      console.log(`[Test] 已切换回会话: ${firstSessionName}`);
      
      // 验证第一个会话的消息列表是否与切换前一致
      const firstSessionMessages = page.locator('.message-item');
      const firstMessageCount = await firstSessionMessages.count();
      console.log(`[Test] 切换回第一个会话后的消息数: ${firstMessageCount}`);
      
      // 第三次切换：再次切换到第二个会话
      console.log('\n[Test] --- 第3次切换：会话1 -> 会话2 ---');
      await sessionList.nth(1).click();
      await page.waitForTimeout(3000);
      console.log(`[Test] 再次切换到会话: ${secondSessionName}`);
      
      const secondMessageCountAfter = await secondSessionMessages.count();
      console.log(`[Test] 第二个会话消息数（第二次访问）: ${secondMessageCountAfter}`);
      
      // 第四次切换：再次切换回第一个会话
      console.log('\n[Test] --- 第4次切换：会话2 -> 会话1 ---');
      await sessionList.nth(0).click();
      await page.waitForTimeout(3000);
      console.log(`[Test] 再次切换回会话: ${firstSessionName}`);
      
      // 最终验证：消息数是否与切换前一致
      const finalMessageCount = await firstSessionMessages.count();
      console.log(`[Test] 最终消息数: ${finalMessageCount} (切换前: ${messageCountBefore})`);
      
      // 验证消息内容是否完整
      const messageContents = await firstSessionMessages.allTextContents();
      console.log(`[Test] 消息内容检查: ${messageContents.length} 条消息`);
      
      // 验证事件捕获系统是否正常工作
      const wsEventsAfterSwitch = await page.evaluate(() => {
        return (window as any).eventCapture?.getAllEvents() || [];
      });
      console.log(`[Test] 切换会话后捕获的WebSocket事件数: ${wsEventsAfterSwitch.length}`);
      
      // 检查会话切换后消息是否正确恢复
      if (finalMessageCount === 0) {
        console.log('[Test] ❌ 错误: 多次切换会话后消息丢失！');
      } else if (finalMessageCount !== messageCountBefore) {
        console.log(`[Test] ⚠️ 警告: 消息数不一致，切换前: ${messageCountBefore}, 切换后: ${finalMessageCount}`);
      } else {
        console.log('[Test] ✅ 多次Session切换测试完成，消息数保持一致');
      }
    } else {
      console.log('[Test] ⚠️ 会话数量不足，跳过Session切换测试');
    }
    
    console.log('\n[Test] ✅ 测试完成');
  });

  // 测试完成后备份测试数据
  test.afterAll(() => {
    console.log('\n[Test] ======== 备份测试数据 ========');
    
    const testDataDir = path.join('d:', 'learnning', '260521', 'src', 'data', 'test');
    const testBakDir = path.join('d:', 'learnning', '260521', 'src', 'data', 'test_bak');
    
    // 创建备份目录（如果不存在）
    if (!fs.existsSync(testBakDir)) {
      fs.mkdirSync(testBakDir, { recursive: true });
      console.log(`[Test] 创建备份目录: ${testBakDir}`);
    }
    
    // 复制所有JSON文件（覆盖式复制）
    if (fs.existsSync(testDataDir)) {
      const files = fs.readdirSync(testDataDir);
      let copiedCount = 0;
      for (const file of files) {
        if (file.endsWith('.json')) {
          const srcPath = path.join(testDataDir, file);
          const destPath = path.join(testBakDir, file);
          fs.copyFileSync(srcPath, destPath);
          copiedCount++;
          console.log(`[Test] 备份: ${file}`);
        }
      }
      console.log(`[Test] 已备份 ${copiedCount} 个文件`);
    } else {
      console.log(`[Test] ⚠️ 警告: 测试数据目录不存在 - ${testDataDir}`);
    }
    
    console.log('[Test] ======== 测试数据备份完成 ========');
  });
});
