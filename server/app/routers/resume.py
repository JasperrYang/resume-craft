"""
简历管理路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from bson import ObjectId

from app.dependencies import get_db, get_current_user
from app.schemas.common import BaseResponse
from app.schemas.resume import ConfirmResumeRequest
from app.models.resume import create_resume_doc
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post("/upload", response_model=BaseResponse)
async def upload_resume(
    file: UploadFile = File(...),
    title: str = Form(None),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """上传简历文件"""
    # 校验文件类型
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持PDF和DOCX文件")

    # 校验文件大小（10MB）
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")

    # 生成默认标题
    if not title:
        title = f"我的简历-{datetime.now().strftime('%Y%m%d')}"

    service = ResumeService(db)
    result = await service.upload_and_parse(
        user_id=user["_id"],
        file_content=content,
        file_name=file.filename,
        content_type=file.content_type,
        title=title,
    )

    return BaseResponse(data=result)


@router.post("/{resume_id}/parse", response_model=BaseResponse)
async def parse_resume(
    resume_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """触发简历解析"""
    service = ResumeService(db)
    result = await service.trigger_parse(
        user_id=user["_id"],
        resume_id=resume_id,
    )
    return BaseResponse(data=result)


@router.get("/{resume_id}", response_model=BaseResponse)
async def get_resume(
    resume_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """获取简历详情"""
    resume = await db.resumes.find_one({
        "_id": ObjectId(resume_id),
        "user_id": user["_id"],
        "is_deleted": {"$ne": True},
    })
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    resume["id"] = str(resume.pop("_id"))
    resume["user_id"] = str(resume["user_id"])
    # 时间格式化
    for key in ["created_at", "updated_at"]:
        if resume.get(key):
            resume[key] = resume[key].isoformat()

    return BaseResponse(data=resume)


@router.put("/{resume_id}/confirm", response_model=BaseResponse)
async def confirm_resume(
    resume_id: str,
    req: ConfirmResumeRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """确认/修正简历解析结果"""
    result = await db.resumes.update_one(
        {"_id": ObjectId(resume_id), "user_id": user["_id"]},
        {
            "$set": {
                "parsed_data": req.parsed_data.model_dump(),
                "is_confirmed": True,
                "updated_at": datetime.utcnow(),
            }
        },
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="简历不存在")

    return BaseResponse(data={
        "resume_id": resume_id,
        "is_confirmed": True,
    })


@router.get("", response_model=BaseResponse)
async def list_resumes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """获取简历列表"""
    query = {"user_id": user["_id"], "is_deleted": {"$ne": True}}
    total = await db.resumes.count_documents(query)

    cursor = db.resumes.find(query).sort("created_at", -1)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)

    items = []
    async for doc in cursor:
        parsed = doc.get("parsed_data", {})
        basic = parsed.get("basic_info", {})
        exp = parsed.get("experience", [])

        items.append({
            "id": str(doc["_id"]),
            "title": doc.get("title", ""),
            "source_type": doc.get("source_type", ""),
            "parse_status": doc.get("parse_status", ""),
            "is_confirmed": doc.get("is_confirmed", False),
            "basic_info_summary": {
                "name": basic.get("name"),
                "latest_company": exp[0].get("company") if exp else None,
                "latest_title": exp[0].get("title") if exp else None,
            },
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else "",
        })

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.delete("/{resume_id}", response_model=BaseResponse)
async def delete_resume(
    resume_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """删除简历（软删除）"""
    result = await db.resumes.update_one(
        {"_id": ObjectId(resume_id), "user_id": user["_id"]},
        {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="简历不存在")

    return BaseResponse(message="删除成功")
