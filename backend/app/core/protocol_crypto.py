import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _build_fernet() -> Fernet:
    # 协议凭据需要可逆加密用于运行时连接 broker，密钥从服务端 SECRET_KEY 派生。
    digest = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_protocol_secret(value: str) -> str:
    return _build_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_protocol_secret(value: str | None) -> str | None:
    if not value:
        return None
    return _build_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
