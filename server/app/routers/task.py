"""
优化任务路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId

from app.dependencies import get_db, get_current_user
from app.schemas.common import BaseResponse
from app.schemas.task import CreateTaskRequest, ChatRequest, ChatActionRequest, ExportRequest
from app.models.task import create_task_doc, create_chat_message_doc
from app.services.ai_service import AIService
from app.models.order import PRODUCTS

router = APIRouter()


@router.post("/create", response_model=BaseResponse)
async def create_task(
    req: CreateTaskRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """创建优化任务"""
    if not req.jd_text and not req.jd_url:
        raise HTTPException(status_code=400, detail="请提供JD文本或链接")

    # 校验简历存在且已解析
    resume = await db.resumes.find_one({
        "_id": ObjectId(req.resume_id),
        "user_id": user["_id"],
        "is_deleted": {"$ne": True},
    })
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    if resume.get("parse_status") != "completed":
        raise HTTPException(status_code=400, detail="简历尚未解析完成")

    # 检查免费次数
    quota = user.get("quota", {})
    today = datetime.utcnow().strftime("%Y-%m-%d")
    free_used = quota.get("free_daily_used", 0)
    free_date = quota.get("free_daily_date", "")
    paid_remaining = quota.get("paid_remaining", 0)

    # 重置每日免费次数
    if free_date != today:
        free_used = 0
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"quota.free_daily_used": 0, "quota.free_daily_date": today}},
        )

    has_free = free_used < 1
    has_paid = paid_remaining > 0

    if not has_free and not has_paid:
        raise HTTPException(status_code=403, detail="免费次数已用完，请购买优化次数")

    # JD文本处理
    jd_text = req.jd_text or ""
    if req.jd_url and not jd_text:
        # TODO: 抓取JD链接内容
        raise HTTPException(status_code=400, detail="JD链接抓取功能开发中，请直接粘贴JD文本")

    # 创建任务
    task_doc = create_task_doc(
        user_id=user["_id"],
        resume_id=ObjectId(req.resume_id),
        jd_text=jd_text,
        jd_url=req.jd_url,
    )

    # 免费用户直接使用免费次数，不标记付费
    if has_free:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$inc": {"quota.free_daily_used": 1}},
        )
    else:
        task_doc["is_paid"] = True
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$inc": {"quota.paid_remaining": -1}},
        )

    result = await db.tasks.insert_one(task_doc)
    task_id = str(result.inserted_id)

    # 更新用户统计
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$inc": {"stats.total_tasks": 1}},
    )

    # 异步触发AI改写（这里同步处理，生产环境应用消息队列）
    ai_service = AIService(db)
    try:
        await ai_service.analyze_and_rewrite(task_id=task_id)
    except Exception as e:
        await db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": "failed", "error_message": str(e)}},
        )

    return BaseResponse(data={
        "task_id": task_id,
        "status": "analyzing_jd",
        "is_paid": task_doc["is_paid"],
    })


@router.get("/{task_id}", response_model=BaseResponse)
async def get_task(
    task_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """获取任务结果"""
    task = await db.tasks.find_one({
        "_id": ObjectId(task_id),
        "user_id": user["_id"],
    })
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    is_paid = task.get("is_paid", False)
    jd = task.get("jd", {})
    result = task.get("result")

    response_data = {
        "id": str(task["_id"]),
        "status": task.get("status"),
        "is_paid": is_paid,
        "jd_summary": {
            "company": jd.get("analysis", {}).get("company") if jd.get("analysis") else None,
            "position": jd.get("analysis", {}).get("position") if jd.get("analysis") else None,
        },
        "created_at": task["created_at"].isoformat() if task.get("created_at") else "",
    }

    if result:
        match_score = result.get("match_score", {})
        if is_paid:
            # 付费用户看完整结果
            response_data["result"] = result
            response_data["jd"] = jd
        else:
            # 免费用户只看匹配度评分
            response_data["match_score"] = {
                "before": match_score.get("before"),
                "after": None,
                "details": None,
            }
            response_data["preview"] = {
                "changes_count": len(result.get("changes", [])),
                "missing_count": len(result.get("missing_items", [])),
            }
            response_data["need_pay"] = True
            response_data["pay_options"] = [
                {
                    "type": p["type"],
                    "name": p["name"],
                    "price": p["price"],
                    "quantity": p["quantity"],
                }
                for p in PRODUCTS.values()
            ]

        response_data["chat_rounds_used"] = task.get("chat_rounds_used", 0)
        response_data["chat_rounds_limit"] = task.get("chat_rounds_limit", 3)

    return BaseResponse(data=response_data)


@router.get("", response_model=BaseResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """获取任务列表"""
    query = {"user_id": user["_id"]}
    total = await db.tasks.count_documents(query)

    cursor = db.tasks.find(query).sort("created_at", -1)
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)

    items = []
    async for doc in cursor:
        jd = doc.get("jd", {})
        analysis = jd.get("analysis", {})
        result = doc.get("result", {})
        match_score = result.get("match_score", {}) if result else {}

        # 获取简历标题
        resume = await db.resumes.find_one({"_id": doc.get("resume_id")})

        items.append({
            "id": str(doc["_id"]),
            "resume_title": resume.get("title", "") if resume else "",
            "jd_summary": {
                "company": analysis.get("company") if analysis else None,
                "position": analysis.get("position") if analysis else None,
            },
            "match_score_before": match_score.get("before"),
            "match_score_after": match_score.get("after"),
            "status": doc.get("status"),
            "is_paid": doc.get("is_paid", False),
            "created_at": doc["created_at"].isoformat() if doc.get("created_at") else "",
        })

    return BaseResponse(data={
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/{task_id}/chat", response_model=BaseResponse)
async def chat_adjust(
    task_id: str,
    req: ChatRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """对话式调整"""
    task = await db.tasks.find_one({
        "_id": ObjectId(task_id),
        "user_id": user["_id"],
    })
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not task.get("is_paid"):
        raise HTTPException(status_code=403, detail="请先购买后使用对话调整功能")
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    # 检查对话次数
    used = task.get("chat_rounds_used", 0)
    limit = task.get("chat_rounds_limit", 3)
    if used >= limit:
        # 检查用户是否有额外对话次数
        user_chat_remaining = user.get("quota", {}).get("chat_remaining", 0)
        if user_chat_remaining <= 0:
            return BaseResponse(
                code=4005,
                message="对话调整次数已达上限，请购买额外次数",
                data={
                    "chat_rounds_used": used,
                    "chat_rounds_limit": limit,
                },
            )
        # 扣减额外对话次数
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$inc": {"quota.chat_remaining": -1}},
        )

    # 保存用户消息
    user_msg = create_chat_message_doc(
        task_id=ObjectId(task_id),
        user_id=user["_id"],
        role="user",
        content=req.message,
    )
    await db.chat_messages.insert_one(user_msg)

    # 获取历史对话
    history = []
    async for msg in db.chat_messages.find(
        {"task_id": ObjectId(task_id)}
    ).sort("created_at", 1):
        history.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # 调用AI进行对话调整
    ai_service = AIService(db)
    ai_result = await ai_service.chat_adjust(
        task_id=task_id,
        user_message=req.message,
        chat_history=history,
    )

    # 保存AI回复
    ai_msg = create_chat_message_doc(
        task_id=ObjectId(task_id),
        user_id=user["_id"],
        role="assistant",
        content=ai_result.get("reply", ""),
    )
    ai_msg["ai_response"] = ai_result
    ai_msg_result = await db.chat_messages.insert_one(ai_msg)

    # 更新对话轮次
    new_used = used + 1
    await db.tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"chat_rounds_used": new_used, "updated_at": datetime.utcnow()}},
    )

    return BaseResponse(data={
        "message_id": str(ai_msg_result.inserted_id),
        "reply": ai_result.get("reply", ""),
        "changes": ai_result.get("changes", []),
        "updated_match_score": ai_result.get("updated_match_score"),
        "needs_confirmation": ai_result.get("needs_confirmation", False),
        "chat_rounds_used": new_used,
        "chat_rounds_remaining": max(0, limit - new_used),
        "updated_full_text": ai_result.get("updated_full_text"),
    })


@router.put("/{task_id}/chat/{message_id}/action", response_model=BaseResponse)
async def chat_action(
    task_id: str,
    message_id: str,
    req: ChatActionRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """应用/撤销对话修改"""
    if req.action not in ("apply", "revert"):
        raise HTTPException(status_code=400, detail="action 必须是 apply 或 revert")

    msg = await db.chat_messages.find_one({
        "_id": ObjectId(message_id),
        "task_id": ObjectId(task_id),
        "role": "assistant",
    })
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    if req.action == "apply":
        await db.chat_messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"applied": True, "reverted": False}},
        )
        # 更新任务的优化结果
        ai_response = msg.get("ai_response", {})
        if ai_response.get("updated_full_text"):
            await db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "result.optimized_text": ai_response["updated_full_text"],
                        "result.match_score.after": ai_response.get("updated_match_score"),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
    else:
        await db.chat_messages.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"applied": False, "reverted": True}},
        )

    return BaseResponse(data={
        "action": req.action,
        "updated_match_score": msg.get("ai_response", {}).get("updated_match_score"),
    })


@router.post("/{task_id}/export", response_model=BaseResponse)
async def export_task(
    task_id: str,
    req: ExportRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """导出PDF"""
    task = await db.tasks.find_one({
        "_id": ObjectId(task_id),
        "user_id": user["_id"],
    })
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if not task.get("is_paid"):
        raise HTTPException(status_code=403, detail="请先购买后导出")
    if not task.get("result", {}).get("optimized_text"):
        raise HTTPException(status_code=400, detail="暂无可导出的优化结果")

    # TODO: 生成PDF并上传COS，返回下载链接
    # 当前返回模拟数据
    return BaseResponse(data={
        "download_url": "https://placeholder.com/export.pdf",
        "expires_in": 3600,
    })
