/**
 * SessionContext - 会话上下文类
 * 
 * 职责：封装单个会话的状态，实现面向对象的状态管理
 * 切换会话时释放 SessionContext 对象，自动清理所有状态
 * 
 * 设计层次：
 *   Session → Dialog → Round → Text/Thinking/Reasoning/Tool
 * 
 * 使用方式：
 * const context = new SessionContext(sessionId);
 * context.markDialogProcessed(dialogId);
 * context.isDialogProcessed(dialogId);
 */
class SessionContext {
    /**
     * 构造函数
     * @param {string} sessionId - 会话ID
     */
    constructor(sessionId) {
        this.sessionId = sessionId;
        
        // 响应块集合（会话级别，每个会话独立）
        this._responseBlocks = new Map();
        
        // 已处理的 dialog_id 集合
        this._processedDialogIds = new Set();
        
        // 已处理的工具调用集合
        this._processedToolCalls = new Set();
        
        // 已处理的响应块ID集合
        this._processedResponseIds = new Set();
        
        // 工具调用ID到响应块的映射
        this._callIdToResponseIdMap = new Map();
        
        // 轮次状态映射
        this._roundStates = new Map();
        
        // 当前响应块ID
        this._currentResponseBlockId = null;
        
        // 当前对话ID
        this._currentDialogId = null;
        
        // 当前轮次号
        this._currentRoundNumber = null;
        
        console.log(`[SessionContext] 创建会话上下文: ${sessionId}`);
    }
    
    // ==================== Response Blocks 管理 ====================
    
    /**
     * 获取响应块
     * @param {string} responseId 
     * @returns {object|null}
     */
    getResponseBlock(responseId) {
        return this._responseBlocks.get(responseId) || null;
    }
    
    /**
     * 设置响应块
     * @param {string} responseId 
     * @param {object} block 
     */
    setResponseBlock(responseId, block) {
        this._responseBlocks.set(responseId, block);
    }
    
    /**
     * 删除响应块
     * @param {string} responseId 
     */
    deleteResponseBlock(responseId) {
        this._responseBlocks.delete(responseId);
    }
    
    /**
     * 获取所有响应块
     * @returns {Map}
     */
    getAllResponseBlocks() {
        return this._responseBlocks;
    }
    
    /**
     * 清空所有响应块
     */
    clearResponseBlocks() {
        this._responseBlocks.clear();
    }
    
    /**
     * 获取响应块数量
     * @returns {number}
     */
    getResponseBlockCount() {
        return this._responseBlocks.size;
    }
    
    // ==================== Dialog 状态管理 ====================
    
    /**
     * 标记 dialog_id 已处理
     * @param {string} dialogId 
     */
    markDialogProcessed(dialogId) {
        this._processedDialogIds.add(dialogId);
    }
    
    /**
     * 检查 dialog_id 是否已处理
     * @param {string} dialogId 
     * @returns {boolean}
     */
    isDialogProcessed(dialogId) {
        return this._processedDialogIds.has(dialogId);
    }
    
    // ==================== Tool Call 状态管理 ====================
    
    /**
     * 标记工具调用已处理
     * @param {string} callId 
     */
    markToolCallProcessed(callId) {
        this._processedToolCalls.add(callId);
    }
    
    /**
     * 检查工具调用是否已处理
     * @param {string} callId 
     * @returns {boolean}
     */
    isToolCallProcessed(callId) {
        return this._processedToolCalls.has(callId);
    }
    
    // ==================== Response 状态管理 ====================
    
    /**
     * 标记响应块已处理
     * @param {string} responseId 
     */
    markResponseProcessed(responseId) {
        this._processedResponseIds.add(responseId);
    }
    
    /**
     * 检查响应块是否已处理
     * @param {string} responseId 
     * @returns {boolean}
     */
    isResponseProcessed(responseId) {
        return this._processedResponseIds.has(responseId);
    }
    
    // ==================== Call ID 映射 ====================
    
