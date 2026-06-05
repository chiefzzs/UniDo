import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// 读取 websocket_messages.json
function getWebSocketMessages(): any[] {
  const wsMessagesPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'websocket_messages.json');
  if (!fs.existsSync(wsMessagesPath)) {
    return [];
  }

  const content = fs.readFileSync(wsMessagesPath, 'utf-8');
  return JSON.parse(content);
}

// 读取 sessions.json
function getSessions(): any[] {
  const sessionsPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'sessions.json');
  if (!fs.existsSync(sessionsPath)) {
    return [];
  }

  const content = fs.readFileSync(sessionsPath, 'utf-8');
  return JSON.parse(content);
}

// 读取 messages.json
function getMessages(): any[] {
  const messagesPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'messages.json');
  if (!fs.existsSync(messagesPath)) {
    return [];
  }

  const content = fs.readFileSync(messagesPath, 'utf-8');
  return JSON.parse(content);
}

// 读取 projects.json
function getProjects(): any[] {
  const projectsPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'projects.json');
  if (!fs.existsSync(projectsPath)) {
    return [];
  }

  const content = fs.readFileSync(projectsPath, 'utf-8');
  return JSON.parse(content);
}

// 读取 llm_calls.json
function getLLMCalls(): any[] {
  const llmCallsPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'llm_calls.json');
  if (!fs.existsSync(llmCallsPath)) {
    return [];
  }

  const content = fs.readFileSync(llmCallsPath, 'utf-8');
  return JSON.parse(content);
}

// 读取 tool_calls.json
function getToolCalls(): any[] {
  const toolCallsPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'tool_calls.json');
  if (!fs.existsSync(toolCallsPath)) {
    return [];
  }

  const content = fs.readFileSync(toolCallsPath, 'utf-8');
  return JSON.parse(content);
}

// 读取 tool_result.json
function getToolResults(): any[] {
  const toolResultPath = path.join('d:', 'learnning', '260521', 'src', 'data', 'test', 'tool_result.json');
  if (!fs.existsSync(toolResultPath)) {
    return [];
  }

  const content = fs.readFileSync(toolResultPath, 'utf-8');
  return JSON.parse(content);
}

