"""
Project Routes - 项目管理API路由
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.create_project import CreateProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.update_project import UpdateProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.delete_project import DeleteProject
from services.L3_scenario_coordination.L3c_ui_scenarios.ProjectManager.list_projects import ListProjects

router = APIRouter()

@router.post("/")
async def create_project(data: Dict[str, Any] = None):
    """创建项目"""
    try:
        if data is None:
            data = {}
        manager = CreateProject()
        result = manager.execute(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/default")
async def create_default_project():
    """创建默认项目"""
    try:
        data = {
            "name": "默认项目",
            "description": "系统自动创建的默认项目"
        }
        manager = CreateProject()
        result = manager.execute(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_projects():
    """获取项目列表"""
    try:
        manager = ListProjects()
        result = manager.execute()
        return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    try:
        manager = ListProjects()
        projects = manager.execute()
        projects = projects if isinstance(projects, list) else []
        project = next((p for p in projects if p.get("project_id") == project_id), None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}")
async def update_project(project_id: str, data: Dict[str, Any]):
    """更新项目"""
    try:
        manager = UpdateProject()
        result = manager.execute(project_id, data)
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/batch")
async def batch_delete_projects(data: Dict[str, Any] = Body(...)):
    """批量删除项目"""
    try:
        project_ids = data.get("project_ids", [])
        results = {"success": [], "failed": []}
        manager = DeleteProject()
        for project_id in project_ids:
            try:
                result = manager.execute(project_id)
                if result.get("success"):
                    results["success"].append(project_id)
                else:
                    results["failed"].append(project_id)
            except:
                results["failed"].append(project_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    try:
        manager = DeleteProject()
        result = manager.execute(project_id)
        if not result.get("success"):
            raise HTTPException(status_code=404, detail="Project not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))