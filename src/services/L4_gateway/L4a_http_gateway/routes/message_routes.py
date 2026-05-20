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