"""
Mock 路由 - 开发调试用，不依赖数据库和第三方服务
当 MOCK_MODE=true 时，覆盖所有路由返回模拟数据
"""
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Query
from typing import Optional

from app.schemas.common import BaseResponse

router = APIRouter()

# ========== Mock 数据 ==========

MOCK_USER = {
    "id": "mock_user_001",
    "nickname": "测试用户",
    "avatar_url": "",
    "quota": {
        "free_daily_used": 0,
        "paid_remaining": 5,
        "chat_remaining": 15,
    },
    "stats": {
        "total_tasks": 3,
        "total_resumes": 2,
    },
    "is_new_user": False,
}

MOCK_RESUME_PARSED = {
    "basic_info": {
        "name": "张三",
        "phone": "138****1234",
        "email": "zhangsan@example.com",
        "location": "深圳",
        "birth_year": 1995,
        "gender": "男",
    },
    "education": [
        {
            "school": "华南理工大学",
            "degree": "本科",
            "major": "计算机科学与技术",
            "start_date": "2013-09",
            "end_date": "2017-06",
            "gpa": "3.6/4.0",
            "highlights": ["优秀毕业生"],
        }
    ],
    "experience": [
        {
            "company": "腾讯",
            "title": "高级后端工程师",
            "department": "微信支付",
            "start_date": "2021-03",
            "end_date": "至今",
            "is_current": True,
            "description": "负责微信支付核心交易系统的架构设计与开发，主导完成支付链路性能优化项目。",
            "keywords": ["Python", "Go", "微服务", "高并发", "MySQL"],
            "metrics": [
                {"text": "系统QPS从5000提升至20000", "type": "growth"},
                {"text": "P99延迟从200ms降至50ms", "type": "efficiency"},
            ],
            "responsibilities": ["核心交易系统架构设计", "团队Code Review", "性能优化"],
            "achievements": ["主导系统重构，性能提升300%", "获得年度技术突破奖"],
        },
        {
            "company": "字节跳动",
            "title": "后端工程师",
            "department": "电商",
            "start_date": "2017-07",
            "end_date": "2021-02",
            "is_current": False,
            "description": "参与抖音电商后端系统开发，负责订单和库存模块。",
            "keywords": ["Go", "Redis", "Kafka", "微服务"],
            "metrics": [
                {"text": "日均处理订单量100万+", "type": "scale"},
            ],
            "responsibilities": ["订单系统开发", "库存服务设计"],
            "achievements": ["设计的库存扣减方案零超卖"],
        },
    ],
    "projects": [
        {
            "name": "支付链路优化",
            "role": "技术负责人",
            "start_date": "2023-01",
            "end_date": "2023-06",
            "description": "对核心支付链路进行全面性能优化，包括数据库优化、缓存策略、异步化改造。",
            "tech_stack": ["Go", "MySQL", "Redis", "Kafka"],
            "highlights": ["QPS提升4倍", "P99降低75%"],
        }
    ],
    "skills": [
        {"name": "Python", "category": "language", "level": "精通"},
        {"name": "Go", "category": "language", "level": "精通"},
        {"name": "MySQL", "category": "tool", "level": "熟练"},
        {"name": "Redis", "category": "tool", "level": "熟练"},
        {"name": "Kafka", "category": "tool", "level": "熟练"},
        {"name": "Docker", "category": "tool", "level": "熟练"},
        {"name": "微服务架构", "category": "skill", "level": "精通"},
    ],
    "certifications": [],
    "additional": {
        "self_assessment": "8年后端开发经验，擅长高并发系统设计",
        "languages": ["英语CET-6"],
        "others": None,
    },
}

MOCK_JD_ANALYSIS = {
    "company": "字节跳动",
    "position": "高级后端工程师",
    "location": "北京",
    "salary_range": "40-70K",
    "required_skills": [
        {"name": "Go", "weight": 9},
        {"name": "微服务", "weight": 8},
        {"name": "高并发", "weight": 8},
        {"name": "分布式系统", "weight": 7},
    ],
    "preferred_skills": [
        {"name": "Kubernetes", "weight": 6},
        {"name": "大数据", "weight": 5},
    ],
    "responsibilities": [
        "负责核心交易系统设计与开发",
        "主导系统架构优化和性能调优",
        "指导初中级工程师，推动技术规范落地",
    ],
    "requirements": [
        "本科及以上学历，计算机相关专业",
        "5年以上后端开发经验",
    ],
    "keywords": [
        {"word": "Go", "weight": 9, "category": "language"},
        {"word": "微服务", "weight": 8, "category": "skill"},
        {"word": "高并发", "weight": 8, "category": "skill"},
        {"word": "分布式系统", "weight": 7, "category": "skill"},
        {"word": "团队管理", "weight": 7, "category": "soft_skill"},
        {"word": "Kubernetes", "weight": 6, "category": "tool"},
        {"word": "MySQL", "weight": 6, "category": "tool"},
    ],
}

