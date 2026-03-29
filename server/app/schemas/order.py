"""
支付相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel


class CreateOrderRequest(BaseModel):
    """创建支付订单"""
    product_type: str  # "single" | "pack_5" | "pack_20"
    task_id: Optional[str] = None


class ProductInfo(BaseModel):
    """商品信息"""
    type: str
    name: str
    description: str
    price: int
    original_price: Optional[int] = None
    quantity: int
    badge: Optional[str] = None


class WxPayParams(BaseModel):
    """微信支付参数（前端调起支付用）"""
    timeStamp: str
    nonceStr: str
    package: str
    signType: str = "RSA"
    paySign: str


class CreateOrderResponse(BaseModel):
    """创建订单响应"""
    order_id: str
    order_no: str
    amount: int
    wx_pay_params: WxPayParams


class OrderInfo(BaseModel):
    """订单信息"""
    order_id: str
    order_no: str
    product: dict
    amount: int
    status: str
    created_at: str
    paid_at: Optional[str] = None
