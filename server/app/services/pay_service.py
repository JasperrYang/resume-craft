"""
微信支付服务 - API v3
"""
import time
import json
import uuid
import hashlib
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import httpx

from app.config import get_settings


class PayService:
    """微信支付服务（API v3）"""

    def __init__(self):
        self.settings = get_settings()
        self.mch_id = self.settings.WECHAT_PAY_MCH_ID
        self.api_key_v3 = self.settings.WECHAT_PAY_API_KEY_V3
        self.serial_no = self.settings.WECHAT_PAY_SERIAL_NO
        self._private_key = None

    @property
    def private_key(self):
        """加载商户私钥"""
        if self._private_key is None:
            with open(self.settings.WECHAT_PAY_PRIVATE_KEY_PATH, "rb") as f:
                self._private_key = serialization.load_pem_private_key(f.read(), password=None)
        return self._private_key

    async def create_jsapi_order(
        self,
        order_no: str,
        amount: int,
        description: str,
        openid: str,
    ) -> dict:
        """JSAPI下单 - 小程序支付"""
        url = "https://api.mch.weixin.qq.com/v3/pay/transactions/jsapi"
        body = {
            "appid": self.settings.WECHAT_APP_ID,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": order_no,
            "notify_url": self.settings.WECHAT_PAY_NOTIFY_URL,
            "amount": {
                "total": amount,
                "currency": "CNY",
            },
            "payer": {
                "openid": openid,
            },
        }

        headers = self._build_auth_header("POST", "/v3/pay/transactions/jsapi", body)

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            result = resp.json()

        prepay_id = result.get("prepay_id", "")

        # 生成前端调起支付的参数
        return self._build_pay_params(prepay_id)

    def _build_pay_params(self, prepay_id: str) -> dict:
        """构建前端调起支付的参数"""
        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex
        package = f"prepay_id={prepay_id}"

        # 签名
        sign_str = f"{self.settings.WECHAT_APP_ID}\n{timestamp}\n{nonce_str}\n{package}\n"
        signature = self.private_key.sign(
            sign_str.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        pay_sign = base64.b64encode(signature).decode("utf-8")

        return {
            "prepay_id": prepay_id,
            "timeStamp": timestamp,
            "nonceStr": nonce_str,
            "package": package,
            "signType": "RSA",
            "paySign": pay_sign,
        }

    def _build_auth_header(self, method: str, url_path: str, body: dict) -> dict:
        """构建 Authorization 请求头"""
        timestamp = str(int(time.time()))
        nonce_str = uuid.uuid4().hex
        body_str = json.dumps(body) if body else ""

        sign_str = f"{method}\n{url_path}\n{timestamp}\n{nonce_str}\n{body_str}\n"
        signature = self.private_key.sign(
            sign_str.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        sign_b64 = base64.b64encode(signature).decode("utf-8")

        auth = (
            f'WECHATPAY2-SHA256-RSA2048 '
            f'mchid="{self.mch_id}",'
            f'nonce_str="{nonce_str}",'
            f'timestamp="{timestamp}",'
            f'serial_no="{self.serial_no}",'
            f'signature="{sign_b64}"'
        )

        return {
            "Authorization": auth,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def verify_and_decrypt_notify(self, body: bytes, headers: dict) -> dict:
        """验签并解密微信支付回调通知"""
        # TODO: 生产环境需验证微信平台证书签名
        # 当前简化处理：直接解密

        notify = json.loads(body)
        resource = notify.get("resource", {})

        # AES-256-GCM 解密
        nonce = resource.get("nonce", "").encode("utf-8")
        ciphertext = base64.b64decode(resource.get("ciphertext", ""))
        associated_data = resource.get("associated_data", "").encode("utf-8")

        aesgcm = AESGCM(self.api_key_v3.encode("utf-8"))
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)

        return json.loads(plaintext)
