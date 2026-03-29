"""
支付订单数据模型
"""
import time
import random
from datetime import datetime, timedelta


def generate_order_no() -> str:
    """生成商户订单号：RC + 时间戳 + 4位随机数"""
    timestamp = time.strftime("%Y%m%d%H%M%S")
    rand = random.randint(1000, 9999)
    return f"RC{timestamp}{rand}"


# 商品定义
PRODUCTS = {
    "single": {
        "type": "single",
        "name": "单次优化",
        "description": "1次完整改写 + 3轮对话调整 + PDF导出",
        "price": 390,
        "original_price": None,
        "quantity": 1,
        "chat_quota": 3,
        "badge": None,
    },
    "pack_5": {
        "type": "pack_5",
        "name": "5次优化包",
        "description": "5次完整优化，每次含3轮对话调整",
        "price": 1490,
        "original_price": 1950,
        "quantity": 5,
        "chat_quota": 15,
        "badge": "最受欢迎",
    },
    "pack_20": {
        "type": "pack_20",
        "name": "20次优化包",
        "description": "20次完整优化，每次含3轮对话调整",
        "price": 4990,
        "original_price": 7800,
        "quantity": 20,
        "chat_quota": 60,
        "badge": "最划算",
    },
}


def create_order_doc(user_id, product_type: str, task_id=None) -> dict:
    """创建订单文档"""
    product = PRODUCTS.get(product_type)
    if not product:
        raise ValueError(f"无效的商品类型: {product_type}")

    now = datetime.utcnow()
    return {
        "user_id": user_id,
        "order_no": generate_order_no(),
        "product": {
            "type": product["type"],
            "name": product["name"],
            "quantity": product["quantity"],
            "unit_price": product["price"] // product["quantity"],
        },
        "amount": product["price"],
        "wechat_pay": {
            "prepay_id": None,
            "transaction_id": None,
            "pay_time": None,
        },
        "status": "pending",
        "task_id": task_id,
        "refund": None,
        "created_at": now,
        "updated_at": now,
        "expired_at": now + timedelta(minutes=30),
    }
