"""
JD解析路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user
from app.schemas.common import BaseResponse
from app.services.ai_service import AIService

router = APIRouter()


class JdParseRequest(BaseModel):
    """JD解析请求"""
    text: Optional[str] = None
    url: Optional[str] = None


@router.post("/parse", response_model=BaseResponse)
async def parse_jd(
    req: JdParseRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """解析JD文本"""
    if not req.text and not req.url:
        raise HTTPException(status_code=400, detail="请提供JD文本或链接")

    jd_text = req.text
    if req.url and not jd_text:
        # TODO: 抓取JD链接
        raise HTTPException(status_code=400, detail="JD链接抓取功能开发中，请直接粘贴JD文本")

    ai_service = AIService(db)
    result = await ai_service.parse_jd(jd_text)

    return BaseResponse(data=result)
