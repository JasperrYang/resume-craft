"""
简历数据模型
"""
from datetime import datetime


def create_resume_doc(
    user_id,
    title: str,
    source_type: str,
    source_file: dict = None,
) -> dict:
    """创建简历文档"""
    now = datetime.utcnow()
    return {
        "user_id": user_id,
        "title": title,
        "source_type": source_type,
        "source_file": source_file or {},
        "raw_text": "",
        "parsed_data": {
            "basic_info": {
                "name": None,
                "phone": None,
                "email": None,
                "location": None,
                "birth_year": None,
                "gender": None,
            },
            "education": [],
            "experience": [],
            "projects": [],
            "skills": [],
            "certifications": [],
            "additional": {
                "self_assessment": None,
                "languages": [],
                "others": None,
            },
        },
        "parse_status": "pending",
        "parse_error": None,
        "is_confirmed": False,
        "is_deleted": False,
        "created_at": now,
        "updated_at": now,
    }