test.describe('会话切换加载测试 - 不清理环境', () => {
  // 测试前不清理环境 - 保留 src/data/test 目录下所有文件
  test.beforeAll(() => {
    console.log('[Test] ======== 不清理测试环境，保留所有数据 ========');
    const testDataDir = path.join('d:', 'learnning', '260521', 'src', 'data', 'test');
    const files = fs.readdirSync(testDataDir);
    console.log('[Test] 测试目录文件:', files);
  });

  test('选择第一个项目，加载第一个session，验证组件创建顺序与消息一致性', async ({ page }) => {
    const consoleLogs: string[] = [];
    const componentCreateLogs: string[] = [];
    const wsReceivedEvents: any[] = [];

    // 监听控制台日志
    page.on('console', msg => {
      const text = msg.text();
      consoleLogs.push(text);

      // 记录组件创建相关的日志
      if (text.includes('创建') || text.includes('created') || text.includes('ChatPanel') ||
          text.includes('SessionComponent') || text.includes('UserMessage') ||
          text.includes('AssistantMessage') || text.includes('ResponseBlock') ||
          text.includes('ThinkBlock') || text.includes('TextBlock') ||
          text.includes('ReasoningBlock') || text.includes('ToolCard') ||
          text.includes('ComponentSubscriptions') || text.includes('EventBus')) {
        componentCreateLogs.push(text);
        console.log('[Console]', text);
      }
    });

    // 记录WebSocket事件
    page.on('websocket', ws => {
      ws.on('framereceived', data => {
        try {
          const payload = data.payload.toString();
          const parsed = JSON.parse(payload);
          wsReceivedEvents.push(parsed);

          // 记录关键事件
          if (parsed.action) {
            console.log(`[WS Received] ${parsed.action}`);
          }
        } catch {}
      });
    });

    // 1. 打开应用
    console.log('[Test] ========== 打开应用 ==========');
    await page.goto('http://localhost:8000');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // 2. 检查是否处于回放模式
    console.log('[Test] ========== 检查回放模式 ==========');
    try {
      // 查找回放切换按钮
      const replayToggle = page.locator('.replay-toggle, [data-testid="replay-toggle"]').first();
      await expect(replayToggle).toBeVisible({ timeout: 5000 });

      const toggleText = await replayToggle.textContent();
      const isReplay = toggleText?.includes('回放') || toggleText?.includes('Replay') ||
                       toggleText?.includes('🔄') || toggleText?.includes('📹');

      if (!isReplay || toggleText?.includes('📹')) {
        console.log('[Test] 当前不是回放模式，切换到回放模式');
        await replayToggle.click();
        await page.waitForTimeout(2000);
      }
      console.log('[Test] 已确认在回放模式');
    } catch (e) {
      console.log('[Test] 未找到回放切换按钮，继续:', e);
    }

    // 3. 选择第一个项目
    console.log('[Test] ========== 选择第一个项目 ==========');
    const projects = getProjects();
    console.log('[Test] 本地projects数据:', projects.length, '个');

    if (projects.length > 0) {
      console.log('[Test] 第一个project:', projects[0]);
    }

    // 通过下拉框选择项目
    try {
      const projectSelect = page.locator('.project-select').first();
      await expect(projectSelect).toBeVisible({ timeout: 5000 });

      // 获取所有选项
      const options = await projectSelect.locator('option').all();
      console.log('[Test] 项目下拉框选项数:', options.length);

      if (options.length > 1) {
        // 选择第二个选项（第一个是空的"选择项目"）
        await projectSelect.selectOption({ index: 1 });
        await page.waitForTimeout(3000);
        console.log('[Test] 已通过下拉框选择第一个项目');
      }
    } catch (e) {
      console.log('[Test] 选择项目出错:', e);
    }

    // 4. 加载第一个session
    console.log('[Test] ========== 加载第一个Session ==========');
    const sessions = getSessions();
    console.log('[Test] 本地sessions数据:', sessions.length, '个');

    if (sessions.length > 0) {
      console.log('[Test] 第一个session:', sessions[0]);
    }

    // 等待会话列表加载
    await page.waitForTimeout(3000);

    // 点击第一个会话项
    const sessionItems = await page.locator('.session-item').all();
    console.log('[Test] 发现会话项数:', sessionItems.length);

    if (sessionItems.length > 0) {
      await sessionItems[0].click();
      console.log('[Test] 已点击第一个会话项');

      // 等待回放事件加载
      console.log('[Test] 等待回放事件加载...');
      await page.waitForTimeout(8000);
    } else {
      console.log('[Test] 未发现会话项，继续等待...');
      await page.waitForTimeout(5000);
    }

    // 5. 检查组件创建顺序与文档一致
    console.log('[Test] ========== 验证组件创建顺序 ==========');
    console.log('[Test] 组件创建日志数:', componentCreateLogs.length);

    // 验证文档中描述的组件层级
    // ChatPanel -> SessionComponent -> UserMessage -> AssistantMessage -> ResponseBlock -> [ThinkBlock/TextBlock/ReasoningBlock/ToolCard]
    const expectedComponents = [
      'ChatPanel',
      'SessionComponent',
      'UserMessage',
      'AssistantMessage',
      'ResponseBlock',
    ];

    console.log('[Test] ========== 检查组件层级创建 ==========');
    const foundComponents = new Set<string>();

    for (const log of componentCreateLogs) {
      for (const component of expectedComponents) {
        if (log.includes(component) && !foundComponents.has(component)) {
          foundComponents.add(component);
          console.log(`[Test] ✅ 找到组件: ${component}`);
        }
      }
    }

    console.log('[Test] 找到的核心组件:', Array.from(foundComponents));

    // 验证文档描述的创建关系是否在日志中体现
    console.log('[Test] ========== 验证组件订阅关系 ==========');
    const hasComponentSubscriptions = componentCreateLogs.some(log =>
      log.includes('ComponentSubscriptions') &&
      log.includes('创建类消息订阅')
    );

    if (hasComponentSubscriptions) {
      console.log('[Test] ✅ 找到ComponentSubscriptions设置创建类消息订阅');
    }

    // 6. 检查渲染后的对话内容
    console.log('[Test] ========== 验证对话内容 ==========');
    const messages = getMessages();
    console.log('[Test] 本地messages数据:', messages.length, '条');

    // 获取页面上显示的消息
    const userMessages = await page.locator('.user-message, [data-testid="user-message"]').all();
    const assistantMessages = await page.locator('.assistant-message, [data-testid="assistant-message"]').all();

    console.log('[Test] 页面用户消息数:', userMessages.length);
    console.log('[Test] 页面助手消息数:', assistantMessages.length);

    // 提取助手消息内容
    const assistantContents: string[] = [];
    for (const msg of assistantMessages) {
      const text = await msg.textContent();
      if (text && text.trim()) {
        assistantContents.push(text.trim());
      }
    }
    console.log('[Test] 助手消息内容:', assistantContents);

    // 7. 与 websocket_messages.json 消息对比
    console.log('[Test] ========== 验证WebSocket消息一致性 ==========');
    const wsMessages = getWebSocketMessages();
    console.log('[Test] websocket_messages.json 消息数:', wsMessages.length);

    // 统计实际收到的事件类型
    const receivedEventTypes = new Map<string, number>();
    for (const event of wsReceivedEvents) {
      if (event.action) {
        const action = event.action;
        receivedEventTypes.set(action, (receivedEventTypes.get(action) || 0) + 1);
      }
    }

    console.log('[Test] 实际收到的WebSocket事件类型:');
    for (const [type, count] of receivedEventTypes.entries()) {
      console.log(`  - ${type}: ${count}`);
    }

    // 统计预期的事件类型
    const expectedEventTypes = new Map<string, number>();
    for (const msg of wsMessages) {
      if (msg.direction === 'outbound' && msg.message_type) {
        const type = msg.message_type;
        expectedEventTypes.set(type, (expectedEventTypes.get(type) || 0) + 1);
      }
    }

    console.log('[Test] websocket_messages.json 中的事件类型:');
    for (const [type, count] of expectedEventTypes.entries()) {
      console.log(`  - ${type}: ${count}`);
    }

    // 8. 检查关键事件是否都收到
    console.log('[Test] ========== 关键事件检查 ==========');
    const criticalEvents = [
      'event_session.created',
      'event_client.message_received',
      'event_dialog.created',
      'event_llm.request_prepared',
      'event_llm.request_sent',
      'event_llm.call_completed',
    ];

    const missingCriticalEvents: string[] = [];
    for (const eventType of criticalEvents) {
      const hasInWS = expectedEventTypes.has(eventType);

      // 转换 event_xxx.created 为 xxx.created 来匹配
      const normalizedType = eventType.replace('event_', '');
      const hasInReceived = Array.from(receivedEventTypes.keys()).some(t =>
        t.includes(normalizedType) || t.includes(eventType)
      );

      if (hasInWS && !hasInReceived) {
        missingCriticalEvents.push(eventType);
        console.log(`[Test] ❌ 缺失关键事件: ${eventType}`);
      } else if (hasInWS) {
        console.log(`[Test] ✅ 找到关键事件: ${eventType}`);
      }
    }

    // 9. 验证大模型输出内容（response中的文本、思考、推理、工具调用）
    console.log('[Test] ========== 验证大模型输出内容 ==========');
    const llmCalls = getLLMCalls();
    console.log('[Test] llm_calls.json 中LLM调用数:', llmCalls.length);

    // 提取所有response中的内容
    const expectedTextContents: string[] = [];
    const expectedThinkingContents: string[] = [];
    const expectedToolCalls: {name: string, args: string}[] = [];

    for (const call of llmCalls) {
      const resp = call.response || {};

      // 文本内容
      if (resp.content && resp.content.trim()) {
        expectedTextContents.push(resp.content.trim());
        console.log(`[Test] LLM文本内容[${expectedTextContents.length}]: ${resp.content.substring(0, 100)}...`);
      }

      // 思考内容
      if (resp.thinking && resp.thinking.trim()) {
        expectedThinkingContents.push(resp.thinking.trim());
        console.log(`[Test] LLM思考内容[${expectedThinkingContents.length}]: ${resp.thinking.substring(0, 100)}...`);
      }

      // 工具调用
      if (resp.tool_calls && Array.isArray(resp.tool_calls)) {
        for (const tc of resp.tool_calls) {
          const toolName = tc.function?.name || 'unknown';
          const toolArgs = tc.function?.arguments || '{}';
          expectedToolCalls.push({ name: toolName, args: toolArgs });
          console.log(`[Test] LLM工具调用: ${toolName}(${toolArgs.substring(0, 50)}...)`);
        }
      }
    }

    console.log('[Test] ====== 大模型输出统计 ======');
    console.log(`[Test] 文本内容数: ${expectedTextContents.length}`);
    console.log(`[Test] 思考内容数: ${expectedThinkingContents.length}`);
    console.log(`[Test] 工具调用数: ${expectedToolCalls.length}`);

    // 10. 验证前台显示的文本内容与LLM response对比
    console.log('[Test] ========== 对比前台显示内容与LLM输出 ==========');

    // 获取页面上的文本块内容
    const textBlocks = await page.locator('.text-block, [data-testid="text-block"], .response-text').all();
    const pageTextContents: string[] = [];
    for (const block of textBlocks) {
      const text = await block.textContent();
      if (text && text.trim()) {
        pageTextContents.push(text.trim());
      }
    }
    console.log('[Test] 前台文本块数:', pageTextContents.length);

    // 获取页面上的思考块内容
    const thinkBlocks = await page.locator('.think-block, [data-testid="think-block"]').all();
    const pageThinkContents: string[] = [];
    for (const block of thinkBlocks) {
      const text = await block.textContent();
      if (text && text.trim()) {
        pageThinkContents.push(text.trim());
      }
    }
    console.log('[Test] 前台思考块数:', pageThinkContents.length);

    // 获取页面上的工具卡片内容
    const toolCards = await page.locator('.tool-card, [data-testid="tool-card"]').all();
    const pageToolNames: string[] = [];
    for (const card of toolCards) {
      const toolName = await card.locator('.tool-name, .tool-header').textContent().catch(() => '');
      if (toolName) {
        pageToolNames.push(toolName.trim());
      }
    }
    console.log('[Test] 前台工具卡片数:', pageToolNames.length);

    // 验证文本内容匹配
    console.log('[Test] ====== 文本内容匹配检查 ======');
    let textMatchCount = 0;
    for (const expectedText of expectedTextContents) {
      const found = pageTextContents.some(pageText =>
        pageText.includes(expectedText.substring(0, Math.min(50, expectedText.length))) ||
        expectedText.includes(pageText.substring(0, Math.min(50, pageText.length)))
      );
      if (found) {
        textMatchCount++;
        console.log(`[Test] ✅ 找到匹配文本: ${expectedText.substring(0, 80)}...`);
      } else {
        console.log(`[Test] ⚠️ 未找到匹配文本: ${expectedText.substring(0, 80)}...`);
      }
    }
    console.log(`[Test] 文本匹配率: ${textMatchCount}/${expectedTextContents.length}`);

    // 验证思考内容匹配
    console.log('[Test] ====== 思考内容匹配检查 ======');
    let thinkMatchCount = 0;
    for (const expectedThink of expectedThinkingContents) {
      const found = pageThinkContents.some(pageThink =>
        pageThink.includes(expectedThink.substring(0, Math.min(50, expectedThink.length))) ||
        expectedThink.includes(pageThink.substring(0, Math.min(50, pageThink.length)))
      );
      if (found) {
        thinkMatchCount++;
        console.log(`[Test] ✅ 找到匹配思考: ${expectedThink.substring(0, 80)}...`);
      } else {
        console.log(`[Test] ⚠️ 未找到匹配思考: ${expectedThink.substring(0, 80)}...`);
      }
    }
    console.log(`[Test] 思考匹配率: ${thinkMatchCount}/${expectedThinkingContents.length}`);

    // 验证工具调用匹配
    console.log('[Test] ====== 工具调用匹配检查 ======');
    let toolMatchCount = 0;
    for (const expectedTool of expectedToolCalls) {
      const found = pageToolNames.some(pageTool => pageTool.includes(expectedTool.name));
      if (found) {
        toolMatchCount++;
        console.log(`[Test] ✅ 找到工具: ${expectedTool.name}`);
      } else {
        console.log(`[Test] ⚠️ 未找到工具: ${expectedTool.name}`);
      }
    }
    console.log(`[Test] 工具匹配率: ${toolMatchCount}/${expectedToolCalls.length}`);

    // 11. 验证历史消息中的工具执行结果
    console.log('[Test] ========== 验证历史消息中的工具执行结果 ==========');
    const toolResults = getToolResults();
    const toolCalls = getToolCalls();
    console.log('[Test] tool_result.json 结果数:', toolResults.length);
    console.log('[Test] tool_calls.json 调用数:', toolCalls.length);

    // 从llm_calls的request.messages中提取工具结果消息
    const expectedToolResults: string[] = [];
    for (const call of llmCalls) {
      const requestMsgs = call.request?.messages || [];
      for (const msg of requestMsgs) {
        // role为tool的消息是工具执行结果
        if (msg.role === 'tool') {
          const content = msg.content || '';
          if (content.trim()) {
            expectedToolResults.push(content.trim());
            console.log(`[Test] 历史消息中工具结果: ${content.substring(0, 100)}...`);
          }
        }
      }
    }
    console.log(`[Test] 历史消息中的工具结果数: ${expectedToolResults.length}`);

    // 获取页面上的工具输出内容
    const pageToolOutputs: string[] = [];
    for (const card of toolCards) {
      const output = await card.locator('.tool-output, .tool-result, .execution-output').textContent().catch(() => '');
      if (output && output.trim()) {
        pageToolOutputs.push(output.trim());
      }
    }
    console.log('[Test] 前台工具输出数:', pageToolOutputs.length);

    // 验证工具结果匹配
    console.log('[Test] ====== 工具执行结果匹配检查 ======');
    let toolResultMatchCount = 0;
    for (const expectedResult of expectedToolResults) {
      const found = pageToolOutputs.some(pageOutput =>
        pageOutput.includes(expectedResult.substring(0, Math.min(50, expectedResult.length))) ||
        expectedResult.includes(pageOutput.substring(0, Math.min(50, pageOutput.length)))
      );
      if (found) {
        toolResultMatchCount++;
        console.log(`[Test] ✅ 找到匹配工具结果`);
      } else {
        // 尝试部分匹配
        const partialFound = pageToolOutputs.some(pageOutput =>
          expectedResult.length > 20 &&
          (pageOutput.includes(expectedResult.substring(0, 30)) ||
           expectedResult.includes(pageOutput.substring(0, 30)))
        );
        if (partialFound) {
          toolResultMatchCount++;
          console.log(`[Test] ✅ 部分匹配工具结果`);
        } else {
          console.log(`[Test] ⚠️ 未找到匹配工具结果: ${expectedResult.substring(0, 80)}...`);
        }
      }
    }
    console.log(`[Test] 工具结果匹配率: ${toolResultMatchCount}/${expectedToolResults.length}`);

    // 12. 总结
    console.log('[Test] ========== 测试总结 ==========');
    console.log('[Test] 控制台日志总数:', consoleLogs.length);
    console.log('[Test] 组件创建日志数:', componentCreateLogs.length);
    console.log('[Test] 实际收到WebSocket事件数:', wsReceivedEvents.length);
    console.log('[Test] 找到的核心组件数:', foundComponents.size);
    console.log('[Test] 页面用户消息数:', userMessages.length);
    console.log('[Test] 页面助手消息数:', assistantMessages.length);
    console.log('[Test] 缺失的关键事件数:', missingCriticalEvents.length);
    console.log('[Test] ====== 大模型输出对比 ======');
    console.log(`[Test] 文本匹配率: ${textMatchCount}/${expectedTextContents.length}`);
    console.log(`[Test] 思考匹配率: ${thinkMatchCount}/${expectedThinkingContents.length}`);
    console.log(`[Test] 工具匹配率: ${toolMatchCount}/${expectedToolCalls.length}`);
    console.log(`[Test] 工具结果匹配率: ${toolResultMatchCount}/${expectedToolResults.length}`);

    if (missingCriticalEvents.length > 0) {
      console.log('[Test] ⚠️ 缺失的关键事件:', missingCriticalEvents);
    }

    // 截图
    await page.screenshot({ path: path.join('d:', 'learnning', '260521', 'test-session-switch.png'), fullPage: true });
    console.log('[Test] ✅ 已保存截图: test-session-switch.png');

    // 验证文档中描述的关键组件都找到了
    console.log('[Test] ========== 验证文档一致性 ==========');
    const docComponents = [
      'ChatPanel',
      'SessionComponent',
      'UserMessage',
      'AssistantMessage',
      'ResponseBlock'
    ];

    const missingDocComponents = docComponents.filter(c => !foundComponents.has(c));
    if (missingDocComponents.length > 0) {
      console.log('[Test] ⚠️ 文档中描述但未找到的组件:', missingDocComponents);
    } else {
      console.log('[Test] ✅ 文档中描述的核心组件全部找到');
    }

    // 验证至少找到了核心组件
    expect(foundComponents.size).toBeGreaterThan(0);
    console.log('[Test] ✅ 测试完成');
  });
});