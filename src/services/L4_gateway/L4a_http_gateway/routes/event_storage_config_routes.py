"""
Event Storage Config Routes - 事件存储配置管理API路由

提供事件存储配置的CRUD操作，允许用户控制哪些事件类型需要持久化到项目时间。
支持单个更新和批量更新。
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from services.L1_infrastructure.L1e_storage_config.event_storage_config_service import get_event_storage_config_service

router = APIRouter()


@router.get("/")
async def list_event_storage_configs(project_id: Optional[str] = Query(None)):
    """
    获取所有事件存储配置
    
    Args:
        project_id: 项目ID（可选，如果不提供则返回默认配置）
    
    Returns:
        事件存储配置列表
    """
    try:
        config_service = get_event_storage_config_service()
        return config_service.list_configs(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check/{event_type}")
async def check_event_persist(
    event_type: str,
    project_id: Optional[str] = Query(None)
):
    """
    检查指定事件类型是否应该持久化
    
    Args:
        event_type: 事件类型
        project_id: 项目ID（可选）
    
    Returns:
        是否应该持久化
    """
    try:
        config_service = get_event_storage_config_service()
        should_persist = config_service.should_persist_event(event_type, project_id)
        return {"event_type": event_type, "persist": should_persist}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_type}")
async def get_event_storage_config(
    event_type: str,
    project_id: Optional[str] = Query(None)
):
    """
    获取指定事件类型的存储配置
    
    Args:
        event_type: 事件类型
        project_id: 项目ID（可选）
    
    Returns:
        事件存储配置
    """
    try:
        config_service = get_event_storage_config_service()
        config = config_service.get_config(event_type, project_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Event storage config for '{event_type}' not found"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{event_type}")
async def update_event_storage_config(
    event_type: str,
    data: Dict[str, Any],
    project_id: Optional[str] = Query(None)
):
    """
    更新指定事件类型的存储配置
    
    Args:
        event_type: 事件类型
        data: 更新数据，包含 persist 和可选的 description
        project_id: 项目ID（可选）
    
    Returns:
        更新结果
    """
    try:
        persist = data.get("persist")
        description = data.get("description")
        
        if persist is None:
            raise HTTPException(
                status_code=400,
                detail="'persist' field is required"
            )
        
        config_service = get_event_storage_config_service()
        success = config_service.update_config(event_type, persist, project_id, description)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update event storage config for '{event_type}'"
            )
        
        return {
            "status": "success",
            "event_type": event_type,
            "persist": persist,
            "project_id": project_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_update_event_storage_configs(
    data: Dict[str, Any],
    project_id: Optional[str] = Query(None)
):
    """
    批量更新事件存储配置
    
    Args:
        data: 包含 updates 数组，每个元素包含 event_type 和 persist
        project_id: 项目ID（可选）
    
    Returns:
        更新结果
    """
    try:
        updates = data.get("updates", [])
        
        if not updates:
            raise HTTPException(
                status_code=400,
                detail="'updates' array is required and cannot be empty"
            )
        
        # 验证更新数据格式
        for update in updates:
            if "event_type" not in update:
                raise HTTPException(
                    status_code=400,
                    detail="Each update must contain 'event_type'"
                )
            if "persist" not in update:
                raise HTTPException(
                    status_code=400,
                    detail="Each update must contain 'persist'"
                )
        
        config_service = get_event_storage_config_service()
        success = config_service.batch_update_configs(updates, project_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to batch update event storage configs"
            )
        
        return {
            "status": "success",
            "updated_count": len(updates),
            "project_id": project_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/project/{project_id}")
async def delete_project_event_config(project_id: str):
    """
    删除项目的配置，恢复使用默认配置
    
    Args:
        project_id: 项目ID
    
    Returns:
        删除结果
    """
    try:
        config_service = get_event_storage_config_service()
        success = config_service.delete_project_config(project_id)
        
        return {"status": "success", "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_event_storage_configs(project_id: Optional[str] = Query(None)):
    """
    重置事件存储配置为默认值
    
    Args:
        project_id: 项目ID（可选，如果不提供则重置默认配置）
    
    Returns:
        重置结果
    """
    try:
        from services.L1_infrastructure.L1e_storage_config.event_storage_config_service import (
            DEFAULT_EVENT_STORAGE_CONFIG
        )
        
        config_service = get_event_storage_config_service()
        
        if project_id:
            config_service._config[project_id] = DEFAULT_EVENT_STORAGE_CONFIG.copy()
        else:
            config_service._config["default"] = DEFAULT_EVENT_STORAGE_CONFIG.copy()
        
        config_service._save_config(config_service._config)
        
        return {
            "status": "success",
            "message": f"Reset {'project' if project_id else 'default'} event storage config",
            "project_id": project_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
