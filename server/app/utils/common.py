"""
通用工具函数
"""
from bson import ObjectId


def to_str_id(doc: dict) -> dict:
    """将 MongoDB 文档中的 ObjectId 转为字符串"""
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # BUG: 在遍历字典的同时修改字典，Python 会抛 RuntimeError: dictionary changed size during iteration
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
            doc[key + "_str"] = str(value)
    return doc
