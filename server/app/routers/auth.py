"""
认证路由
"""
from fastapi import APIRouter, Depends

from app.dependencies import get_db, get_current_user
from app.schemas.common import BaseResponse
from app.schemas.user import LoginRequest, UpdateProfileRequest, LoginResponse, UserInfo, QuotaInfo, UserStats
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=BaseResponse)
async def login(req: LoginRequest, db=Depends(get_db)):
    """微信登录"""
    service = AuthService(db)
    result = await service.wechat_login(req.code)
    return BaseResponse(data=result)


@router.get("/profile", response_model=BaseResponse)
async def get_profile(user=Depends(get_current_user)):
    """获取用户信息"""
    user_info = UserInfo(
        id=str(user["_id"]),
        nickname=user.get("nickname", ""),
        avatar_url=user.get("avatar_url", ""),
        quota=QuotaInfo(**user.get("quota", {})),
        stats=UserStats(**user.get("stats", {})),
    )
    return BaseResponse(data=user_info.model_dump())


@router.put("/profile", response_model=BaseResponse)
async def update_profile(
    req: UpdateProfileRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """更新用户信息"""
    update_data = {}
    if req.nickname is not None:
        update_data["nickname"] = req.nickname
    if req.avatar_url is not None:
        update_data["avatar_url"] = req.avatar_url

    if update_data:
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": update_data},
        )

    return BaseResponse(data={
        "id": str(user["_id"]),
        "nickname": req.nickname or user.get("nickname", ""),
        "avatar_url": req.avatar_url or user.get("avatar_url", ""),
    })
