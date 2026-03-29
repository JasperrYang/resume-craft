"""
用户相关 Schema
"""
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """微信登录请求"""
    code: str


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class QuotaInfo(BaseModel):
    """配额信息"""
    free_daily_used: int = 0
    paid_remaining: int = 0
    chat_remaining: int = 0


class UserStats(BaseModel):
    """用户统计"""
    total_tasks: int = 0
    total_resumes: int = 0


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    nickname: str = ""
    avatar_url: str = ""
    quota: QuotaInfo = QuotaInfo()
    stats: UserStats = UserStats()
    is_new_user: bool = False


class LoginResponse(BaseModel):
    """登录响应"""
    token: str
    expires_in: int = 7200
    user: UserInfo
