import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

test.describe('LLM异常处理测试 - 验证错误信息显示', () => {
  // 测试前清理环境
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

    console.log('[Test] ======== 环境清理完成 ========');
  });

  test('验证LLM调用失败时助手显示错误信息', async ({ page }) => {
    // 设置测试超时时间为 2 分钟
    test.setTimeout(120000);
    
    console.log('[Test] ========== 开始LLM异常处理测试 ==========');

    // ========== 1. 注入事件捕获系统 ==========
    await page.addInitScript(() => {
      // 事件捕获系统
      (window as any).eventCapture = {
        events: [],
        handlers: new Map(),
        initialized: false,
        
        on(eventType: string, handler: (data: any) => void) {
          if (!this.handlers.has(eventType)) {
            this.handlers.set(eventType, []);
          }
          this.handlers.get(eventType).push(handler);
        },
        
        emit(eventType: string, data: any) {
          this.events.push({ 
            type: eventType, 
            timestamp: Date.now(), 
            data: JSON.parse(JSON.stringify(data))
          });
          
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
        
        getAllEvents() {
          return [...this.events];
        },
        
        getEventsByType(eventType: string) {
          return this.events.filter(e => e.type === eventType);
        },
        
        clear() {
          this.events = [];
        },
        
        initWsCapture() {
          if (this.initialized) return;
          if (!window.EventBus || !window.EventBus.on) {
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
    });

    // ========== 2. 打开页面 ==========
    await page.goto('http://localhost:8000/');
    await page.waitForLoadState('networkidle');
    
    // 初始化事件捕获
    await page.waitForFunction('window.eventCapture !== undefined', { timeout: 10000 });
    await page.evaluate(() => {
      window.eventCapture.initWsCapture();
    });
    
    await page.waitForTimeout(2000);

    // ========== 3. 确保处于录制模式 ==========
    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();

    let currentModeText = await toggle.textContent();
    console.log('[Test] 当前模式:', currentModeText);

    // 如果是回放模式，切换到录制模式
    const isReplayMode = currentModeText.includes('回放') || currentModeText.includes('🔄');
    if (isReplayMode) {
      await toggle.click();
      await page.waitForTimeout(3000);
      console.log('[Test] 已从回放模式切换到录制模式');
    }

    // ========== 4. 选择第一个项目 ==========
    console.log('[Test] 选择第一个项目...');
    const projectSelect = page.locator('.project-select');
    await projectSelect.waitFor();
    await page.waitForTimeout(2000);

    const projectOptions = await projectSelect.locator('option').all();
    if (projectOptions.length > 1) {
      await projectSelect.selectOption({ index: 1 });
      console.log('[Test] 已选择第一个项目');
    }
    await page.waitForTimeout(1500);

    // ========== 5. 创建新 session ==========
    console.log('[Test] 创建新会话...');
    const newBtn = page.locator('button:has-text("+ 新建")');
    await newBtn.waitFor({ timeout: 5000 });
    await newBtn.click();
    await page.waitForTimeout(3000);
    console.log('[Test] 会话创建完成');

    // ========== 6. 发送消息触发LLM调用 ==========
    console.log('[Test] 发送消息触发LLM调用...');
    
    const textarea = page.locator('textarea').first();
    await textarea.waitFor({ timeout: 5000 });

    await textarea.fill('xxx');
    await textarea.press('Enter');
    console.log('[Test] 已发送消息: xxx');
    
    // 等待一段时间让LLM调用完成（包括可能的失败）
    await page.waitForTimeout(15000);

    // ========== 7. 检查是否收到LLM相关事件 ==========
    const capturedEvents = await page.evaluate(() => {
      return (window as any).eventCapture?.getAllEvents() || [];
    });
    
    console.log(`[Test] 捕获到 ${capturedEvents.length} 个事件`);
    
    // 查找关键事件
    const callFailedEvents = capturedEvents.filter((e: any) => e.type === 'llm.call_failed');
    const responseClassifiedEvents = capturedEvents.filter((e: any) => e.type === 'llm.response_classified');
    const dialogCompletedEvents = capturedEvents.filter((e: any) => e.type === 'dialog.completed');
    
    console.log(`[Test] llm.call_failed 事件数: ${callFailedEvents.length}`);
    console.log(`[Test] llm.response_classified 事件数: ${responseClassifiedEvents.length}`);
    console.log(`[Test] dialog.completed 事件数: ${dialogCompletedEvents.length}`);

    // 打印 response_classified 事件的详细信息
    if (responseClassifiedEvents.length > 0) {
      console.log('[Test] response_classified 事件详情:');
      responseClassifiedEvents.forEach((event: any, index: number) => {
        const data = event.data?.data || event.data;
        console.log(`  事件 ${index + 1}:`);
        console.log(`    finish_reason: ${data?.finish_reason}`);
        console.log(`    success: ${data?.success}`);
        console.log(`    content: ${data?.content?.substring(0, 100)}...`);
      });
    }

    // ========== 8. 检查页面上的消息显示 ==========
    console.log('[Test] 检查页面消息显示...');
    
    const messageDetails = await page.evaluate(() => {
      const items: any[] = [];
      document.querySelectorAll('.message-item').forEach((item) => {
        const isUser = item.classList.contains('user-message');
        const isAssistant = item.classList.contains('assistant-message');

        if (!isUser && !isAssistant) return;

        const role = isUser ? 'user' : 'assistant';
        const contentEl = item.querySelector('.message-content, .message-text');
        const content = contentEl?.textContent?.trim() || '';
        
        // 检查是否是错误消息
        const isError = item.classList.contains('error-message') || 
                       content.includes('Error:') || 
                       content.includes('失败') ||
                       content.includes('错误');

        items.push({
          role,
          content,
          contentLength: content.length,
          isError,
          elementHTML: item.outerHTML.substring(0, 500)
        });
      });
      return items;
    });

    console.log(`[Test] 页面上共有 ${messageDetails.length} 条消息`);
    
    messageDetails.forEach((msg: any, index: number) => {
      console.log(`\n--- 消息 ${index + 1} ---`);
      console.log(`角色: ${msg.role}`);
      console.log(`内容: ${msg.content.substring(0, 200)}...`);
      console.log(`是否错误: ${msg.isError}`);
    });

    // ========== 9. 验证测试结果 ==========
    console.log('[Test] ========== 验证测试结果 ==========');
    
    // 验证1：应该至少有2条消息（用户消息 + 助手回复）
    expect(messageDetails.length).toBeGreaterThanOrEqual(2);
    console.log('[Test] ✓ 验证1通过: 消息数量 >= 2');
    
    // 验证2：第一条应该是用户消息
    const userMessage = messageDetails.find((m: any) => m.role === 'user');
    expect(userMessage).toBeDefined();
    expect(userMessage.content).toContain('xxx');
    console.log('[Test] ✓ 验证2通过: 找到用户消息');
    
    // 验证3：应该有一条助手消息
    const assistantMessages = messageDetails.filter((m: any) => m.role === 'assistant');
    expect(assistantMessages.length).toBeGreaterThanOrEqual(1);
    console.log(`[Test] ✓ 验证3通过: 找到 ${assistantMessages.length} 条助手消息`);
    
    // 验证4：如果LLM调用失败，助手消息应该包含错误信息
    if (callFailedEvents.length > 0 || 
        responseClassifiedEvents.some((e: any) => {
          const data = e.data?.data || e.data;
          return data?.finish_reason === 'error';
        })) {
      console.log('[Test] 检测到LLM调用失败事件，检查错误信息显示...');
      
      // 检查助手消息是否包含错误相关内容
      const hasErrorContent = assistantMessages.some((msg: any) => {
        return msg.isError || 
               msg.content.includes('Error') || 
               msg.content.includes('失败') ||
               msg.content.includes('无法连接') ||
               msg.content.includes('错误');
      });
      
      expect(hasErrorContent).toBe(true);
      console.log('[Test] ✓ 验证4通过: 助手消息显示错误信息');
    } else {
      console.log('[Test] 未检测到LLM调用失败，假设调用成功');
      // 如果没有失败事件，检查助手消息是否有正常内容
      const hasContent = assistantMessages.some((msg: any) => msg.contentLength > 0);
      expect(hasContent).toBe(true);
      console.log('[Test] ✓ 验证4通过: 助手消息有内容');
    }

    // 验证5：检查输入框状态是否已重置（isGenerating = false）
    const isTextareaDisabled = await textarea.isDisabled();
    expect(isTextareaDisabled).toBe(false);
    console.log('[Test] ✓ 验证5通过: 输入框已启用（isGenerating = false）');

    // ========== 10. 会话切换测试 ==========
    console.log('[Test] ========== 会话切换测试 ==========');
    
    // 记录第一个会话的消息详情
    const firstSessionMessages = [...messageDetails];
    console.log(`[Test] 第一个会话消息数: ${firstSessionMessages.length}`);
    
    // 创建第二个会话
    const newSessionBtn = page.locator('.btn.btn-sm.btn-outline');
    await newSessionBtn.waitFor();
    await newSessionBtn.click();
    await page.waitForTimeout(3000);
    console.log('[Test] 已创建第二个会话');
    
    // 在第二个会话发送消息
    await textarea.fill('test message');
    await textarea.press('Enter');
    await page.waitForTimeout(10000);
    console.log('[Test] 已在第二个会话发送消息');
    
    // 切换回第一个会话
    const firstSessionItem = page.locator('.session-item').first();
    await firstSessionItem.waitFor();
    await firstSessionItem.click();
    await page.waitForTimeout(3000);
    console.log('[Test] 已切换回第一个会话');
    
    // 检查切换后的消息显示
    const messagesAfterSwitch = await page.evaluate(() => {
      const items: any[] = [];
      document.querySelectorAll('.message-item').forEach((item) => {
        const isUser = item.classList.contains('user-message');
        const isAssistant = item.classList.contains('assistant-message');

        if (!isUser && !isAssistant) return;

        const role = isUser ? 'user' : 'assistant';
        const contentEl = item.querySelector('.message-content, .message-text');
        const content = contentEl?.textContent?.trim() || '';

        items.push({
          role,
          content,
          contentLength: content.length
        });
      });
      return items;
    });
    
    console.log(`[Test] 切换回第一个会话后消息数: ${messagesAfterSwitch.length}`);
    
    // 验证6：切换后消息数量应该与切换前一致
    expect(messagesAfterSwitch.length).toBe(firstSessionMessages.length);
    console.log('[Test] ✓ 验证6通过: 切换后消息数量正确');
    
    // 验证7：检查用户消息是否存在
    const userMsgAfterSwitch = messagesAfterSwitch.find((m: any) => m.role === 'user');
    expect(userMsgAfterSwitch).toBeDefined();
    expect(userMsgAfterSwitch.content).toContain('xxx');
    console.log('[Test] ✓ 验证7通过: 用户消息正确显示');
    
    // 验证8：检查助手消息是否存在
    const assistantMsgAfterSwitch = messagesAfterSwitch.find((m: any) => m.role === 'assistant');
    expect(assistantMsgAfterSwitch).toBeDefined();
    expect(assistantMsgAfterSwitch.contentLength).toBeGreaterThan(0);
    console.log('[Test] ✓ 验证8通过: 助手消息正确显示');

    console.log('[Test] ========== 所有测试通过 ==========');
  });
});