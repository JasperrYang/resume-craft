"""
腾讯云 OCR 文字识别服务
"""
import base64
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.ocr.v20181119 import ocr_client, models

from app.config import get_settings


class OcrService:
    """腾讯云 OCR 服务"""

    def __init__(self):
        settings = get_settings()
        cred = credential.Credential(settings.OCR_SECRET_ID, settings.OCR_SECRET_KEY)

        http_profile = HttpProfile()
        http_profile.endpoint = "ocr.tencentcloudapi.com"

        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile

        self.client = ocr_client.OcrClient(cred, "ap-guangzhou", client_profile)

    async def recognize(self, file_content: bytes, source_type: str) -> str:
        """识别文件文本内容"""
        if source_type == "upload_pdf":
            return await self._recognize_pdf(file_content)
        elif source_type == "upload_docx":
            return await self._recognize_docx(file_content)
        else:
            raise ValueError(f"不支持的文件类型: {source_type}")

    async def _recognize_pdf(self, content: bytes) -> str:
        """PDF 文字识别"""
        # 使用通用印刷体识别（高精度）
        file_base64 = base64.b64encode(content).decode("utf-8")

        req = models.GeneralAccurateOCRRequest()
        req.ImageBase64 = file_base64
        req.IsPdf = True
        req.PdfPageNumber = 0  # 0表示识别所有页

        resp = self.client.GeneralAccurateOCR(req)

        # 拼接识别结果
        texts = []
        if resp.TextDetections:
            for detection in resp.TextDetections:
                texts.append(detection.DetectedText)

        return "\n".join(texts)

    async def _recognize_docx(self, content: bytes) -> str:
        """DOCX 文本提取（直接解析XML，不走OCR）"""
        import zipfile
        import io
        import xml.etree.ElementTree as ET

        # DOCX 本质是 ZIP 包，直接解析 XML 提取文本
        texts = []
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # 读取 word/document.xml
            if "word/document.xml" in zf.namelist():
                with zf.open("word/document.xml") as f:
                    tree = ET.parse(f)
                    root = tree.getroot()

                    # Word XML 命名空间
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

                    for paragraph in root.iter(f"{{{ns['w']}}}p"):
                        para_text = []
                        for run in paragraph.iter(f"{{{ns['w']}}}t"):
                            if run.text:
                                para_text.append(run.text)
                        if para_text:
                            texts.append("".join(para_text))

        return "\n".join(texts)
