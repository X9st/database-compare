"""加密工具"""
from cryptography.fernet import Fernet
import base64
import os

# 从环境变量或生成密钥
_KEY = os.environ.get('ENCRYPTION_KEY')
if _KEY:
    _KEY = _KEY.encode()
else:
    _KEY = Fernet.generate_key()

_cipher = Fernet(_KEY)


def encrypt(plain_text: str) -> str:
    """加密字符串"""
    if not plain_text:
        return ""
    encrypted = _cipher.encrypt(plain_text.encode('utf-8'))
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt(encrypted_text: str) -> str:
    """解密字符串"""
    if not encrypted_text:
        return ""
    try:
        encrypted = base64.b64decode(encrypted_text.encode('utf-8'))
        return _cipher.decrypt(encrypted).decode('utf-8')
    except Exception:
        # 如果解密失败，可能是明文密码
        return encrypted_text
