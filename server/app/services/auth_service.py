"""
认证服务 - 微信登录 + JWT
"""
from datetime import datetime, timedelta
from jose import jwt
import httpx

from app.config import get_settings
from app.models.user import create_user_doc


class AuthService:
    """认证服务"""

    def __init__(self, db):
        self.db = db
        self.settings = get_settings()

    async def wechat_login(self, code: str) -> dict:
        """微信登录：code 换 openid，返回 JWT Token + 用户信息"""

        # 调用微信 code2Session 接口
        session_data = await self._code2session(code)
        openid = session_data.get("openid")
        unionid = session_data.get("unionid")

        if not openid:
            raise ValueError(f"微信登录失败: {session_data.get('errmsg', '未知错误')}")

        # 查找或创建用户
        user = await self.db.users.find_one({"openid": openid})
        is_new = user is None

        if is_new:
            user_doc = create_user_doc(openid=openid, unionid=unionid)
            result = await self.db.users.insert_one(user_doc)
            user = await self.db.users.find_one({"_id": result.inserted_id})
        else:
            # 更新最后登录时间
            await self.db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login_at": datetime.utcnow()}},
            )

        # 生成 JWT Token
        token = self._create_token(str(user["_id"]))

        return {
            "token": token,
            "expires_in": self.settings.JWT_EXPIRE_HOURS * 3600,
            "user": {
                "id": str(user["_id"]),
                "nickname": user.get("nickname", ""),
                "avatar_url": user.get("avatar_url", ""),
                "quota": {
                    "free_daily_used": user.get("quota", {}).get("free_daily_used", 0),
                    "paid_remaining": user.get("quota", {}).get("paid_remaining", 0),
                },
                "is_new_user": is_new,
            },
        }

    async def _code2session(self, code: str) -> dict:
        """调用微信 code2Session 接口"""
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            "appid": self.settings.WECHAT_APP_ID,
            "secret": self.settings.WECHAT_APP_SECRET,
            "js_code": code,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            return resp.json()

    def _create_token(self, user_id: str) -> str:
        """生成 JWT Token"""
        expire = datetime.utcnow() + timedelta(hours=self.settings.JWT_EXPIRE_HOURS)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM,
        )
