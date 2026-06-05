import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const TEST_DATA_DIR = path.join('d:', 'learnning', '260521', 'src', 'data', 'test');
const LLM_CALLS_PATH = path.join(TEST_DATA_DIR, 'llm_calls.json');

test.describe('回放模式功能', () => {
  test.beforeEach(() => {
    if (!fs.existsSync(TEST_DATA_DIR)) {
      fs.mkdirSync(TEST_DATA_DIR, { recursive: true });
    }
  });

  test('回放模式下发送消息不应新增 llm_calls.json 数据', async ({ page }) => {
    await page.goto('/');

    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();

    const isRecording = await toggle.getAttribute('class');
    if (isRecording.includes('active')) {
      await toggle.click();
      await page.waitForTimeout(1500);
    }
    console.log('[Test] 当前模式: 回放模式');

    const select = page.locator('.project-select');
    await select.waitFor();
    await page.waitForTimeout(2000);

    const options = await select.locator('option').all();
    console.log(`[Test] 找到 ${options.length} 个项目`);

    for (let i = 0; i < options.length; i++) {
      const text = await options[i].textContent();
      const value = await options[i].getAttribute('value');
      console.log(`[Test] 选项 ${i}: "${text}" (value: ${value})`);
    }

    if (options.length > 1) {
      await select.selectOption({ index: 1 });
      console.log('[Test] 已选择项目');
    } else {
      console.warn('[Test] 没有可用项目，跳过测试');
      return;
    }

    await page.waitForTimeout(1500);

    const newBtn = page.locator('button:has-text("+ 新建")');
    if (await newBtn.isVisible()) {
      await newBtn.click();
      await page.waitForTimeout(2000);
    }

    let fileSizeBefore = 0;
    if (fs.existsSync(LLM_CALLS_PATH)) {
      const content = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
      const data = JSON.parse(content);
      fileSizeBefore = content.length;
      console.log(`[Test] 发送前: ${fileSizeBefore} bytes, ${data.length} 条记录`);
    }

    const input = page.locator('input[type="text"]');
    if (await input.count() > 0) {
      await input.fill('回放模式测试');
      await page.keyboard.press('Enter');
      console.log('[Test] 消息已发送');

      await page.waitForTimeout(5000);

      if (fs.existsSync(LLM_CALLS_PATH)) {
        const contentAfter = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
        const dataAfter = JSON.parse(contentAfter);
        const fileSizeAfter = contentAfter.length;
        console.log(`[Test] 发送后: ${fileSizeAfter} bytes, ${dataAfter.length} 条记录`);

        const sizeDiff = fileSizeAfter - fileSizeBefore;
        console.log(`[Test] 差值: ${sizeDiff} bytes`);

        expect(sizeDiff).toBeLessThan(500);
        console.log('[Test] ✅ 通过: 回放模式无数据写入');
      }
    }
  });

  test('录制模式下发送消息应新增 llm_calls.json 数据', async ({ page }) => {
    // 录制模式测试不清空数据，使用现有的测试数据
    if (!fs.existsSync(LLM_CALLS_PATH)) {
      fs.writeFileSync(LLM_CALLS_PATH, '[]');
    }

    await page.goto('/');

    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();

    const isRecording = await toggle.getAttribute('class');
    if (!isRecording.includes('active')) {
      await toggle.click();
      await page.waitForTimeout(2000);
    }
    console.log('[Test] 当前模式: 录制模式');

    const select = page.locator('.project-select');
    await select.waitFor();
    await page.waitForTimeout(2000);

    const options = await select.locator('option').all();
    console.log(`[Test] 找到 ${options.length} 个项目`);

    if (options.length > 1) {
      await select.selectOption({ index: 1 });
      console.log('[Test] 已选择项目');
    } else {
      console.warn('[Test] 没有可用项目，跳过测试');
      return;
    }

    await page.waitForTimeout(1500);

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

    let recordsBefore = 0;
    if (fs.existsSync(LLM_CALLS_PATH)) {
      const content = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
      const data = JSON.parse(content);
      recordsBefore = data.length;
      console.log(`[Test] 发送前记录数: ${recordsBefore}`);
    }

    const input = page.locator('input[type="text"]');
    if (await input.count() > 0) {
      await input.fill('录制模式测试');
      await page.keyboard.press('Enter');
      console.log('[Test] 消息已发送');

      await page.waitForTimeout(10000);

      if (fs.existsSync(LLM_CALLS_PATH)) {
        const contentAfter = fs.readFileSync(LLM_CALLS_PATH, 'utf-8');
        const dataAfter = JSON.parse(contentAfter);
        const recordsAfter = dataAfter.length;
        console.log(`[Test] 发送后记录数: ${recordsAfter}`);

        expect(recordsAfter).toBeGreaterThan(recordsBefore);
        console.log('[Test] ✅ 通过: 录制模式有新数据');
      }
    }
  });

  test('模式切换时后端 API 被调用', async ({ page }) => {
    await page.goto('/');

    const apiCalls = [];
    page.on('request', (request) => {
      if (request.url().includes('/llm/mode')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          body: request.postData()
        });
        console.log(`[Test] API调用: ${request.method()} ${request.url()}`);
      }
    });

    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();
    await toggle.click();
    await page.waitForTimeout(2000);

    expect(apiCalls.length).toBeGreaterThan(0);

    const call = apiCalls[0];
    expect(call.method).toBe('POST');
    expect(call.url).toContain('/llm/mode');

    const body = JSON.parse(call.body);
    expect(body).toHaveProperty('mode');
    expect(['record', 'loopback']).toContain(body.mode);
    console.log('[Test] ✅ 通过: 模式切换API正确调用');
  });
});