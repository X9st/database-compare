"""数据比对器"""
from typing import List, Dict, Any, Optional
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
    PRIMARY_KEY_MISSING = "primary_key_missing"
    TABLE_COMPARE_ERROR = "table_compare_error"


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
                          where_clause: str = None,
                          target_where_clause: str = None) -> Optional[DataDiff]:
        """比对行数"""
        target_table = target_table or table_name
        
        source_count = self.source_conn.get_row_count(table_name, where_clause)
        target_count = self.target_conn.get_row_count(target_table, target_where_clause or where_clause)
        
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
                     target_where_clause: str = None,
                     max_diffs: int = 1000) -> List[DataDiff]:
        """比对数据"""
        target_table = target_table or table_name
        column_mapping = column_mapping or {}
        diffs = []

        # 仅比较双方都存在的字段，避免因结构差异导致目标库查询失败
        source_columns = self.source_conn.get_columns(table_name)
        target_columns = self.target_conn.get_columns(target_table)
        target_column_map = {c.name.lower(): c.name for c in target_columns}

        effective_mapping: Dict[str, str] = {}
        compare_columns: List[str] = []
        for source_col in source_columns:
            if self.skip_large_fields and source_col.data_type.lower() in self.large_field_types:
                continue

            target_col = self._resolve_target_column(source_col.name, column_mapping, target_column_map)
            if not target_col:
                continue

            compare_columns.append(source_col.name)
            effective_mapping[source_col.name] = target_col

        # 主键字段必须可映射，否则无法进行数据定位
        for pk in primary_keys:
            target_pk = self._resolve_target_column(pk, column_mapping, target_column_map)
            if not target_pk:
                raise ValueError(f"目标表 {target_table} 缺少主键字段 {pk}，无法进行数据比对")
            effective_mapping[pk] = target_pk

        source_fetch_columns = self._merge_columns(compare_columns + primary_keys)
        target_pk_columns = [effective_mapping.get(pk, pk) for pk in primary_keys]

        if getattr(self.source_conn, "is_file_source", False) or getattr(self.target_conn, "is_file_source", False):
            return self._compare_data_with_file_source(
                table_name=table_name,
                target_table=target_table,
                primary_keys=primary_keys,
                compare_columns=compare_columns,
                source_fetch_columns=source_fetch_columns,
                target_pk_columns=target_pk_columns,
                effective_mapping=effective_mapping,
                max_diffs=max_diffs,
            )
        
        # 构建排序字段
        order_by = primary_keys.copy()
        row_count_diff = self.compare_row_count(
            table_name=table_name,
            target_table=target_table,
            where_clause=where_clause,
            target_where_clause=target_where_clause,
        )
        if row_count_diff:
            diffs.append(row_count_diff)
            if len(diffs) >= max_diffs:
                return diffs

        source_pk_set = set()
        offset = 0
        while len(diffs) < max_diffs:
            # 分页获取源数据
            source_data = self.source_conn.fetch_data(
                table_name, source_fetch_columns, where_clause, order_by, offset, self.page_size
            )
            
            if not source_data:
                break
            
            # 获取对应的目标数据
            pk_values = [self._extract_pk(row, primary_keys) for row in source_data]
            target_data = self._fetch_target_by_pks(
                target_table,
                pk_values,
                primary_keys,
                source_fetch_columns,
                effective_mapping,
                base_where_clause=target_where_clause
            )
            target_map = {
                self._pk_to_key(self._extract_pk_with_mapping(row, primary_keys, effective_mapping)): row
                for row in target_data
            }
            
            # 比对每一行
            for source_row in source_data:
                if len(diffs) >= max_diffs:
                    break
                    
                pk = self._extract_pk(source_row, primary_keys)
                pk_key = self._pk_to_key(pk)
                source_pk_set.add(pk_key)
                
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
                        target_col = effective_mapping.get(col, col)
                        if not self._values_equal(source_row.get(col), target_row.get(target_col)):
                            diff_columns.append(col)
                    
                    if diff_columns:
                        # 判断是否为空值差异
                        is_null_diff = any(
                            (source_row.get(c) is None) != (target_row.get(effective_mapping.get(c, c)) is None)
                            for c in diff_columns
                        )
                        diffs.append(DataDiff(
                            table_name=table_name,
                            primary_key=pk,
                            diff_type=DataDiffType.NULL_DIFF if is_null_diff else DataDiffType.VALUE_DIFF,
                            diff_columns=diff_columns,
                            source_values={c: self._serialize_value(source_row.get(c)) for c in diff_columns},
                            target_values={c: self._serialize_value(target_row.get(effective_mapping.get(c, c))) for c in diff_columns}
                        ))
            
            offset += self.page_size

        if len(diffs) < max_diffs:
            self._append_target_extra_rows(
                diffs=diffs,
                table_name=table_name,
                target_table=target_table,
                primary_keys=primary_keys,
                effective_mapping=effective_mapping,
                source_pk_set=source_pk_set,
                target_where_clause=target_where_clause,
                compare_columns=compare_columns,
                target_pk_columns=target_pk_columns,
                max_diffs=max_diffs
            )
        
        return diffs

    def _compare_data_with_file_source(
        self,
        table_name: str,
        target_table: str,
        primary_keys: List[str],
        compare_columns: List[str],
        source_fetch_columns: List[str],
        target_pk_columns: List[str],
        effective_mapping: Dict[str, str],
        max_diffs: int,
    ) -> List[DataDiff]:
        """文件数据源回退比对：不依赖 SQL where 下推。"""
        diffs: List[DataDiff] = []
        row_count_diff = self.compare_row_count(table_name=table_name, target_table=target_table)
        if row_count_diff:
            diffs.append(row_count_diff)
            if len(diffs) >= max_diffs:
                return diffs

        target_fetch_columns = self._merge_columns([effective_mapping.get(c, c) for c in source_fetch_columns])
        target_map: Dict[str, Dict[str, Any]] = {}
        target_offset = 0
        while True:
            target_rows = self.target_conn.fetch_data(
                target_table,
                columns=target_fetch_columns,
                where_clause=None,
                order_by=target_pk_columns,
                offset=target_offset,
                limit=self.page_size,
            )
            if not target_rows:
                break
            for row in target_rows:
                key = self._pk_to_key(self._extract_pk_with_mapping(row, primary_keys, effective_mapping))
                target_map[key] = row
            target_offset += self.page_size

        source_pk_set = set()
        source_offset = 0
        while len(diffs) < max_diffs:
            source_rows = self.source_conn.fetch_data(
                table_name,
                columns=source_fetch_columns,
                where_clause=None,
                order_by=primary_keys,
                offset=source_offset,
                limit=self.page_size,
            )
            if not source_rows:
                break

            for source_row in source_rows:
                if len(diffs) >= max_diffs:
                    break
                pk = self._extract_pk(source_row, primary_keys)
                pk_key = self._pk_to_key(pk)
                source_pk_set.add(pk_key)
                target_row = target_map.get(pk_key)
                if target_row is None:
                    diffs.append(
                        DataDiff(
                            table_name=table_name,
                            primary_key=pk,
                            diff_type=DataDiffType.ROW_MISSING_IN_TARGET,
                            diff_columns=[],
                            source_values=self._serialize_row(source_row),
                        )
                    )
                    continue

                diff_columns = []
                for col in compare_columns:
                    target_col = effective_mapping.get(col, col)
                    if not self._values_equal(source_row.get(col), target_row.get(target_col)):
                        diff_columns.append(col)
                if diff_columns:
                    is_null_diff = any(
                        (source_row.get(c) is None) != (target_row.get(effective_mapping.get(c, c)) is None)
                        for c in diff_columns
                    )
                    diffs.append(
                        DataDiff(
                            table_name=table_name,
                            primary_key=pk,
                            diff_type=DataDiffType.NULL_DIFF if is_null_diff else DataDiffType.VALUE_DIFF,
                            diff_columns=diff_columns,
                            source_values={c: self._serialize_value(source_row.get(c)) for c in diff_columns},
                            target_values={
                                c: self._serialize_value(target_row.get(effective_mapping.get(c, c)))
                                for c in diff_columns
                            },
                        )
                    )
            source_offset += self.page_size

        if len(diffs) < max_diffs:
            for key, target_row in target_map.items():
                if len(diffs) >= max_diffs:
                    break
                if key in source_pk_set:
                    continue
                diffs.append(
                    DataDiff(
                        table_name=table_name,
                        primary_key=self._extract_pk_with_mapping(target_row, primary_keys, effective_mapping),
                        diff_type=DataDiffType.ROW_EXTRA_IN_TARGET,
                        diff_columns=[],
                        target_values=self._serialize_row(target_row),
                    )
                )
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

    def _extract_pk_with_mapping(self, row: Dict[str, Any], pk_columns: List[str],
                                 column_mapping: Dict[str, str]) -> Dict[str, Any]:
        """提取并统一主键值（按源主键名返回）"""
        return {col: row.get(column_mapping.get(col, col)) for col in pk_columns}
    
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

    def _resolve_target_column(self, source_column: str,
                               column_mapping: Dict[str, str],
                               target_column_map: Dict[str, str]) -> Optional[str]:
        """解析源字段对应的目标字段（支持大小写不敏感匹配）"""
        mapped = column_mapping.get(source_column, source_column)
        return target_column_map.get(str(mapped).lower())

    def _merge_columns(self, columns: List[str]) -> List[str]:
        """按出现顺序去重字段（大小写不敏感）"""
        merged: List[str] = []
        seen = set()
        for col in columns:
            key = col.lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(col)
        return merged

    def _format_sql_literal(self, value: Any) -> str:
        """格式化SQL字面量"""
        if value is None:
            return "NULL"
        if isinstance(value, str):
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        if isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        if isinstance(value, bytes):
            return f"'{value.hex()}'"
        return str(value)
    
    def _fetch_target_by_pks(self, table_name: str, pk_values: List[Dict],
                             pk_columns: List[str], columns: List[str],
                             column_mapping: Dict[str, str],
                             base_where_clause: str = None) -> List[Dict]:
        """根据主键批量获取目标数据"""
        if not pk_values:
            return []

        target_pk_columns = [column_mapping.get(col, col) for col in pk_columns]
        
        # 构建IN查询条件
        if len(pk_columns) == 1:
            source_pk = pk_columns[0]
            target_pk = target_pk_columns[0]
            values = [pk[source_pk] for pk in pk_values]
            non_null_values = [v for v in values if v is not None]

            clauses = []
            if non_null_values:
                formatted_values = [self._format_sql_literal(v) for v in non_null_values]
                clauses.append(f"{target_pk} IN ({','.join(formatted_values)})")
            if any(v is None for v in values):
                clauses.append(f"{target_pk} IS NULL")

            if not clauses:
                return []
            where = " OR ".join(clauses)
        else:
            # 复合主键
            conditions = []
            for pk in pk_values:
                cond_parts = []
                for source_pk, target_pk in zip(pk_columns, target_pk_columns):
                    v = pk.get(source_pk)
                    if v is None:
                        cond_parts.append(f"{target_pk} IS NULL")
                    else:
                        cond_parts.append(f"{target_pk} = {self._format_sql_literal(v)}")
                conditions.append(f"({' AND '.join(cond_parts)})")
            where = ' OR '.join(conditions)
        
        if base_where_clause:
            where = f"({base_where_clause}) AND ({where})"

        target_columns = [column_mapping.get(c, c) for c in columns]
        return self.target_conn.fetch_data(
            table_name,
            self._merge_columns(target_columns),
            where,
            limit=max(len(pk_values), 1)
        )

    def _append_target_extra_rows(
        self,
        diffs: List[DataDiff],
        table_name: str,
        target_table: str,
        primary_keys: List[str],
        effective_mapping: Dict[str, str],
        source_pk_set: set,
        target_where_clause: Optional[str],
        compare_columns: List[str],
        target_pk_columns: List[str],
        max_diffs: int
    ) -> None:
        """补充目标库多余行差异。"""
        target_fetch_columns = self._merge_columns(
            [effective_mapping.get(col, col) for col in compare_columns] + target_pk_columns
        )
        target_order_by = target_pk_columns.copy()

        offset = 0
        while len(diffs) < max_diffs:
            target_data = self.target_conn.fetch_data(
                target_table,
                target_fetch_columns,
                target_where_clause,
                target_order_by,
                offset,
                self.page_size
            )
            if not target_data:
                break

            for target_row in target_data:
                if len(diffs) >= max_diffs:
                    break
                target_pk = self._extract_pk_with_mapping(
                    target_row, primary_keys, effective_mapping
                )
                target_pk_key = self._pk_to_key(target_pk)
                if target_pk_key in source_pk_set:
                    continue
                diffs.append(DataDiff(
                    table_name=table_name,
                    primary_key=target_pk,
                    diff_type=DataDiffType.ROW_EXTRA_IN_TARGET,
                    diff_columns=[],
                    target_values=self._serialize_row(target_row)
                ))

            offset += self.page_size
