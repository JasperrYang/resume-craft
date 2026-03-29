"""
优化任务数据模型
"""
from datetime import datetime


def create_task_doc(user_id, resume_id, jd_text: str, jd_url: str = None) -> dict:
    """创建优化任务文档"""
    now = datetime.utcnow()
    return {
        "user_id": user_id,
        "resume_id": resume_id,
        "jd": {
            "raw_text": jd_text,
            "source_url": jd_url,
            "analysis": None,
        },
        "result": None,
        "chat_rounds_used": 0,
        "chat_rounds_limit": 3,
        "exports": [],
        "status": "pending",
        "error_message": None,
        "is_paid": False,
        "order_id": None,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }


def create_chat_message_doc(task_id, user_id, role: str, content: str) -> dict:
    """创建对话消息文档"""
    return {
        "task_id": task_id,
        "user_id": user_id,
        "role": role,
        "content": content,
        "ai_response": None,
        "applied": False,
        "reverted": False,
        "created_at": datetime.utcnow(),
    }
