"""
Session Routes - 会话管理API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.create_session import CreateSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.update_session import UpdateSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.delete_session import DeleteSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.archive_session import ArchiveSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.list_sessions import ListSessions

router = APIRouter()

@router.post("/")
async def create_session(data: Dict[str, Any] = None):
    """创建会话"""
    try:
        if data is None:
            data = {}
        manager = CreateSession()
        result = manager.execute(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_sessions():
    """获取会话列表"""
    try:
        manager = ListSessions()
        result = manager.execute()
        return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    try:
        manager = ListSessions()
        sessions = manager.execute()
        sessions = sessions if isinstance(sessions, list) else []
        session = next((s for s in sessions if s.get("session_id") == session_id), None)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{session_id}")
async def update_session(session_id: str, data: Dict[str, Any]):
    """更新会话"""
    try:
        manager = UpdateSession()
        result = manager.execute(session_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    try:
        manager = DeleteSession()
        result = manager.execute(session_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/archive")
async def archive_session(session_id: str):
    """归档会话"""
    try:
        manager = ArchiveSession()
        result = manager.execute(session_id)
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))