/**
 * 迭代二UI组件集成
 * 
 * 包含所有迭代二组件的注册和初始化逻辑
 */

// 加载组件
import RecordingPanel from './components/infrastructure/recording/RecordingPanel.js';
import ReplayControls from './components/infrastructure/recording/ReplayControls.js';
import ToolList from './components/infrastructure/tools/ToolList.js';
import LLMInvokePanel from './components/infrastructure/llm/LLMInvokePanel.js';

// 全局注册组件
function registerComponents(Vue) {
    if (Vue) {
        Vue.component('RecordingPanel', RecordingPanel);
        Vue.component('ReplayControls', ReplayControls);
        Vue.component('ToolList', ToolList);
        Vue.component('LLMInvokePanel', LLMInvokePanel);
    }
}

// 初始化组件（不使用Vue时）
function initComponents() {
    // RecordingPanel功能初始化
    window.initRecordingPanel = function() {
        return RecordingPanel;
    };
    
    // ReplayControls功能初始化
    window.initReplayControls = function() {
        return ReplayControls;
    };
    
    // ToolList功能初始化
    window.initToolList = function() {
        return ToolList;
    };
    
    // LLMInvokePanel功能初始化
    window.initLLMInvokePanel = function() {
        return LLMInvokePanel;
    };
}

// 导出
export {
    RecordingPanel,
    ReplayControls,
    ToolList,
    LLMInvokePanel,
    registerComponents,
    initComponents
};