MOCK_TASK_RESULT = {
    "match_score": {
        "before": 42,
        "after": 85,
        "details": {
            "skills_match": 82,
            "experience_match": 88,
            "keyword_match": 90,
            "education_match": 80,
        },
    },
    "optimized_text": """张三
高级后端工程师 | 深圳 | 138****1234 | zhangsan@example.com

【工作经历】

腾讯 · 微信支付 | 高级后端工程师 | 2021.03 - 至今
• 主导微信支付核心交易系统架构设计与开发，基于Go微服务架构实现高并发交易处理，系统QPS从5000提升至20000（4倍增长）
• 负责支付链路全面性能优化，通过数据库索引优化、Redis缓存策略、Kafka异步化改造，将P99延迟从200ms降至50ms（降低75%）
• 带领3人小组完成核心模块重构，建立Code Review规范和技术文档体系，团队代码质量显著提升
• 荣获年度技术突破奖

字节跳动 · 电商 | 后端工程师 | 2017.07 - 2021.02
• 负责抖音电商订单和库存微服务系统设计与开发，日均处理订单量100万+
• 设计并实现高并发库存扣减方案（Redis预扣减 + MySQL最终一致），实现零超卖
• 基于Go + Kafka构建订单事件驱动架构，支撑大促期间10倍流量峰值

【教育背景】
华南理工大学 | 计算机科学与技术 | 本科 | 2013 - 2017 | GPA 3.6/4.0

【技能】
Go(精通) Python(精通) 微服务架构(精通) MySQL Redis Kafka Docker""",
    "changes": [
        {
            "section": "工作经历-腾讯",
            "section_type": "experience",
            "original": "负责微信支付核心交易系统的架构设计与开发，主导完成支付链路性能优化项目。",
            "optimized": "主导微信支付核心交易系统架构设计与开发，基于Go微服务架构实现高并发交易处理，系统QPS从5000提升至20000（4倍增长）",
            "reason": "JD要求Go和高并发经验，将技术栈和量化指标前置，突出与JD的匹配度",
            "matched_keywords": ["Go", "微服务", "高并发"],
        },
        {
            "section": "工作经历-腾讯(性能优化)",
            "section_type": "experience",
            "original": "主导系统重构，性能提升300%",
            "optimized": "负责支付链路全面性能优化，通过数据库索引优化、Redis缓存策略、Kafka异步化改造，将P99延迟从200ms降至50ms（降低75%）",
            "reason": "JD要求性能调优能力，用STAR法则展开具体方案和数据",
            "matched_keywords": ["高并发", "分布式系统"],
        },
        {
            "section": "工作经历-腾讯(团队)",
            "section_type": "experience",
            "original": "团队Code Review",
            "optimized": "带领3人小组完成核心模块重构，建立Code Review规范和技术文档体系",
            "reason": "JD要求指导初中级工程师，补充团队管理相关描述",
            "matched_keywords": ["团队管理"],
        },
        {
            "section": "工作经历-字节跳动",
            "section_type": "experience",
            "original": "参与抖音电商后端系统开发，负责订单和库存模块。",
            "optimized": "负责抖音电商订单和库存微服务系统设计与开发，日均处理订单量100万+",
            "reason": "将'参与'改为'负责'，补充规模数据，突出微服务关键词",
            "matched_keywords": ["微服务", "Go"],
        },
    ],
    "missing_items": [
        {
            "requirement": "Kubernetes容器化部署经验",
            "importance": "medium",
            "suggestion": "您使用Docker但未提及K8s经验，如果有相关实践建议补充",
        },
        {
            "requirement": "大数据处理经验",
            "importance": "low",
            "suggestion": "JD中为加分项，非必须。如有Spark/Flink等经验可补充",
        },
    ],
    "tips": [
        "建议将Go相关经历描述提前，JD对Go的权重最高",
        "可以在技能栏补充分布式系统相关描述",
        "自我评价部分可以针对JD要求重写",
    ],
}


