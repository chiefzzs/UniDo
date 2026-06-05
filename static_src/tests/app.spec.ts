import { test, expect } from '@playwright/test';

test.describe('会话管理功能', () => {
  test('页面加载后显示会话列表区域', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('.chat-sidebar')).toBeVisible();
    await expect(page.locator('.section-title')).toContainText('会话列表');
    await expect(page.locator('.project-select')).toBeVisible();
    await expect(page.locator('button:has-text("+ 新建")')).toBeVisible();
  });

  test('项目选择下拉框加载项目列表', async ({ page }) => {
    await page.goto('/');
    
    const select = page.locator('.project-select');
    await select.waitFor();
    
    const options = await select.locator('option').all();
    expect(options.length).toBeGreaterThanOrEqual(1);
  });

  test('点击新建按钮创建会话', async ({ page }) => {
    await page.goto('/');
    
    const select = page.locator('.project-select');
    await select.waitFor();
    
    const options = await select.locator('option').all();
    if (options.length > 1) {
      await select.selectOption({ index: 1 });
      
      await page.waitForTimeout(1000);
      
      const initialCount = await page.locator('.session-item').count();
      
      await page.click('button:has-text("+ 新建")');
      
      await page.waitForTimeout(2000);
      
      const newCount = await page.locator('.session-item').count();
      expect(newCount).toBeGreaterThan(initialCount);
    }
  });

  test('点击会话项切换会话', async ({ page }) => {
    await page.goto('/');
    
    const select = page.locator('.project-select');
    await select.waitFor();
    
    const options = await select.locator('option').all();
    if (options.length > 1) {
      await select.selectOption({ index: 1 });
      
      await page.waitForTimeout(1000);
      
      const sessions = await page.locator('.session-item').all();
      if (sessions.length > 0) {
        await sessions[0].click();
        
        await page.waitForTimeout(1000);
        
        expect(sessions[0]).toHaveClass(/active/);
      }
    }
  });
});

test.describe('配置管理页面', () => {
  test('导航到项目页面', async ({ page }) => {
    await page.goto('/');
    
    await page.click('.menu-tab:has-text("项目")');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#page-projects')).toBeVisible();
  });

  test('导航到工作区页面', async ({ page }) => {
    await page.goto('/');
    
    await page.click('.menu-tab:has-text("工作区")');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#page-workspaces')).toBeVisible();
  });

  test('导航到模型配置页面', async ({ page }) => {
    await page.goto('/');
    
    await page.click('.menu-tab:has-text("模型")');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#page-models')).toBeVisible();
  });

  test('导航到工具页面', async ({ page }) => {
    await page.goto('/');
    
    await page.click('.menu-tab:has-text("工具")');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#page-tools')).toBeVisible();
  });

  test('导航到存储配置页面', async ({ page }) => {
    await page.goto('/');
    
    await page.click('.menu-tab:has-text("存储配置")');
    await page.waitForTimeout(500);
    
    await expect(page.locator('#page-storage')).toBeVisible();
  });
});

test.describe('聊天界面功能', () => {
  test('聊天区域显示', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('.chat-main')).toBeVisible();
  });

  test('导航到对话页面', async ({ page }) => {
    await page.goto('/');
    
    await page.click('.menu-tab:has-text("对话")');
    await page.waitForTimeout(500);
    
    await expect(page.locator('.chat-page')).toBeVisible();
  });
});

test.describe('录制回放功能', () => {
  test('录制回放按钮存在', async ({ page }) => {
    await page.goto('/');
    
    const toggle = page.locator('.replay-toggle');
    await toggle.waitFor();
    await expect(toggle).toBeVisible();
  });
});

test.describe('页面导航', () => {
  test('导航栏显示', async ({ page }) => {
    await page.goto('/');
    
    await expect(page.locator('.top-nav')).toBeVisible();
    await expect(page.locator('.logo')).toBeVisible();
    await expect(page.locator('.menu-tabs')).toBeVisible();
  });

  test('所有菜单按钮存在', async ({ page }) => {
    await page.goto('/');
    
    const tabs = page.locator('.menu-tab');
    await tabs.first().waitFor();
    
    const labels = await tabs.allTextContents();
    expect(labels.some(label => label.includes('对话'))).toBe(true);
    expect(labels.some(label => label.includes('项目'))).toBe(true);
    expect(labels.some(label => label.includes('工作区'))).toBe(true);
    expect(labels.some(label => label.includes('模型'))).toBe(true);
    expect(labels.some(label => label.includes('工具'))).toBe(true);
    expect(labels.some(label => label.includes('存储配置'))).toBe(true);
  });
});

test.describe('响应式布局', () => {
  test('侧边栏在小屏幕显示', async ({ page }) => {
    await page.goto('/');
    await page.setViewportSize({ width: 768, height: 1024 });
    
    await expect(page.locator('.chat-sidebar')).toBeVisible();
  });

  test('主内容区域自适应', async ({ page }) => {
    await page.goto('/');
    
    const main = page.locator('.chat-main');
    await main.waitFor();
    
    const boundingBox = await main.boundingBox();
    expect(boundingBox.width).toBeGreaterThan(0);
    expect(boundingBox.height).toBeGreaterThan(0);
  });
});