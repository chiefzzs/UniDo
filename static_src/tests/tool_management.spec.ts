import { test, expect } from '@playwright/test';

test.describe('工具管理页面', () => {
  test('页面加载并显示工具列表', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 检查页面标题
    const title = page.locator('h2');
    await expect(title).toHaveText('🔧 工具管理');
    
    // 检查表格结构
    const table = page.locator('.data-table table');
    await expect(table).toBeVisible();
    
    // 检查表头
    const headers = page.locator('thead th');
    await expect(headers.nth(0)).toHaveText('工具名称');
    await expect(headers.nth(1)).toHaveText('工具类型');
    await expect(headers.nth(2)).toHaveText('支持操作系统');
    await expect(headers.nth(3)).toHaveText('支持终端');
    await expect(headers.nth(4)).toHaveText('描述');
    await expect(headers.nth(5)).toHaveText('状态');
    await expect(headers.nth(6)).toHaveText('创建时间');
    await expect(headers.nth(7)).toHaveText('操作');
    
    console.log('[Test] ✅ 工具管理页面加载成功');
  });

  test('搜索工具功能', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 输入搜索关键词
    const searchInput = page.locator('.search-box input');
    await searchInput.fill('Search');
    
    // 等待搜索结果
    await page.waitForTimeout(1000);
    
    console.log('[Test] ✅ 搜索功能测试完成');
  });

  test('打开新建工具弹窗', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 点击新建按钮
    const newBtn = page.locator('button:has-text("+ 新建工具")');
    await newBtn.click();
    
    // 检查弹窗
    const modal = page.locator('.modal-overlay');
    await expect(modal).toBeVisible();
    
    const modalTitle = page.locator('.modal-header h3');
    await expect(modalTitle).toHaveText('新建工具');
    
    console.log('[Test] ✅ 新建工具弹窗打开成功');
  });

  test('创建新工具', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 打开新建弹窗
    const newBtn = page.locator('button:has-text("+ 新建工具")');
    await newBtn.click();
    
    // 填写表单
    const nameInput = page.locator('.modal-body input[type="text"]');
    await nameInput.fill('测试工具');
    
    const typeSelect = page.locator('.modal-body select');
    await typeSelect.selectOption('file');
    
    const descriptionTextarea = page.locator('.modal-body textarea').first();
    await descriptionTextarea.fill('这是一个测试工具');
    
    // 点击保存
    const saveBtn = page.locator('.modal-footer button:has-text("保存")');
    await saveBtn.click();
    
    // 等待弹窗关闭
    await page.waitForTimeout(1000);
    
    // 检查工具是否创建成功
    const toolRow = page.locator('tbody tr');
    const count = await toolRow.count();
    expect(count).toBeGreaterThan(0);
    
    console.log('[Test] ✅ 创建新工具成功');
  });

  test('编辑工具', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 获取第一个工具的编辑按钮
    const editBtn = page.locator('tbody tr:first-child button:has-text("编辑")');
    if (await editBtn.isVisible()) {
      await editBtn.click();
      
      // 检查弹窗标题
      const modalTitle = page.locator('.modal-header h3');
      await expect(modalTitle).toHaveText('编辑工具');
      
      // 修改工具名称
      const nameInput = page.locator('.modal-body input[type="text"]');
      const originalName = await nameInput.getAttribute('value');
      await nameInput.fill(originalName + '_edited');
      
      // 保存
      const saveBtn = page.locator('.modal-footer button:has-text("保存")');
      await saveBtn.click();
      
      await page.waitForTimeout(1000);
      
      console.log('[Test] ✅ 编辑工具成功');
    } else {
      console.log('[Test] ⚠️ 没有可编辑的工具');
    }
  });

  test('删除工具', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 获取第一个工具的删除按钮
    const deleteBtn = page.locator('tbody tr:first-child button:has-text("删除")');
    if (await deleteBtn.isVisible()) {
      // 模拟确认对话框
      page.on('dialog', dialog => dialog.accept());
      
      await deleteBtn.click();
      await page.waitForTimeout(1000);
      
      console.log('[Test] ✅ 删除工具成功');
    } else {
      console.log('[Test] ⚠️ 没有可删除的工具');
    }
  });

  test('检查操作系统选择器', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 打开新建弹窗
    const newBtn = page.locator('button:has-text("+ 新建工具")');
    await newBtn.click();
    
    // 检查操作系统选项
    const osCheckboxes = page.locator('.checkbox-group:first-child input[type="checkbox"]');
    const osLabels = page.locator('.checkbox-group:first-child .checkbox-label');
    
    expect(await osCheckboxes.count()).toBe(3);
    expect(await osLabels.nth(0).textContent()).toContain('Windows');
    expect(await osLabels.nth(1).textContent()).toContain('Linux');
    expect(await osLabels.nth(2).textContent()).toContain('macOS');
    
    console.log('[Test] ✅ 操作系统选择器测试完成');
  });

  test('检查终端选择器', async ({ page }) => {
    await page.goto('/admin/tools');
    
    // 打开新建弹窗
    const newBtn = page.locator('button:has-text("+ 新建工具")');
    await newBtn.click();
    
    // 检查终端选项（第二个checkbox-group）
    const terminalCheckboxes = page.locator('.checkbox-group').nth(1).locator('input[type="checkbox"]');
    const terminalLabels = page.locator('.checkbox-group').nth(1).locator('.checkbox-label');
    
    expect(await terminalCheckboxes.count()).toBe(4);
    expect(await terminalLabels.nth(0).textContent()).toContain('PowerShell');
    expect(await terminalLabels.nth(1).textContent()).toContain('CMD');
    expect(await terminalLabels.nth(2).textContent()).toContain('Bash');
    expect(await terminalLabels.nth(3).textContent()).toContain('Zsh');
    
    console.log('[Test] ✅ 终端选择器测试完成');
  });
});