import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_DATA_DIR = path.join('d:', 'learnning', '260521', 'src', 'data', 'test');
const LLM_CALLS_PATH = path.join(TEST_DATA_DIR, 'llm_calls.json');

test.describe('录制模式数据收集', () => {
  test.beforeEach(() => {
    if (!fs.existsSync(TEST_DATA_DIR)) {
      fs.mkdirSync(TEST_DATA_DIR, { recursive: true });
    }
  });

  test('录制简单对话', async ({ page }) => {
    await page.goto('/');

    // 切换到录制模式
    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();
    const isRecording = await toggle.getAttribute('class');
    if (!isRecording.includes('active')) {
      await toggle.click();
      await page.waitForTimeout(2000);
    }
    console.log('[Test] 已切换到录制模式');

    // 选择测试项目
    const select = page.locator('.project-select');
    await select.waitFor();
    await page.waitForTimeout(2000);

    const options = await select.locator('option').all();
    if (options.length > 1) {
      await select.selectOption({ index: 1 });
      console.log('[Test] 已选择测试项目');
    }

    await page.waitForTimeout(1500);

    // 创建新会话
    const newBtn = page.locator('button:has-text("+ 新建")');
    if (await newBtn.isVisible()) {
      await newBtn.click();
      await page.waitForTimeout(2000);
    }

    // 发送简单对话消息
    const input = page.locator('textarea');
    await input.fill('你好，我是来测试录制功能的');
    await page.keyboard.press('Enter');
    console.log('[Test] 发送简单对话消息');

    // 等待响应
    await page.waitForTimeout(10000);

    // 发送第二个消息
    await input.fill('什么是人工智能？');
    await page.keyboard.press('Enter');
    console.log('[Test] 发送第二个消息');

    await page.waitForTimeout(10000);

    // 检查数据是否生成
    if (fs.existsSync(LLM_CALLS_PATH)) {
      const content = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
      const data = JSON.parse(content);
      console.log(`[Test] 已录制 ${data.length} 条 LLM 调用记录`);
      expect(data.length).toBeGreaterThan(0);
    }

    console.log('[Test] ✅ 简单对话录制完成');
  });

  test('录制工具调用 - 创建目录', async ({ page }) => {
    await page.goto('/');

    // 确保在录制模式
    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();
    const isRecording = await toggle.getAttribute('class');
    if (!isRecording.includes('active')) {
      await toggle.click();
      await page.waitForTimeout(2000);
    }

    // 选择测试项目
    const select = page.locator('.project-select');
    await select.waitFor();
    await page.waitForTimeout(1000);
    const options = await select.locator('option').all();
    if (options.length > 1) {
      await select.selectOption({ index: 1 });
    }

    await page.waitForTimeout(1500);

    // 创建新会话或选择现有会话
    const sessions = await page.locator('.session-item').all();
    if (sessions.length === 0) {
      const newBtn = page.locator('button:has-text("+ 新建")');
      if (await newBtn.isVisible()) {
        await newBtn.click();
        await page.waitForTimeout(2000);
      }
    } else {
      await sessions[0].click();
      await page.waitForTimeout(1000);
    }

    // 发送创建目录的请求
    const input = page.locator('textarea');
    await input.fill('在工作区创建一个名为 test_dir 的目录');
    await page.keyboard.press('Enter');
    console.log('[Test] 发送创建目录请求');

    await page.waitForTimeout(15000);

    // 检查数据
    if (fs.existsSync(LLM_CALLS_PATH)) {
      const content = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
      const data = JSON.parse(content);
      console.log(`[Test] 当前已录制 ${data.length} 条记录`);
    }

    console.log('[Test] ✅ 目录创建录制完成');
  });

  test('录制复杂操作 - 创建目录和文件', async ({ page }) => {
    await page.goto('/');

    // 确保在录制模式
    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();
    const isRecording = await toggle.getAttribute('class');
    if (!isRecording.includes('active')) {
      await toggle.click();
      await page.waitForTimeout(2000);
    }

    // 选择测试项目
    const select = page.locator('.project-select');
    await select.waitFor();
    await page.waitForTimeout(1000);
    const options = await select.locator('option').all();
    if (options.length > 1) {
      await select.selectOption({ index: 1 });
    }

    await page.waitForTimeout(1500);

    // 创建新会话
    const newBtn = page.locator('button:has-text("+ 新建")');
    if (await newBtn.isVisible()) {
      await newBtn.click();
      await page.waitForTimeout(2000);
    }

    // 发送复杂请求：创建目录并写入文件
    const input = page.locator('textarea');
    await input.fill('创建一个名为 project 的目录，然后在里面创建一个 README.md 文件，内容为 "这是一个测试项目"');
    await page.keyboard.press('Enter');
    console.log('[Test] 发送复杂操作请求');

    await page.waitForTimeout(20000);

    // 检查最终数据
    if (fs.existsSync(LLM_CALLS_PATH)) {
      const content = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
      const data = JSON.parse(content);
      console.log(`[Test] 录制完成，共 ${data.length} 条 LLM 调用记录`);
      
      // 输出最后一条记录摘要
      if (data.length > 0) {
        const lastRecord = data[data.length - 1];
        console.log(`[Test] 最后一条记录: ${lastRecord.call_id}`);
        console.log(`[Test] 用户提问: ${lastRecord.request.messages[0].content.substring(0, 50)}...`);
      }
    }

    console.log('[Test] ✅ 复杂操作录制完成');
  });
});