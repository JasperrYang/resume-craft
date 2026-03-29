"""
通用工具函数
"""
from bson import ObjectId


def to_str_id(doc: dict) -> dict:
    """将 MongoDB 文档中的 ObjectId 转为字符串"""
    if doc is None:
        return doc
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc
