"""
Storage Config Routes - 存储配置管理API路由

提供存储配置的CRUD操作，允许用户控制哪些实体类型需要持久化。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from services.L1_infrastructure.L1e_storage_config import get_storage_config_service

router = APIRouter()


@router.get("/")
async def list_storage_configs():
    """获取所有存储配置"""
    try:
        config_service = get_storage_config_service()
        return config_service.list_configs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entity_type}")
async def get_storage_config(entity_type: str):
    """获取指定实体类型的存储配置"""
    try:
        config_service = get_storage_config_service()
        config = config_service.get_config(entity_type)
        if not config:
            raise HTTPException(status_code=404, detail=f"Storage config for '{entity_type}' not found")
        return config
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_storage_config(data: Dict[str, Any]):
    """创建新的存储配置"""
    try:
        entity_type = data.get("entity_type")
        if not entity_type:
            raise HTTPException(status_code=400, detail="entity_type is required")
        
        persist = data.get("persist", True)
        description = data.get("description", "")
        
        config_service = get_storage_config_service()
        result = config_service.add_config(entity_type, persist, description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{entity_type}")
async def update_storage_config(entity_type: str, data: Dict[str, Any]):
    """更新指定实体类型的存储配置"""
    try:
        persist = data.get("persist")
        description = data.get("description")
        
        if persist is None and description is None:
            raise HTTPException(status_code=400, detail="At least 'persist' or 'description' must be provided")
        
        config_service = get_storage_config_service()
        success = config_service.update_config(entity_type, persist, description)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Storage config for '{entity_type}' not found")
        
        return {"status": "success", "entity_type": entity_type}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entity_type}")
async def delete_storage_config(entity_type: str):
    """删除指定实体类型的存储配置"""
    try:
        config_service = get_storage_config_service()
        success = config_service.delete_config(entity_type)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Storage config for '{entity_type}' not found")
        
        return {"status": "success", "entity_type": entity_type}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/persist/types")
async def get_persist_types():
    """获取需要持久化的实体类型列表"""
    try:
        config_service = get_storage_config_service()
        return {"persist_types": config_service.get_persist_types()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/non-persist/types")
async def get_non_persist_types():
    """获取不需要持久化的实体类型列表"""
    try:
        config_service = get_storage_config_service()
        return {"non_persist_types": config_service.get_non_persist_types()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
