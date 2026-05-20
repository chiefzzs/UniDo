class EventTypes:
    PROJECT_CREATED = 'project.created'
    PROJECT_UPDATED = 'project.updated'
    PROJECT_DELETED = 'project.deleted'

    SESSION_CREATED = 'session.created'
    SESSION_UPDATED = 'session.updated'
    SESSION_DELETED = 'session.deleted'

    DIALOG_CREATED = 'dialog.created'
    DIALOG_UPDATED = 'dialog.updated'
    DIALOG_DELETED = 'dialog.deleted'
    DIALOG_COMPLETED = 'dialog.completed'

    MESSAGE_CREATED = 'message.created'
    MESSAGE_UPDATED = 'message.updated'
    MESSAGE_DELETED = 'message.deleted'

    LLM_REQUEST_SENT = 'llm.request_sent'
    LLM_RESPONSE_RECEIVED = 'llm.response_received'
    LLM_STREAM_CHUNK = 'llm.stream_chunk'
    LLM_ERROR = 'llm.error'
    LLM_CALL_FAILED = 'llm.call_failed'
    LLM_CALL_COMPLETED = 'llm.call_completed'
    LLM_RESPONSE_CLASSIFIED = 'llm.response_classified'

    TOOL_REGISTERED = 'tool.registered'
    TOOL_UNREGISTERED = 'tool.unregistered'
    TOOL_EXECUTION_STARTED = 'tool.execution_started'
    TOOL_EXECUTION_COMPLETED = 'tool.execution_completed'
    TOOL_EXECUTION_FAILED = 'tool.execution_failed'
    TOOL_CALL_STARTED = 'tool.call_started'
    TOOL_CALL_COMPLETED = 'tool.call_completed'
    TOOL_CALL_FAILED = 'tool.call_failed'
    TOOL_CALL_CANCELLED = 'tool.call_cancelled'
    
    # 工具执行实时输出事件（流式输出）
    TOOL_EXECUTION_OUTPUT = 'tool.execution_output'
    TOOL_EXECUTION_OUTPUT_END = 'tool.execution_output_end'

    SKILL_REGISTERED = 'skill.registered'
    SKILL_UNREGISTERED = 'skill.unregistered'

    ROUND_STARTED = 'round.started'
    ROUND_COMPLETED = 'round.completed'

    TASK_STARTED = 'task.started'
    TASK_COMPLETED = 'task.completed'
    TASK_UPDATED = 'task.updated'
    TASK_FAILED = 'task.failed'
    
    # 任务组相关事件
    TASK_GROUP_CREATED = 'task_group.created'
    TASK_GROUP_UPDATED = 'task_group.updated'
    TASK_GROUP_DELETED = 'task_group.deleted'
    TASK_GROUP_COMPLETED = 'task_group.completed'
    
    # 客户端消息事件
    CLIENT_MESSAGE_RECEIVED = 'client.message_received'
    CLIENT_MESSAGE_SENT = 'client.message_sent'
    
    # 系统状态事件
    SYSTEM_STATUS_CHANGED = 'system.status_changed'
