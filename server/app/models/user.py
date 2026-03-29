"""
用户数据模型
"""
from datetime import datetime


def create_user_doc(openid: str, unionid: str = None) -> dict:
    """创建用户文档"""
    now = datetime.utcnow()
    return {
        "openid": openid,
        "unionid": unionid,
        "nickname": "",
        "avatar_url": "",
        "phone": None,
        "quota": {
            "free_daily_used": 0,
            "free_daily_date": "",
            "paid_remaining": 0,
            "chat_remaining": 0,
        },
        "stats": {
            "total_tasks": 0,
            "total_resumes": 0,
            "total_spent": 0,
        },
        "created_at": now,
        "updated_at": now,
        "last_login_at": now,
    }
