"""
提示词管理 API 路由

提供提示词模板的 CRUD 操作、版本管理和变量替换功能。
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Optional

from services.L2_domain.L2h_prompt_management import (
    PromptManagementService,
    Prompt,
    PromptVersion,
    get_prompt_management_service
)

router = APIRouter(prefix="/api/prompts", tags=["提示词管理"])

prompt_service = get_prompt_management_service()


@router.get("/", response_model=List[Prompt])
async def list_prompts(
    category: Optional[str] = Query(None, description="分类过滤"),
    include_inactive: bool = Query(False, description="是否包含非激活的提示词")
):
    """获取提示词列表"""
    prompts = prompt_service.list_prompts(category, include_inactive)
    return prompts


@router.get("/{prompt_id}", response_model=Optional[Prompt])
async def get_prompt(prompt_id: str):
    """获取单个提示词"""
    prompt = prompt_service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return prompt


@router.post("/", response_model=Prompt)
async def create_prompt(
    name: str = Body(..., description="提示词名称"),
    category: str = Body(..., description="提示词分类"),
    content: str = Body(..., description="提示词内容"),
    is_active: bool = Body(True, description="是否激活")
):
    """创建提示词"""
    prompt = prompt_service.create_prompt(name, category, content, is_active)
    return prompt


@router.put("/{prompt_id}", response_model=Optional[Prompt])
async def update_prompt(
    prompt_id: str,
    name: Optional[str] = Body(None, description="提示词名称"),
    category: Optional[str] = Body(None, description="提示词分类"),
    content: Optional[str] = Body(None, description="提示词内容"),
    is_active: Optional[bool] = Body(None, description="是否激活")
):
    """更新提示词"""
    prompt = prompt_service.update_prompt(
        prompt_id, content, name, category, is_active
    )
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return prompt


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """删除提示词（软删除）"""
    success = prompt_service.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return {"success": True, "message": "提示词已删除"}


@router.get("/{prompt_id}/versions", response_model=List[PromptVersion])
async def get_versions(prompt_id: str):
    """获取提示词的版本历史"""
    prompt = prompt_service.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    versions = prompt_service.get_versions(prompt_id)
    return versions


@router.post("/{prompt_id}/rollback")
async def rollback(
    prompt_id: str,
    version: str = Body(..., description="目标版本号")
):
    """回滚到指定版本"""
    success = prompt_service.rollback(prompt_id, version)
    if not success:
        raise HTTPException(status_code=404, detail="回滚失败，提示词或版本不存在")
    
    prompt = prompt_service.get_prompt(prompt_id)
    return {
        "success": True,
        "message": f"已回滚到版本 {version}",
        "prompt": prompt
    }


@router.post("/{prompt_id}/render")
async def render_prompt(
    prompt_id: str,
    variables: Dict[str, str] = Body(..., description="变量键值对")
):
    """渲染提示词，替换变量"""
    try:
        content = prompt_service.render_prompt(prompt_id, variables)
        return {"content": content}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))