    /**
     * 设置工具调用ID到响应块的映射
     * @param {string} callId 
     * @param {string} responseId 
     */
    setCallIdToResponseId(callId, responseId) {
        this._callIdToResponseIdMap.set(callId, responseId);
    }
    
    /**
     * 获取工具调用对应的响应块ID
     * @param {string} callId 
     * @returns {string|null}
     */
    getResponseIdByCallId(callId) {
        return this._callIdToResponseIdMap.get(callId) || null;
    }
    
    // ==================== Round 状态管理 ====================
    
    /**
     * 设置轮次状态
     * @param {number} roundNumber 
     * @param {object} state 
     */
    setRoundState(roundNumber, state) {
        this._roundStates.set(roundNumber, state);
    }
    
    /**
     * 获取轮次状态
     * @param {number} roundNumber 
     * @returns {object|null}
     */
    getRoundState(roundNumber) {
        return this._roundStates.get(roundNumber) || null;
    }
    
    // ==================== 当前状态管理 ====================
    
    /**
     * 设置当前响应块ID
     * @param {string|null} responseBlockId 
     */
    setCurrentResponseBlockId(responseBlockId) {
        this._currentResponseBlockId = responseBlockId;
    }
    
    /**
     * 获取当前响应块ID
     * @returns {string|null}
     */
    getCurrentResponseBlockId() {
        return this._currentResponseBlockId;
    }
    
    /**
     * 设置当前对话ID
     * @param {string|null} dialogId 
     */
    setCurrentDialogId(dialogId) {
        this._currentDialogId = dialogId;
    }
    
    /**
     * 获取当前对话ID
     * @returns {string|null}
     */
    getCurrentDialogId() {
        return this._currentDialogId;
    }
    
    /**
     * 设置当前轮次号
     * @param {number|null} roundNumber 
     */
    setCurrentRoundNumber(roundNumber) {
        this._currentRoundNumber = roundNumber;
    }
    
    /**
     * 获取当前轮次号
     * @returns {number|null}
     */
    getCurrentRoundNumber() {
        return this._currentRoundNumber;
    }
    
    // ==================== 获取状态 ====================
    
    /**
     * 获取所有已处理的 dialog_id
     * @returns {Set}
     */
    getProcessedDialogIds() {
        return this._processedDialogIds;
    }
    
    /**
     * 获取所有已处理的工具调用
     * @returns {Set}
     */
    getProcessedToolCalls() {
        return this._processedToolCalls;
    }
    
    /**
     * 获取所有已处理的响应块ID
     * @returns {Set}
     */
    getProcessedResponseIds() {
        return this._processedResponseIds;
    }
    
    // ==================== 清理 ====================
    
