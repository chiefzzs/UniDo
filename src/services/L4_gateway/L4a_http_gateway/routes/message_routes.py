"""
Message Routes - 消息管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.L3_scenario_coordination.L3c_ui_scenarios.MessageManager.message_manager import MessageManager
from services.L3_scenario_coordination.L3c_ui_scenarios.DialogManager.dialog_manager import DialogManager
from services.L3_scenario_coordination.L3a_task_coordination.dialogue_service import DialogueService

router = APIRouter()

@router.post("/send")
async def send_message(data: Dict[str, Any]):
    """发送消息"""
    try:
        session_id = data.get("session_id")
        user_input = data.get("content")
        
        if not session_id or not user_input:
            raise HTTPException(status_code=400, detail="session_id and content are required")
        
        # 使用DialogManager处理用户输入
        dialog_manager = DialogManager()
        result = dialog_manager.process_user_input(session_id, user_input)
        
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dialog_id}/user")
async def create_user_message(dialog_id: str, data: Dict[str, Any]):
    """创建用户消息"""
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        
        manager = MessageManager()
        result = manager.create_user_message(dialog_id, content)
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dialog_id}/assistant")
async def create_assistant_message(dialog_id: str, data: Dict[str, Any]):
    """创建助手消息"""
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        
        manager = MessageManager()
        result = manager.create_assistant_message(dialog_id, content)
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dialog_id}/system")
async def create_system_message(dialog_id: str, data: Dict[str, Any]):
    """创建系统消息"""
    try:
        content = data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="content is required")
        
        manager = MessageManager()
        result = manager.create_system_message(dialog_id, content)
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{dialog_id}")
async def get_messages(dialog_id: str):
    """获取对话消息列表"""
    try:
        manager = MessageManager()
        result = manager.list_messages(dialog_id)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== WebSocket缓存历史消息API ==========

from typing import List, Optional
from fastapi import Query
from services.L2_domain.L2b_memory_state.websocket_cache_service import get_websocket_cache_service

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