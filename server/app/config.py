"""
ResumeCraft 配置管理
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件读取"""

    # 应用配置
    APP_NAME: str = "ResumeCraft"
    APP_ENV: str = "development"
    DEBUG: bool = True
    MOCK_MODE: bool = False  # Mock模式：不依赖数据库和第三方服务
    SECRET_KEY: str = "change-me-in-production"
    API_PREFIX: str = "/api/v1"

    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "resume_craft"

    # 微信小程序
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # 微信支付
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_API_KEY_V3: str = ""
    WECHAT_PAY_SERIAL_NO: str = ""
    WECHAT_PAY_PRIVATE_KEY_PATH: str = "./certs/apiclient_key.pem"
    WECHAT_PAY_NOTIFY_URL: str = ""

    # 腾讯云 COS
    COS_SECRET_ID: str = ""
    COS_SECRET_KEY: str = ""
    COS_REGION: str = "ap-guangzhou"
    COS_BUCKET: str = ""

    # 腾讯云 OCR
    OCR_SECRET_ID: str = ""
    OCR_SECRET_KEY: str = ""

    # 腾讯云智能体平台
    AI_PLATFORM_APP_ID: str = ""
    AI_PLATFORM_API_KEY: str = ""
    AI_PLATFORM_BASE_URL: str = ""

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 2

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