# ========== Mock 路由 ==========

# --- 认证 ---
@router.post("/auth/login", response_model=BaseResponse)
async def mock_login(req: dict = None):
    """Mock 微信登录"""
    return BaseResponse(data={
        "token": "mock_token_for_dev_testing_only",
        "expires_in": 7200,
        "user": MOCK_USER,
    })


@router.get("/auth/profile", response_model=BaseResponse)
async def mock_profile():
    """Mock 获取用户信息"""
    return BaseResponse(data=MOCK_USER)


@router.put("/auth/profile", response_model=BaseResponse)
async def mock_update_profile():
    """Mock 更新用户信息"""
    return BaseResponse(data={
        "id": "mock_user_001",
        "nickname": "测试用户",
        "avatar_url": "",
    })


# --- 简历 ---
@router.post("/resume/upload", response_model=BaseResponse)
async def mock_upload_resume(
    file: UploadFile = File(None),
    title: str = Form(None),
):
    """Mock 上传简历"""
    return BaseResponse(data={
        "resume_id": "mock_resume_001",
        "title": title or f"我的简历-{datetime.now().strftime('%Y%m%d')}",
        "source_file": {
            "file_name": file.filename if file else "mock_resume.pdf",
            "file_size": 524288,
        },
        "parse_status": "completed",
    })


@router.post("/resume/{resume_id}/parse", response_model=BaseResponse)
async def mock_parse_resume(resume_id: str):
    """Mock 触发解析"""
    return BaseResponse(data={
        "resume_id": resume_id,
        "parse_status": "completed",
    })


@router.get("/resume/{resume_id}", response_model=BaseResponse)
async def mock_get_resume(resume_id: str):
    """Mock 获取简历详情"""
    return BaseResponse(data={
        "id": resume_id,
        "title": "我的简历-20260329",
        "source_type": "upload_pdf",
        "parse_status": "completed",
        "is_confirmed": False,
        "parsed_data": MOCK_RESUME_PARSED,
        "created_at": "2026-03-29T10:00:00",
        "updated_at": "2026-03-29T10:00:00",
    })


@router.put("/resume/{resume_id}/confirm", response_model=BaseResponse)
async def mock_confirm_resume(resume_id: str):
    """Mock 确认简历"""
    return BaseResponse(data={
        "resume_id": resume_id,
        "is_confirmed": True,
    })


@router.get("/resume", response_model=BaseResponse)
async def mock_list_resumes(
    page: int = Query(1),
    page_size: int = Query(20),
):
    """Mock 简历列表"""
    return BaseResponse(data={
        "list": [
            {
                "id": "mock_resume_001",
                "title": "我的简历-20260329",
                "source_type": "upload_pdf",
                "parse_status": "completed",
                "is_confirmed": True,
                "basic_info_summary": {
                    "name": "张三",
                    "latest_company": "腾讯",
                    "latest_title": "高级后端工程师",
                },
                "created_at": "2026-03-29T10:00:00",
            },
            {
                "id": "mock_resume_002",
                "title": "我的简历-旧版",
                "source_type": "upload_docx",
                "parse_status": "completed",
                "is_confirmed": True,
                "basic_info_summary": {
                    "name": "张三",
                    "latest_company": "字节跳动",
                    "latest_title": "后端工程师",
                },
                "created_at": "2026-03-15T08:00:00",
            },
        ],
        "total": 2,
        "page": page,
        "page_size": page_size,
    })


@router.delete("/resume/{resume_id}", response_model=BaseResponse)
async def mock_delete_resume(resume_id: str):
    """Mock 删除简历"""
    return BaseResponse(message="删除成功")


# --- JD ---
@router.post("/jd/parse", response_model=BaseResponse)
async def mock_parse_jd():
    """Mock JD解析"""
    return BaseResponse(data=MOCK_JD_ANALYSIS)


# --- 任务 ---
@router.post("/task/create", response_model=BaseResponse)
async def mock_create_task():
    """Mock 创建任务"""
    return BaseResponse(data={
        "task_id": "mock_task_001",
        "status": "completed",
        "is_paid": True,
    })


