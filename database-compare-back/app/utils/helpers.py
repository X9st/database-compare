"""辅助函数工具类"""
import uuid
import hashlib
import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal
import json


def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """生成短ID"""
    return uuid.uuid4().hex[:length]


def hash_string(text: str) -> str:
    """计算字符串的MD5哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间"""
    if dt is None:
        return ""
    return dt.strftime(fmt)


def parse_datetime(text: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """解析日期时间字符串"""
    if not text:
        return None
    try:
        return datetime.strptime(text, fmt)
    except ValueError:
        return None


def format_duration(seconds: int) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}时{minutes}分{secs}秒"


def format_number(num: Union[int, float], precision: int = 2) -> str:
    """格式化数字，添加千位分隔符"""
    if isinstance(num, float):
        return f"{num:,.{precision}f}"
    return f"{num:,}"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - len(suffix)] + suffix


def safe_json_dumps(obj: Any, default_value: str = "{}") -> str:
    """安全的JSON序列化"""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default_value


def safe_json_loads(text: str, default_value: Any = None) -> Any:
    """安全的JSON反序列化"""
    if not text:
        return default_value
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default_value


def convert_to_serializable(obj: Any) -> Any:
    """将对象转换为可JSON序列化的格式"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    if isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    return str(obj)


def camel_to_snake(name: str) -> str:
    """驼峰命名转下划线命名"""
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', name).lower()


def snake_to_camel(name: str) -> str:
    """下划线命名转驼峰命名"""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def merge_dicts(base: Dict, updates: Dict, deep: bool = True) -> Dict:
    """合并字典"""
    result = base.copy()
    for key, value in updates.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List) -> List:
    """扁平化嵌套列表"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def remove_none_values(d: Dict) -> Dict:
    """移除字典中值为None的键"""
    return {k: v for k, v in d.items() if v is not None}


def get_nested_value(d: Dict, keys: List[str], default: Any = None) -> Any:
    """获取嵌套字典中的值"""
    result = d
    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default
    return result


def set_nested_value(d: Dict, keys: List[str], value: Any) -> None:
    """设置嵌套字典中的值"""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def compare_versions(v1: str, v2: str) -> int:
    """比较版本号，返回 -1/0/1 分别表示 v1<v2/v1=v2/v1>v2"""
    parts1 = [int(x) for x in v1.split('.')]
    parts2 = [int(x) for x in v2.split('.')]
    
    # 补齐长度
    max_len = max(len(parts1), len(parts2))
    parts1.extend([0] * (max_len - len(parts1)))
    parts2.extend([0] * (max_len - len(parts2)))
    
    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        if p1 > p2:
            return 1
    return 0


def mask_sensitive(text: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """脱敏敏感信息"""
    if not text:
        return ""
    if len(text) <= visible_chars * 2:
        return mask_char * len(text)
    return text[:visible_chars] + mask_char * (len(text) - visible_chars * 2) + text[-visible_chars:]


def validate_table_name(name: str) -> bool:
    """验证表名是否合法"""
    if not name:
        return False
    # 只允许字母、数字、下划线，且不能以数字开头
    pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
    return bool(pattern.match(name))


def normalize_db_type(db_type: str) -> str:
    """标准化数据库类型名称"""
    mapping = {
        'mysql': 'mysql',
        'mariadb': 'mysql',
        'postgres': 'postgresql',
        'postgresql': 'postgresql',
        'pg': 'postgresql',
        'oracle': 'oracle',
        'sqlserver': 'sqlserver',
        'mssql': 'sqlserver',
        'dm': 'dm',
        'dameng': 'dm',
        '达梦': 'dm',
        'inceptor': 'inceptor',
        'transwarp': 'inceptor',
    }
    return mapping.get(db_type.lower(), db_type.lower())


def calculate_percentage(part: int, total: int, precision: int = 2) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return round(part / total * 100, precision)
