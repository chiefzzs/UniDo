from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

class TaskStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Task:
    task_id: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    session_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    error_message: Optional[str] = None
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class TaskGroup:
    task_group_id: str
    parent_task_id: str
    subtasks: List[Task] = field(default_factory=list)
    execution_mode: str = "sequential"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

@dataclass
class DialogueResponse:
    session_id: str
    task_id: str
    status: str
    content: str
    created_at: datetime = field(default_factory=datetime.now)
