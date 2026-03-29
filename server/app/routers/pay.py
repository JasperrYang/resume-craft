"""
支付路由
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from bson import ObjectId

from app.dependencies import get_db, get_current_user
from app.schemas.common import BaseResponse
from app.schemas.order import CreateOrderRequest
from app.models.order import create_order_doc, PRODUCTS
from app.services.pay_service import PayService

router = APIRouter()


@router.get("/products", response_model=BaseResponse)
async def get_products():
    """获取商品列表"""
    products = [
        {
            "type": p["type"],
            "name": p["name"],
            "description": p["description"],
            "price": p["price"],
            "original_price": p["original_price"],
            "quantity": p["quantity"],
            "badge": p["badge"],
        }
        for p in PRODUCTS.values()
    ]
    return BaseResponse(data={"products": products})


@router.post("/create", response_model=BaseResponse)
async def create_order(
    req: CreateOrderRequest,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """创建支付订单"""
    if req.product_type not in PRODUCTS:
        raise HTTPException(status_code=400, detail="无效的商品类型")

    # 创建订单
    task_id = ObjectId(req.task_id) if req.task_id else None
    order_doc = create_order_doc(
        user_id=user["_id"],
        product_type=req.product_type,
        task_id=task_id,
    )
    result = await db.orders.insert_one(order_doc)
    order_id = str(result.inserted_id)

    # 调用微信支付统一下单
    pay_service = PayService()
    try:
        wx_pay_params = await pay_service.create_jsapi_order(
            order_no=order_doc["order_no"],
            amount=order_doc["amount"],
            description=PRODUCTS[req.product_type]["name"],
            openid=user["openid"],
        )
    except Exception as e:
        # 支付创建失败，更新订单状态
        await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "failed", "updated_at": datetime.utcnow()}},
        )
        raise HTTPException(status_code=500, detail=f"支付创建失败: {str(e)}")

    # 更新 prepay_id
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"wechat_pay.prepay_id": wx_pay_params.get("prepay_id", "")}},
    )

    return BaseResponse(data={
        "order_id": order_id,
        "order_no": order_doc["order_no"],
        "amount": order_doc["amount"],
        "wx_pay_params": wx_pay_params,
    })


@router.post("/notify")
async def pay_notify(request: Request, db=Depends(get_db)):
    """微信支付回调通知（无需认证）"""
    body = await request.body()
    headers = dict(request.headers)

    pay_service = PayService()

    # 验签并解密
    try:
        notify_data = pay_service.verify_and_decrypt_notify(body, headers)
    except Exception:
        return {"code": "FAIL", "message": "签名验证失败"}

    order_no = notify_data.get("out_trade_no")
    transaction_id = notify_data.get("transaction_id")
    trade_state = notify_data.get("trade_state")

    if trade_state != "SUCCESS":
        return {"code": "SUCCESS", "message": ""}

    # 查找订单
    order = await db.orders.find_one({"order_no": order_no})
    if not order:
        return {"code": "FAIL", "message": "订单不存在"}

    # 幂等：已支付的订单跳过
    if order["status"] == "paid":
        return {"code": "SUCCESS", "message": ""}

    # 金额校验
    paid_amount = notify_data.get("amount", {}).get("total", 0)
    if paid_amount != order["amount"]:
        return {"code": "FAIL", "message": "金额不一致"}

    now = datetime.utcnow()

    # 更新订单
    await db.orders.update_one(
        {"_id": order["_id"]},
        {
            "$set": {
                "status": "paid",
                "wechat_pay.transaction_id": transaction_id,
                "wechat_pay.pay_time": now,
                "updated_at": now,
            }
        },
    )

    # 增加用户付费次数
    product = PRODUCTS.get(order["product"]["type"], {})
    quantity = product.get("quantity", 1)
    chat_quota = product.get("chat_quota", 3)

    await db.users.update_one(
        {"_id": order["user_id"]},
        {
            "$inc": {
                "quota.paid_remaining": quantity,
                "quota.chat_remaining": chat_quota,
                "stats.total_spent": order["amount"],
            }
        },
    )

    # 如果关联了任务，标记任务为已付费
    if order.get("task_id"):
        await db.tasks.update_one(
            {"_id": order["task_id"]},
            {"$set": {"is_paid": True, "order_id": order["_id"]}},
        )

    return {"code": "SUCCESS", "message": ""}


@router.get("/order/{order_id}", response_model=BaseResponse)
async def get_order(
    order_id: str,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """查询订单状态"""
    order = await db.orders.find_one({
        "_id": ObjectId(order_id),
        "user_id": user["_id"],
    })
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return BaseResponse(data={
        "order_id": str(order["_id"]),
        "order_no": order["order_no"],
        "product": order["product"],
        "amount": order["amount"],
        "status": order["status"],
        "created_at": order["created_at"].isoformat(),
        "paid_at": order["wechat_pay"]["pay_time"].isoformat() if order["wechat_pay"].get("pay_time") else None,
    })
