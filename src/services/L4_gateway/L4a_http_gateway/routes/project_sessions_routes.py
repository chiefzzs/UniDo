"""
Project Sessions Routes - 项目会话管理API路由

处理 /api/projects/{project_id}/sessions 路由
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.create_session import CreateSession
from services.L3_scenario_coordination.L3c_ui_scenarios.SessionManager.list_sessions import ListSessions

router = APIRouter()

@router.get("/")
async def get_project_sessions(project_id: str):
    """获取项目的会话列表"""
    try:
        manager = ListSessions()
        sessions = manager.execute()
        sessions = sessions if isinstance(sessions, list) else []
        # 过滤属于该项目的会话
        project_sessions = [s for s in sessions if s.get("project_id") == project_id]
        return project_sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_project_session(project_id: str, data: Dict[str, Any] = None):
    """为项目创建会话"""
    try:
        if data is None:
            data = {}
        # 添加project_id到数据中
        data["project_id"] = project_id
        manager = CreateSession()
        result = manager.execute(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