@router.get("/task/{task_id}", response_model=BaseResponse)
async def mock_get_task(task_id: str):
    """Mock 获取任务结果"""
    return BaseResponse(data={
        "id": task_id,
        "status": "completed",
        "is_paid": True,
        "jd": {
            "raw_text": "...",
            "analysis": MOCK_JD_ANALYSIS,
        },
        "jd_summary": {
            "company": "字节跳动",
            "position": "高级后端工程师",
        },
        "result": MOCK_TASK_RESULT,
        "chat_rounds_used": 0,
        "chat_rounds_limit": 3,
        "created_at": "2026-03-29T10:10:00",
        "completed_at": "2026-03-29T10:10:30",
    })


@router.get("/task", response_model=BaseResponse)
async def mock_list_tasks(
    page: int = Query(1),
    page_size: int = Query(20),
):
    """Mock 任务列表"""
    return BaseResponse(data={
        "list": [
            {
                "id": "mock_task_001",
                "resume_title": "我的简历-20260329",
                "jd_summary": {"company": "字节跳动", "position": "高级后端工程师"},
                "match_score_before": 42,
                "match_score_after": 85,
                "status": "completed",
                "is_paid": True,
                "created_at": "2026-03-29T10:10:00",
            },
            {
                "id": "mock_task_002",
                "resume_title": "我的简历-旧版",
                "jd_summary": {"company": "阿里巴巴", "position": "技术专家"},
                "match_score_before": 35,
                "match_score_after": 78,
                "status": "completed",
                "is_paid": True,
                "created_at": "2026-03-28T14:00:00",
            },
            {
                "id": "mock_task_003",
                "resume_title": "我的简历-20260329",
                "jd_summary": {"company": "美团", "position": "后端开发"},
                "match_score_before": 50,
                "match_score_after": None,
                "status": "completed",
                "is_paid": False,
                "created_at": "2026-03-27T09:00:00",
            },
        ],
        "total": 3,
        "page": page,
        "page_size": page_size,
    })


@router.post("/task/{task_id}/chat", response_model=BaseResponse)
async def mock_chat(task_id: str, req: dict = None):
    """Mock 对话调整"""
    message = req.get("message", "") if req else ""
    return BaseResponse(data={
        "message_id": f"mock_msg_{datetime.now().strftime('%H%M%S')}",
        "reply": f"已根据你的要求「{message}」进行了调整。主要修改了工作经历第一段的表述方式，突出了相关能力。",
        "changes": [
            {
                "section": "工作经历-腾讯",
                "before": "主导微信支付核心交易系统架构设计与开发",
                "after": f"主导微信支付核心交易系统架构设计与开发，{message}方面经验丰富",
            }
        ],
        "updated_match_score": 87,
        "needs_confirmation": False,
        "chat_rounds_used": 1,
        "chat_rounds_remaining": 2,
        "updated_full_text": MOCK_TASK_RESULT["optimized_text"],
    })


@router.put("/task/{task_id}/chat/{message_id}/action", response_model=BaseResponse)
async def mock_chat_action(task_id: str, message_id: str):
    """Mock 应用/撤销"""
    return BaseResponse(data={
        "action": "apply",
        "updated_match_score": 87,
    })


@router.post("/task/{task_id}/export", response_model=BaseResponse)
async def mock_export(task_id: str):
    """Mock 导出"""
    return BaseResponse(data={
        "download_url": "https://example.com/mock-resume.pdf",
        "expires_in": 3600,
    })


# --- 支付 ---
# 商品列表走真实路由（不依赖数据库），这里提供备用
@router.post("/pay/create", response_model=BaseResponse)
async def mock_create_order():
    """Mock 创建订单"""
    return BaseResponse(data={
        "order_id": "mock_order_001",
        "order_no": "RC20260329110000001",
        "amount": 390,
        "wx_pay_params": {
            "timeStamp": "1711699200",
            "nonceStr": "mock_nonce",
            "package": "prepay_id=mock_prepay_id",
            "signType": "RSA",
            "paySign": "mock_sign",
        },
    })


@router.get("/pay/order/{order_id}", response_model=BaseResponse)
async def mock_get_order(order_id: str):
    """Mock 查询订单"""
    return BaseResponse(data={
        "order_id": order_id,
        "order_no": "RC20260329110000001",
        "product": {"type": "single", "name": "单次优化", "quantity": 1},
        "amount": 390,
        "status": "paid",
        "created_at": "2026-03-29T11:00:00",
        "paid_at": "2026-03-29T11:00:15",
    })
