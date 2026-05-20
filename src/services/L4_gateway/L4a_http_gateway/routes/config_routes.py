"""
Config Routes - 配置管理API路由

支持多种API格式以兼容前端：
- /api/config/workspace, /api/config/model
- /api/workspaces, /api/models
- /api/tools
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, List
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.workspace_config import WorkspaceConfig
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.model_config import ModelConfig
from services.L3_scenario_coordination.L3c_ui_scenarios.ConfigManager.tool_config import ToolConfig

router = APIRouter()

# 工作区配置路由 (兼容 /api/config/workspace)
@router.get("/config/workspace")
async def list_workspace_configs():
    """获取工作区配置列表"""
    try:
        config = WorkspaceConfig()
        result = config.list()
        return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspaces")
async def create_workspace(data: Dict[str, Any]):
    """创建工作区"""
    try:
        config = WorkspaceConfig()
        result = config.create(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{config_id}")
async def get_workspace(config_id: str):
    """获取工作区"""
    try:
        config = WorkspaceConfig()
        result = config.get(config_id)
        if not result:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/workspaces/{config_id}")
async def update_workspace(config_id: str, data: Dict[str, Any]):
    """更新工作区"""
    try:
        config = WorkspaceConfig()
        result = config.update(config_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/workspaces/batch")
async def batch_delete_workspaces(data: Dict[str, Any] = Body(...)):
    """批量删除工作区"""
    try:
        workspace_ids = data.get("workspace_ids", [])
        results = {"success": [], "failed": []}
        config = WorkspaceConfig()
        for workspace_id in workspace_ids:
            try:
                result = config.delete(workspace_id)
                if result.get("success"):
                    results["success"].append(workspace_id)
                else:
                    results["failed"].append(workspace_id)
            except:
                results["failed"].append(workspace_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/workspaces/{config_id}")
async def delete_workspace(config_id: str):
    """删除工作区"""
    try:
        config = WorkspaceConfig()
        result = config.delete(config_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail="Workspace not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 模型配置路由 (兼容 /api/config/model)
@router.get("/config/model")
async def list_model_configs():
    """获取模型配置列表"""
    try:
        config = ModelConfig()
        result = config.list()
        return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """获取模型列表"""
    try:
        config = ModelConfig()
        result = config.list()
        return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models")
async def create_model(data: Dict[str, Any]):
    """创建模型配置"""
    try:
        config = ModelConfig()
        result = config.create(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{config_id}")
async def get_model(config_id: str):
    """获取模型配置"""
    try:
        config = ModelConfig()
        result = config.get(config_id)
        if not result:
            raise HTTPException(status_code=404, detail="Model config not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/models/{config_id}")
async def update_model(config_id: str, data: Dict[str, Any]):
    """更新模型配置"""
    try:
        config = ModelConfig()
        result = config.update(config_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Model config not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/models/{config_id}")
async def delete_model(config_id: str):
    """删除模型配置"""
    try:
        config = ModelConfig()
        result = config.delete(config_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail="Model config not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/config/model/batch")
async def batch_delete_models(data: Dict[str, Any]):
    """批量删除模型配置"""
    try:
        config_ids = data.get("config_ids", [])
        results = {"success": [], "failed": []}
        config = ModelConfig()
        for config_id in config_ids:
            try:
                result = config.delete(config_id)
                if result.get("success"):
                    results["success"].append(config_id)
                else:
                    results["failed"].append(config_id)
            except:
                results["failed"].append(config_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 工具配置路由
@router.get("/tools")
async def list_tools():
    """获取工具列表"""
    try:
        config = ToolConfig()
        result = config.list()
        return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools")
async def register_tool(data: Dict[str, Any]):
    """注册工具"""
    try:
        config = ToolConfig()
        result = config.register(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/{tool_id}")
async def get_tool(tool_id: str):
    """获取工具信息"""
    try:
        config = ToolConfig()
        result = config.get(tool_id)
        if not result:
            raise HTTPException(status_code=404, detail="Tool not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tools/{tool_id}")
async def update_tool(tool_id: str, data: Dict[str, Any]):
    """更新工具配置"""
    try:
        config = ToolConfig()
        result = config.update(tool_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Tool not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tools/{tool_id}")
async def unregister_tool(tool_id: str):
    """注销工具"""
    try:
        config = ToolConfig()
        result = config.unregister(tool_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail="Tool not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))