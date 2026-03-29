"""
简历相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel


class BasicInfo(BaseModel):
    """基本信息"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    birth_year: Optional[int] = None
    gender: Optional[str] = None


class Education(BaseModel):
    """教育经历"""
    school: Optional[str] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    highlights: List[str] = []


class Metric(BaseModel):
    """量化指标"""
    text: str
    type: str = "growth"


class Experience(BaseModel):
    """工作经历"""
    company: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    keywords: List[str] = []
    metrics: List[Metric] = []
    responsibilities: List[str] = []
    achievements: List[str] = []


class Project(BaseModel):
    """项目经历"""
    name: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []
    highlights: List[str] = []


class Skill(BaseModel):
    """技能"""
    name: str
    category: str = "skill"
    level: Optional[str] = None


class Certification(BaseModel):
    """证书"""
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None


class AdditionalInfo(BaseModel):
    """其他信息"""
    self_assessment: Optional[str] = None
    languages: List[str] = []
    others: Optional[str] = None


class ParsedData(BaseModel):
    """简历结构化数据"""
    basic_info: BasicInfo = BasicInfo()
    education: List[Education] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    skills: List[Skill] = []
    certifications: List[Certification] = []
    additional: AdditionalInfo = AdditionalInfo()


class ConfirmResumeRequest(BaseModel):
    """确认/修正简历解析结果"""
    parsed_data: ParsedData


class ResumeListItem(BaseModel):
    """简历列表项"""
    id: str
    title: str
    source_type: str
    parse_status: str
    is_confirmed: bool
    basic_info_summary: Optional[dict] = None
    created_at: str
