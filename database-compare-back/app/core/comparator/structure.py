"""结构比对器"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from app.core.connector.base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class StructureDiffType(str, Enum):
    TABLE_MISSING_IN_TARGET = "table_missing_in_target"
    TABLE_EXTRA_IN_TARGET = "table_extra_in_target"
    COLUMN_MISSING = "column_missing"
    COLUMN_EXTRA = "column_extra"
    COLUMN_TYPE_DIFF = "column_type_diff"
    COLUMN_LENGTH_DIFF = "column_length_diff"
    COLUMN_PRECISION_DIFF = "column_precision_diff"
    COLUMN_NULLABLE_DIFF = "column_nullable_diff"
    COLUMN_DEFAULT_DIFF = "column_default_diff"
    INDEX_DIFF = "index_diff"
    CONSTRAINT_DIFF = "constraint_diff"
    COMMENT_DIFF = "comment_diff"


@dataclass
class StructureDiff:
    """结构差异"""
    table_name: str
    diff_type: StructureDiffType
    field_name: Optional[str] = None
    source_value: Optional[str] = None
    target_value: Optional[str] = None
    diff_detail: str = ""


class StructureComparator:
    """表结构比对器"""
    
    def __init__(self, source_conn: BaseConnector, target_conn: BaseConnector,
                 options: Dict[str, Any] = None):
        self.source_conn = source_conn
        self.target_conn = target_conn
        self.options = options or {}
        self.compare_index = self.options.get('compare_index', True)
        self.compare_constraint = self.options.get('compare_constraint', True)
        self.compare_comment = self.options.get('compare_comment', True)
        self._source_table_meta: Optional[Dict[str, TableInfo]] = None
        self._target_table_meta: Optional[Dict[str, TableInfo]] = None
    
    def compare_tables(self, source_tables: List[str], 
                       target_tables: List[str]) -> List[StructureDiff]:
        """比对表存在性"""
        diffs = []
        source_set = set(source_tables)
        target_set = set(target_tables)
        
        # 目标库缺少的表
        for table in source_set - target_set:
            diffs.append(StructureDiff(
                table_name=table,
                diff_type=StructureDiffType.TABLE_MISSING_IN_TARGET,
                diff_detail=f"目标库缺少表: {table}"
            ))
        
        # 目标库多余的表
        for table in target_set - source_set:
            diffs.append(StructureDiff(
                table_name=table,
                diff_type=StructureDiffType.TABLE_EXTRA_IN_TARGET,
                diff_detail=f"目标库多余表: {table}"
            ))
        
        return diffs
    
    def compare_columns(self, table_name: str, 
                        source_columns: List[ColumnInfo],
                        target_columns: List[ColumnInfo],
                        column_mapping: Optional[Dict[str, str]] = None) -> List[StructureDiff]:
        """比对字段"""
        diffs = []
        column_mapping = column_mapping or {}
        source_map = {c.name.lower(): c for c in source_columns}
        target_map = {c.name.lower(): c for c in target_columns}
        mapped_source_keys = {
            self._get_mapped_column_name(src_col.name, column_mapping).lower()
            for src_col in source_columns
        }
        
        # 检查缺少和多余的字段
        for col_name, src_col in source_map.items():
            mapped_target_name = self._get_mapped_column_name(src_col.name, column_mapping)
            target_key = mapped_target_name.lower()
            if target_key not in target_map:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.COLUMN_MISSING,
                    field_name=src_col.name,
                    source_value=src_col.data_type,
                    target_value=mapped_target_name,
                    diff_detail=f"目标表缺少字段: {src_col.name} -> {mapped_target_name}"
                ))
        
        for col_name, tgt_col in target_map.items():
            if col_name not in mapped_source_keys:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.COLUMN_EXTRA,
                    field_name=tgt_col.name,
                    target_value=tgt_col.data_type,
                    diff_detail=f"目标表多余字段: {tgt_col.name}"
                ))
        
        # 比对共有字段的属性
        for col_name, src_col in source_map.items():
            mapped_target_name = self._get_mapped_column_name(src_col.name, column_mapping)
            target_key = mapped_target_name.lower()
            if target_key in target_map:
                tgt_col = target_map[target_key]
                
                # 数据类型
                if src_col.data_type.lower() != tgt_col.data_type.lower():
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.COLUMN_TYPE_DIFF,
                        field_name=src_col.name,
                        source_value=src_col.data_type,
                        target_value=tgt_col.data_type,
                        diff_detail=f"字段 {src_col.name} 类型不同"
                    ))
                
                # 字段长度
                if src_col.length != tgt_col.length:
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.COLUMN_LENGTH_DIFF,
                        field_name=src_col.name,
                        source_value=str(src_col.length),
                        target_value=str(tgt_col.length),
                        diff_detail=f"字段 {src_col.name} 长度不同"
                    ))

                # 字段精度/小数位
                if src_col.precision != tgt_col.precision or src_col.scale != tgt_col.scale:
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.COLUMN_PRECISION_DIFF,
                        field_name=src_col.name,
                        source_value=f"precision={src_col.precision}, scale={src_col.scale}",
                        target_value=f"precision={tgt_col.precision}, scale={tgt_col.scale}",
                        diff_detail=f"字段 {src_col.name} 精度/小数位不同"
                    ))
                
                # 可空属性
                if src_col.nullable != tgt_col.nullable:
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.COLUMN_NULLABLE_DIFF,
                        field_name=src_col.name,
                        source_value="NULL" if src_col.nullable else "NOT NULL",
                        target_value="NULL" if tgt_col.nullable else "NOT NULL",
                        diff_detail=f"字段 {src_col.name} 可空属性不同"
                    ))
                
                # 默认值
                if src_col.default_value != tgt_col.default_value:
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.COLUMN_DEFAULT_DIFF,
                        field_name=src_col.name,
                        source_value=src_col.default_value,
                        target_value=tgt_col.default_value,
                        diff_detail=f"字段 {src_col.name} 默认值不同"
                    ))
                
                # 注释
                if self.compare_comment and src_col.comment != tgt_col.comment:
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.COMMENT_DIFF,
                        field_name=src_col.name,
                        source_value=src_col.comment,
                        target_value=tgt_col.comment,
                        diff_detail=f"字段 {src_col.name} 注释不同"
                    ))
        
        return diffs
    
    def compare_table_structure(self, table_name: str,
                                table_mapping: Dict[str, str] = None,
                                column_mapping: Optional[Dict[str, str]] = None) -> List[StructureDiff]:
        """比对单表结构"""
        target_table = table_mapping.get(table_name, table_name) if table_mapping else table_name
        diffs = []
        
        # 获取字段信息
        source_columns = self.source_conn.get_columns(table_name)
        target_columns = self.target_conn.get_columns(target_table)
        diffs.extend(self.compare_columns(table_name, source_columns, target_columns, column_mapping=column_mapping))

        if self.compare_comment:
            source_comment = self._get_table_comment(table_name, source=True)
            target_comment = self._get_table_comment(target_table, source=False)
            if source_comment != target_comment:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.COMMENT_DIFF,
                    field_name="__table_comment__",
                    source_value=source_comment,
                    target_value=target_comment,
                    diff_detail=f"表注释不同: {table_name}"
                ))
        
        # 比对索引
        if self.compare_index:
            source_indexes = self.source_conn.get_indexes(table_name)
            target_indexes = self.target_conn.get_indexes(target_table)
            diffs.extend(self._compare_indexes(table_name, source_indexes, target_indexes))
        
        # 比对约束
        if self.compare_constraint:
            source_constraints = self.source_conn.get_constraints(table_name)
            target_constraints = self.target_conn.get_constraints(target_table)
            diffs.extend(self._compare_constraints(table_name, source_constraints, target_constraints))
        
        return diffs

    def _get_table_comment(self, table_name: str, source: bool) -> Optional[str]:
        if source:
            if self._source_table_meta is None:
                self._source_table_meta = {t.name.lower(): t for t in self.source_conn.get_tables()}
            table = self._source_table_meta.get(table_name.lower())
        else:
            if self._target_table_meta is None:
                self._target_table_meta = {t.name.lower(): t for t in self.target_conn.get_tables()}
            table = self._target_table_meta.get(table_name.lower())
        return table.comment if table else None

    def _get_mapped_column_name(self, source_column: str, column_mapping: Dict[str, str]) -> str:
        if source_column in column_mapping:
            return column_mapping[source_column]
        source_key = source_column.lower()
        for src, tgt in (column_mapping or {}).items():
            if str(src).lower() == source_key:
                return tgt
        return source_column
    
    def _compare_indexes(self, table_name: str,
                         source_indexes: List[IndexInfo],
                         target_indexes: List[IndexInfo]) -> List[StructureDiff]:
        """比对索引"""
        diffs = []
        source_map = {i.name.lower(): i for i in source_indexes}
        target_map = {i.name.lower(): i for i in target_indexes}
        
        for idx_name in set(source_map.keys()) | set(target_map.keys()):
            src_idx = source_map.get(idx_name)
            tgt_idx = target_map.get(idx_name)
            
            if src_idx and not tgt_idx:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.INDEX_DIFF,
                    field_name=src_idx.name,
                    source_value=f"索引存在 ({','.join(src_idx.columns)})",
                    target_value="索引不存在",
                    diff_detail=f"目标表缺少索引: {src_idx.name}"
                ))
            elif tgt_idx and not src_idx:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.INDEX_DIFF,
                    field_name=tgt_idx.name,
                    source_value="索引不存在",
                    target_value=f"索引存在 ({','.join(tgt_idx.columns)})",
                    diff_detail=f"目标表多余索引: {tgt_idx.name}"
                ))
            elif src_idx and tgt_idx:
                if src_idx.columns != tgt_idx.columns or src_idx.is_unique != tgt_idx.is_unique:
                    diffs.append(StructureDiff(
                        table_name=table_name,
                        diff_type=StructureDiffType.INDEX_DIFF,
                        field_name=src_idx.name,
                        source_value=f"{','.join(src_idx.columns)} (unique={src_idx.is_unique})",
                        target_value=f"{','.join(tgt_idx.columns)} (unique={tgt_idx.is_unique})",
                        diff_detail=f"索引 {src_idx.name} 定义不同"
                    ))
        
        return diffs
    
    def _compare_constraints(self, table_name: str,
                             source_constraints: List[ConstraintInfo],
                             target_constraints: List[ConstraintInfo]) -> List[StructureDiff]:
        """比对约束"""
        diffs = []
        source_map = {c.name.lower(): c for c in source_constraints}
        target_map = {c.name.lower(): c for c in target_constraints}
        
        for cst_name in set(source_map.keys()) | set(target_map.keys()):
            src_cst = source_map.get(cst_name)
            tgt_cst = target_map.get(cst_name)
            
            if src_cst and not tgt_cst:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.CONSTRAINT_DIFF,
                    field_name=src_cst.name,
                    source_value=f"{src_cst.constraint_type} ({','.join(src_cst.columns)})",
                    target_value="约束不存在",
                    diff_detail=f"目标表缺少约束: {src_cst.name}"
                ))
            elif tgt_cst and not src_cst:
                diffs.append(StructureDiff(
                    table_name=table_name,
                    diff_type=StructureDiffType.CONSTRAINT_DIFF,
                    field_name=tgt_cst.name,
                    source_value="约束不存在",
                    target_value=f"{tgt_cst.constraint_type} ({','.join(tgt_cst.columns)})",
                    diff_detail=f"目标表多余约束: {tgt_cst.name}"
                ))
        
        return diffs
