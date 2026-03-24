"""数据比对器"""
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from datetime import datetime
from app.core.connector.base import BaseConnector


class DataDiffType(str, Enum):
    ROW_COUNT_DIFF = "row_count_diff"
    ROW_MISSING_IN_TARGET = "row_missing_in_target"
    ROW_EXTRA_IN_TARGET = "row_extra_in_target"
    VALUE_DIFF = "value_diff"
    NULL_DIFF = "null_diff"


@dataclass
class DataDiff:
    """数据差异"""
    table_name: str
    primary_key: Dict[str, Any]
    diff_type: DataDiffType
    diff_columns: List[str]
    source_values: Optional[Dict[str, Any]] = None
    target_values: Optional[Dict[str, Any]] = None


class DataComparator:
    """数据比对器"""
    
    def __init__(self, source_conn: BaseConnector, target_conn: BaseConnector,
                 options: Dict[str, Any] = None):
        self.source_conn = source_conn
        self.target_conn = target_conn
        self.options = options or {}
        
        # 比对选项
        self.float_precision = self.options.get('float_precision', 6)
        self.ignore_case = self.options.get('ignore_case', False)
        self.trim_whitespace = self.options.get('trim_whitespace', True)
        self.datetime_precision = self.options.get('datetime_precision', 'second')
        self.page_size = self.options.get('page_size', 10000)
        self.skip_large_fields = self.options.get('skip_large_fields', False)
        self.large_field_types = {'text', 'longtext', 'clob', 'blob', 'longblob', 'bytea'}
    
    def compare_row_count(self, table_name: str, 
                          target_table: str = None,
                          where_clause: str = None) -> Optional[DataDiff]:
        """比对行数"""
        target_table = target_table or table_name
        
        source_count = self.source_conn.get_row_count(table_name, where_clause)
        target_count = self.target_conn.get_row_count(target_table, where_clause)
        
        if source_count != target_count:
            return DataDiff(
                table_name=table_name,
                primary_key={},
                diff_type=DataDiffType.ROW_COUNT_DIFF,
                diff_columns=[],
                source_values={'row_count': source_count},
                target_values={'row_count': target_count}
            )
        return None
    
    def compare_data(self, table_name: str, primary_keys: List[str],
                     target_table: str = None,
                     column_mapping: Dict[str, str] = None,
                     where_clause: str = None,
                     max_diffs: int = 1000) -> List[DataDiff]:
        """比对数据"""
        target_table = target_table or table_name
        column_mapping = column_mapping or {}
        diffs = []
        
        # 获取需要比对的字段
        source_columns = self.source_conn.get_columns(table_name)
        compare_columns = [
            c.name for c in source_columns 
            if not (self.skip_large_fields and c.data_type.lower() in self.large_field_types)
        ]
        
        # 构建排序字段
        order_by = primary_keys.copy()
        
        offset = 0
        while len(diffs) < max_diffs:
            # 分页获取源数据
            source_data = self.source_conn.fetch_data(
                table_name, compare_columns, where_clause, order_by, offset, self.page_size
            )
            
            if not source_data:
                break
            
            # 获取对应的目标数据
            pk_values = [self._extract_pk(row, primary_keys) for row in source_data]
            target_data = self._fetch_target_by_pks(
                target_table, pk_values, primary_keys, compare_columns, column_mapping
            )
            target_map = {self._pk_to_key(self._extract_pk(row, primary_keys)): row 
                          for row in target_data}
            
            # 比对每一行
            for source_row in source_data:
                if len(diffs) >= max_diffs:
                    break
                    
                pk = self._extract_pk(source_row, primary_keys)
                pk_key = self._pk_to_key(pk)
                
                if pk_key not in target_map:
                    # 目标库缺少该行
                    diffs.append(DataDiff(
                        table_name=table_name,
                        primary_key=pk,
                        diff_type=DataDiffType.ROW_MISSING_IN_TARGET,
                        diff_columns=[],
                        source_values=self._serialize_row(source_row)
                    ))
                else:
                    # 比对字段值
                    target_row = target_map[pk_key]
                    diff_columns = []
                    
                    for col in compare_columns:
                        target_col = column_mapping.get(col, col)
                        if not self._values_equal(source_row.get(col), target_row.get(target_col)):
                            diff_columns.append(col)
                    
                    if diff_columns:
                        # 判断是否为空值差异
                        is_null_diff = any(
                            (source_row.get(c) is None) != (target_row.get(column_mapping.get(c, c)) is None)
                            for c in diff_columns
                        )
                        diffs.append(DataDiff(
                            table_name=table_name,
                            primary_key=pk,
                            diff_type=DataDiffType.NULL_DIFF if is_null_diff else DataDiffType.VALUE_DIFF,
                            diff_columns=diff_columns,
                            source_values={c: self._serialize_value(source_row.get(c)) for c in diff_columns},
                            target_values={c: self._serialize_value(target_row.get(column_mapping.get(c, c))) for c in diff_columns}
                        ))
            
            offset += self.page_size
        
        return diffs
    
    def _values_equal(self, source_val: Any, target_val: Any) -> bool:
        """比较两个值是否相等"""
        # 都为None
        if source_val is None and target_val is None:
            return True
        
        # 其中一个为None
        if source_val is None or target_val is None:
            return False
        
        # 浮点数比较
        if isinstance(source_val, (float, Decimal)) or isinstance(target_val, (float, Decimal)):
            try:
                return abs(float(source_val) - float(target_val)) < 10 ** (-self.float_precision)
            except:
                return str(source_val) == str(target_val)
        
        # 字符串比较
        if isinstance(source_val, str) and isinstance(target_val, str):
            s1, s2 = source_val, target_val
            if self.trim_whitespace:
                s1, s2 = s1.strip(), s2.strip()
            if self.ignore_case:
                s1, s2 = s1.lower(), s2.lower()
            return s1 == s2
        
        # 日期时间比较
        if isinstance(source_val, datetime) and isinstance(target_val, datetime):
            if self.datetime_precision == 'second':
                return source_val.replace(microsecond=0) == target_val.replace(microsecond=0)
            return source_val == target_val
        
        # 默认比较
        return source_val == target_val
    
    def _extract_pk(self, row: Dict[str, Any], pk_columns: List[str]) -> Dict[str, Any]:
        """提取主键值"""
        return {col: row.get(col) for col in pk_columns}
    
    def _pk_to_key(self, pk: Dict[str, Any]) -> str:
        """主键转为字符串key"""
        return '|'.join(str(v) for v in pk.values())
    
    def _serialize_value(self, value: Any) -> Any:
        """序列化值为JSON兼容格式"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, bytes):
            return value.hex()
        return value
    
    def _serialize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """序列化整行数据"""
        return {k: self._serialize_value(v) for k, v in row.items()}
    
    def _fetch_target_by_pks(self, table_name: str, pk_values: List[Dict],
                             pk_columns: List[str], columns: List[str],
                             column_mapping: Dict[str, str]) -> List[Dict]:
        """根据主键批量获取目标数据"""
        if not pk_values:
            return []
        
        # 构建IN查询条件
        if len(pk_columns) == 1:
            col = pk_columns[0]
            values = [pk[col] for pk in pk_values]
            # 处理不同类型的值
            formatted_values = []
            for v in values:
                if isinstance(v, str):
                    formatted_values.append(f"'{v}'")
                else:
                    formatted_values.append(str(v))
            where = f"{col} IN ({','.join(formatted_values)})"
        else:
            # 复合主键
            conditions = []
            for pk in pk_values:
                cond_parts = []
                for k, v in pk.items():
                    if isinstance(v, str):
                        cond_parts.append(f"{k} = '{v}'")
                    else:
                        cond_parts.append(f"{k} = {v}")
                conditions.append(f"({' AND '.join(cond_parts)})")
            where = ' OR '.join(conditions)
        
        target_columns = [column_mapping.get(c, c) for c in columns]
        return self.target_conn.fetch_data(table_name, target_columns, where)
