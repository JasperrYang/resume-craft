"""
任务相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    """创建优化任务"""
    resume_id: str
    jd_text: Optional[str] = None
    jd_url: Optional[str] = None


class ChatRequest(BaseModel):
    """对话调整请求"""
    message: str


class ChatActionRequest(BaseModel):
    """应用/撤销对话修改"""
    action: str  # "apply" | "revert"


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = "pdf"
    template: str = "classic"


class SkillWeight(BaseModel):
    """技能权重"""
    name: str
    weight: int


class KeywordWeight(BaseModel):
    """关键词权重"""
    word: str
    weight: int
    category: str


class JdAnalysis(BaseModel):
    """JD分析结果"""
    company: Optional[str] = None
    position: Optional[str] = None
    location: Optional[str] = None
    required_skills: List[SkillWeight] = []
    preferred_skills: List[SkillWeight] = []
    responsibilities: List[str] = []
    requirements: List[str] = []
    keywords: List[KeywordWeight] = []


class ChangeItem(BaseModel):
    """改动项"""
    section: str
    section_type: str = ""
    original: str
    optimized: str
    reason: str
    matched_keywords: List[str] = []


class MissingItem(BaseModel):
    """缺失项"""
    requirement: str
    importance: str = "medium"
    suggestion: str


class MatchScore(BaseModel):
    """匹配度评分"""
    before: int
    after: Optional[int] = None
    details: Optional[dict] = None


class TaskResult(BaseModel):
    """任务结果"""
    match_score: MatchScore
    optimized_text: Optional[str] = None
    changes: List[ChangeItem] = []
    missing_items: List[MissingItem] = []
    tips: List[str] = []


class ChatChange(BaseModel):
    """对话修改项"""
    section: str
    before: str
    after: str


class ChatResponse(BaseModel):
    """对话调整响应"""
    message_id: str
    reply: str
    changes: List[ChatChange] = []
    updated_match_score: Optional[int] = None
    needs_confirmation: bool = False
    chat_rounds_used: int = 0
    chat_rounds_remaining: int = 0
    updated_full_text: Optional[str] = None
