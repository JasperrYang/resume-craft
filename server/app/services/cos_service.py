"""
腾讯云 COS 文件存储服务
"""
from qcloud_cos import CosConfig, CosS3Client

from app.config import get_settings


class CosService:
    """腾讯云 COS 服务"""

    def __init__(self):
        settings = get_settings()
        config = CosConfig(
            Region=settings.COS_REGION,
            SecretId=settings.COS_SECRET_ID,
            SecretKey=settings.COS_SECRET_KEY,
        )
        self.client = CosS3Client(config)
        self.bucket = settings.COS_BUCKET
        self.region = settings.COS_REGION

    async def upload_file(self, key: str, content: bytes, content_type: str) -> str:
        """上传文件到 COS，返回访问 URL"""
        self.client.put_object(
            Bucket=self.bucket,
            Body=content,
            Key=key,
            ContentType=content_type,
        )
        return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{key}"

    async def download_file(self, key: str) -> bytes:
        """从 COS 下载文件"""
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=key,
        )
        return response["Body"].get_raw_stream().read()

    def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        """生成临时签名 URL"""
        return self.client.get_presigned_url(
            Method="GET",
            Bucket=self.bucket,
            Key=key,
            Expired=expires,
        )
