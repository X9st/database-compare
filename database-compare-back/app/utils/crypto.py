"""加密工具"""
from cryptography.fernet import Fernet
import base64
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_key_file() -> Path:
    """解析密钥文件路径，保证未配置时使用项目固定目录。"""
    configured = os.environ.get("ENCRYPTION_KEY_FILE")
    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            candidate = PROJECT_ROOT / candidate
        return candidate
    return PROJECT_ROOT / "data/encryption.key"


DEFAULT_KEY_FILE = _resolve_key_file()


def _load_or_create_key() -> bytes:
    """加载或生成稳定加密密钥。"""
    env_key = os.environ.get("ENCRYPTION_KEY")
    if env_key:
        return env_key.encode()

    key_file = DEFAULT_KEY_FILE
    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        key = key_file.read_bytes().strip()
        if key:
            return key

    key = Fernet.generate_key()
    key_file.write_bytes(key)
    try:
        key_file.chmod(0o600)
    except OSError:
        # Windows 等平台不支持 chmod 时忽略
        pass
    return key


_KEY = _load_or_create_key()
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
    except Exception as exc:
        raise ValueError("密码解密失败，请检查 ENCRYPTION_KEY 是否与历史数据一致") from exc
