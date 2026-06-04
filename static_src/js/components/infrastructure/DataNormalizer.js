/**
 * DataNormalizer - 数据规范化工具
 * 
 * 统一处理后端返回的数据格式，确保前端使用一致的字段命名
 * 
 * 后端字段 → 前端字段映射：
 * - project_id → id (Project)
 * - config_id → id (WorkspaceConfig, ModelConfig, ToolConfig, StorageConfig)
 */
export const DataNormalizer = {
    /**
     * 规范化项目数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeProject(data) {
        if (Array.isArray(data)) {
            return data.map(item => this._normalizeProjectItem(item));
        }
        return this._normalizeProjectItem(data);
    },

    _normalizeProjectItem(item) {
        if (!item) return item;
        return {
            ...item,
            id: item.id || item.project_id || ''
        };
    },

    /**
     * 规范化工作区数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeWorkspace(data) {
        if (Array.isArray(data)) {
            return data.map(item => this._normalizeWorkspaceItem(item));
        }
        return this._normalizeWorkspaceItem(data);
    },

    _normalizeWorkspaceItem(item) {
        if (!item) return item;
        return {
            ...item,
            id: item.id || item.config_id || ''
        };
    },

    /**
     * 规范化模型配置数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeModel(data) {
        if (Array.isArray(data)) {
            return data.map(item => this._normalizeModelItem(item));
        }
        return this._normalizeModelItem(data);
    },

    _normalizeModelItem(item) {
        if (!item) return item;
        return {
            ...item,
            id: item.id || item.config_id || ''
        };
    },

    /**
     * 规范化工具配置数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeTool(data) {
        if (Array.isArray(data)) {
            return data.map(item => this._normalizeToolItem(item));
        }
        return this._normalizeToolItem(data);
    },

    _normalizeToolItem(item) {
        if (!item) return item;
        return {
            ...item,
            id: item.id || item.tool_id || item.config_id || '',
            name: item.name || item.tool_name || '',
            type: item.type || item.category || '',
            status: item.status || (item.is_active !== undefined ? (item.is_active ? 'active' : 'inactive') : 'inactive'),
            supported_os: item.supported_os || [],
            supported_terminals: item.supported_terminals || []
        };
    },

    /**
     * 规范化存储配置数据
     * @param {Object|Array} data - 原始数据
     * @returns {Object|Array} - 规范化后的数据
     */
    normalizeStorage(data) {
        if (Array.isArray(data)) {
            return data.map(item => this._normalizeStorageItem(item));
        }
        return this._normalizeStorageItem(data);
    },

    _normalizeStorageItem(item) {
        if (!item) return item;
        return {
            ...item,
            id: item.id || item.config_id || ''
        };
    },

    /**
     * 通用规范化方法
     * @param {Object|Array} data - 原始数据
     * @param {string} type - 数据类型: 'project', 'workspace', 'model', 'tool', 'storage'
     * @returns {Object|Array} - 规范化后的数据
     */
    normalize(data, type) {
        switch (type) {
            case 'project':
                return this.normalizeProject(data);
            case 'workspace':
                return this.normalizeWorkspace(data);
            case 'model':
                return this.normalizeModel(data);
            case 'tool':
                return this.normalizeTool(data);
            case 'storage':
                return this.normalizeStorage(data);
            default:
                return data;
        }
    },

    /**
     * 解析API响应数据
     * @param {Object|Array} result - API响应结果
     * @param {string} dataField - 数据字段名（如 'projects', 'data'）
     * @returns {Array} - 数据数组
     */
    parseResponse(result, dataField) {
        if (Array.isArray(result)) {
            return result;
        } else if (result && result.data && Array.isArray(result.data)) {
            return result.data;
        } else if (result && result[dataField] && Array.isArray(result[dataField])) {
            return result[dataField];
        }
        return [];
    }
};

window.DataNormalizer = DataNormalizer;