    /**
     * 清理所有状态（用于会话切换时）
     * 父对象销毁时，子对象自动销毁
     * 按照层次结构逐一清理：Session → Dialog → Round → Text/Thinking/Reasoning/Tool
     */
    clear() {
        console.log(`[SessionContext] =========================================`);
        console.log(`[SessionContext] 🗑️  开始清理会话上下文: ${this.sessionId}`);
        console.log(`[SessionContext] =========================================`);
        
        // 1. 清理响应块（包含 Text/Thinking/Reasoning/Tool）
        console.log(`[SessionContext] 📦 清理响应块 (ResponseBlocks):`);
        if (this._responseBlocks.size > 0) {
            this._responseBlocks.forEach((block, id) => {
                console.log(`  └─ 删除响应块: ${id}`);
                console.log(`     ├─ Text: ${block.textContent?.substring(0, 50) || '(empty)'}...`);
                console.log(`     ├─ Thinking: ${block.thinkContent?.substring(0, 50) || '(empty)'}...`);
                console.log(`     ├─ Reasoning: ${block.reasonContent?.substring(0, 50) || '(empty)'}...`);
                console.log(`     └─ ToolCalls: ${block.toolCalls?.length || 0} 个`);
            });
        } else {
            console.log(`  └─ 无响应块需要清理`);
        }
        this._responseBlocks.clear();
        
        // 2. 清理已处理的响应块ID
        console.log(`[SessionContext] 🏷️ 清理已处理的响应块ID:`);
        console.log(`  └─ 删除 ${this._processedResponseIds.size} 个已处理的响应块ID`);
        this._processedResponseIds.clear();
        
        // 3. 清理工具调用映射
        console.log(`[SessionContext] 🔧 清理工具调用映射 (CallIdToResponseIdMap):`);
        console.log(`  └─ 删除 ${this._callIdToResponseIdMap.size} 个工具调用映射`);
        this._callIdToResponseIdMap.clear();
        
        // 4. 清理已处理的工具调用
        console.log(`[SessionContext] 🔧 清理已处理的工具调用:`);
        console.log(`  └─ 删除 ${this._processedToolCalls.size} 个已处理的工具调用`);
        this._processedToolCalls.clear();
        
        // 5. 清理轮次状态（包含 Round）
        console.log(`[SessionContext] 🔄 清理轮次状态 (RoundStates):`);
        if (this._roundStates.size > 0) {
            this._roundStates.forEach((state, key) => {
                console.log(`  └─ 删除轮次: ${key}`);
                console.log(`     ├─ dialog_id: ${state.dialog_id}`);
                console.log(`     └─ responseBlocks: ${state.responseBlocks?.length || 0} 个`);
            });
        } else {
            console.log(`  └─ 无轮次状态需要清理`);
        }
        this._roundStates.clear();
        
        // 6. 清理已处理的对话（包含 Dialog）
        console.log(`[SessionContext] 💬 清理已处理的对话 (Dialogs):`);
        console.log(`  └─ 删除 ${this._processedDialogIds.size} 个已处理的对话ID`);
        if (this._processedDialogIds.size > 0) {
            this._processedDialogIds.forEach(id => {
                console.log(`     └─ ${id}`);
            });
        }
        this._processedDialogIds.clear();
        
        // 7. 清理当前状态
        console.log(`[SessionContext] 📍 清理当前状态:`);
        console.log(`  ├─ currentDialogId: ${this._currentDialogId} → null`);
        console.log(`  ├─ currentResponseBlockId: ${this._currentResponseBlockId} → null`);
        console.log(`  └─ currentRoundNumber: ${this._currentRoundNumber} → null`);
        
        this._currentResponseBlockId = null;
        this._currentDialogId = null;
        this._currentRoundNumber = null;
        
        console.log(`[SessionContext] ✅ 会话上下文清理完成: ${this.sessionId}`);
        console.log(`[SessionContext] =========================================`);
    }
    
    /**
     * 获取上下文摘要
     * @returns {object}
     */
    getSummary() {
        return {
            sessionId: this.sessionId,
            responseBlockCount: this._responseBlocks.size,
            processedDialogCount: this._processedDialogIds.size,
            processedToolCallCount: this._processedToolCalls.size,
            processedResponseCount: this._processedResponseIds.size,
            callIdMapSize: this._callIdToResponseIdMap.size,
            roundStateCount: this._roundStates.size,
            currentDialogId: this._currentDialogId,
            currentResponseBlockId: this._currentResponseBlockId,
            currentRoundNumber: this._currentRoundNumber
        };
    }
    
    /**
     * 打印上下文摘要
     */
    logSummary() {
        const summary = this.getSummary();
        console.log(`[SessionContext] 会话 ${summary.sessionId} 状态摘要:`);
        console.log(`  - 响应块数: ${summary.responseBlockCount}`);
        console.log(`  - 已处理对话数: ${summary.processedDialogCount}`);
        console.log(`  - 已处理工具调用数: ${summary.processedToolCallCount}`);
        console.log(`  - 已处理响应块数: ${summary.processedResponseCount}`);
        console.log(`  - 当前对话ID: ${summary.currentDialogId}`);
        console.log(`  - 当前响应块ID: ${summary.currentResponseBlockId}`);
        console.log(`  - 当前轮次: ${summary.currentRoundNumber}`);
    }
}

export default SessionContext;