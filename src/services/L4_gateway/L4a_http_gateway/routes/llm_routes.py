"""
LLM Routes - LLM模式切换API路由

提供LLM运行模式（录制/回放）的切换接口。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.L2_domain.L2d_llm_execution import get_llm_execution_service

router = APIRouter(prefix="/api/llm", tags=["LLM"])


class LLMModeRequest(BaseModel):
    """LLM模式切换请求模型"""
    mode: str


class LLMModeResponse(BaseModel):
    """LLM模式响应模型"""
    mode: str
    message: str


@router.get("/mode", response_model=LLMModeResponse)
async def get_llm_mode():
    """获取当前LLM运行模式"""
    service = get_llm_execution_service()
    current_mode = service.get_mode()
    return LLMModeResponse(
        mode=current_mode,
        message=f"当前模式: {'录制模式' if current_mode == 'record' else '回放模式'}"
    )


@router.post("/mode", response_model=LLMModeResponse)
async def set_llm_mode(request: LLMModeRequest):
    """设置LLM运行模式"""
    mode = request.mode
    
    if mode not in ['record', 'loopback']:
        raise HTTPException(status_code=400, detail="无效的模式，必须是 'record' 或 'loopback'")
    
    service = get_llm_execution_service()
    service.set_mode(mode)
    
    mode_name = '录制模式' if mode == 'record' else '回放模式'
    return LLMModeResponse(
        mode=mode,
        message=f"已切换到 {mode_name}"
    )
