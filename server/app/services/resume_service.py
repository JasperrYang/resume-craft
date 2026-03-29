"""
简历解析服务 - 文件上传 + OCR + AI结构化提取
"""
from datetime import datetime
from bson import ObjectId

from app.models.resume import create_resume_doc
from app.services.cos_service import CosService
from app.services.ocr_service import OcrService
from app.services.ai_service import AIService


class ResumeService:
    """简历解析服务"""

    def __init__(self, db):
        self.db = db
        self.cos = CosService()
        self.ocr = OcrService()
        self.ai = AIService(db)

    async def upload_and_parse(
        self,
        user_id,
        file_content: bytes,
        file_name: str,
        content_type: str,
        title: str,
    ) -> dict:
        """上传简历并触发解析"""

        # 确定文件类型
        if content_type == "application/pdf":
            source_type = "upload_pdf"
            ext = "pdf"
        else:
            source_type = "upload_docx"
            ext = "docx"

        # 上传到 COS
        cos_key = f"resumes/{user_id}/{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        cos_url = await self.cos.upload_file(
            key=cos_key,
            content=file_content,
            content_type=content_type,
        )

        # 创建简历记录
        resume_doc = create_resume_doc(
            user_id=user_id,
            title=title,
            source_type=source_type,
            source_file={
                "cos_key": cos_key,
                "cos_url": cos_url,
                "file_name": file_name,
                "file_size": len(file_content),
                "mime_type": content_type,
            },
        )
        result = await self.db.resumes.insert_one(resume_doc)
        resume_id = str(result.inserted_id)

        # 更新用户统计
        await self.db.users.update_one(
            {"_id": user_id},
            {"$inc": {"stats.total_resumes": 1}},
        )

        # 异步触发解析（当前同步处理）
        try:
            await self._parse_resume(resume_id, file_content, source_type)
        except Exception as e:
            await self.db.resumes.update_one(
                {"_id": ObjectId(resume_id)},
                {
                    "$set": {
                        "parse_status": "failed",
                        "parse_error": str(e),
                        "updated_at": datetime.utcnow(),
                    }
                },
            )

        return {
            "resume_id": resume_id,
            "title": title,
            "source_file": {
                "file_name": file_name,
                "file_size": len(file_content),
            },
            "parse_status": "parsing",
        }

    async def trigger_parse(self, user_id, resume_id: str) -> dict:
        """手动触发解析"""
        resume = await self.db.resumes.find_one({
            "_id": ObjectId(resume_id),
            "user_id": user_id,
        })
        if not resume:
            raise ValueError("简历不存在")

        # 从COS重新下载文件
        cos_key = resume.get("source_file", {}).get("cos_key")
        if cos_key:
            file_content = await self.cos.download_file(cos_key)
            await self._parse_resume(resume_id, file_content, resume["source_type"])

        return {
            "resume_id": resume_id,
            "parse_status": "parsing",
        }

    async def _parse_resume(
        self,
        resume_id: str,
        file_content: bytes,
        source_type: str,
    ) -> None:
        """执行简历解析流程"""

        # 更新状态为解析中
        await self.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {"$set": {"parse_status": "parsing", "updated_at": datetime.utcnow()}},
        )

        # Step 1: OCR 识别文本
        raw_text = await self.ocr.recognize(file_content, source_type)

        # Step 2: AI 结构化提取
        parsed_data = await self.ai.parse_resume_text(raw_text)

        # Step 3: 保存结果
        await self.db.resumes.update_one(
            {"_id": ObjectId(resume_id)},
            {
                "$set": {
                    "raw_text": raw_text,
                    "parsed_data": parsed_data,
                    "parse_status": "completed",
                    "updated_at": datetime.utcnow(),
                }
            },
        )
