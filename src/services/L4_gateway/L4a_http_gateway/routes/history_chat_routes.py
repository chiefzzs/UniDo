"""
History Chat Routes - WebSocket缓存历史消息API路由
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from services.L2_domain.L2b_memory_state.websocket_cache_service import get_websocket_cache_service

router = APIRouter()


@router.get("/history-chat/{session_id}")
async def get_history_chat(
    session_id: str,
    limit: int = Query(100, ge=1, le=1000, description="返回消息数量限制"),
    offset: int = Query(0, ge=0, description="分页偏移")
):
    """
    获取WebSocket缓存的历史消息（用于前端展示）
    
    消息通过WebSocket推送时实时缓存到内存，切换会话时从缓存回放。
    消息不持久化到磁盘，仅在服务运行期间有效。
    
    Args:
        session_id: 会话ID
        limit: 返回消息数量限制
        offset: 分页偏移
        
    Returns:
        历史消息列表，按时间排序
    """
    try:
        cache_service = get_websocket_cache_service()
        messages = cache_service.get_messages(
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "data": [msg.to_dict() for msg in messages],
            "count": len(messages),
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history-chat/{session_id}")
async def clear_history_chat(session_id: str):
    """
    清空会话的WebSocket缓存消息
    
    Args:
        session_id: 会话ID
        
    Returns:
        操作结果
    """
    try:
        cache_service = get_websocket_cache_service()
        cache_service.clear_session(session_id)
        
        return {
            "status": "success",
            "message": f"会话 {session_id} 的缓存历史已清空"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))