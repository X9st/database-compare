#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库比对器模块
实现表结构、字段信息、数据内容的三维度比对
"""

import hashlib
from typing import Dict, List, Any
from database import DatabaseManager


class DatabaseComparator:
    """数据库比对器"""
    
    def __init__(self, source_config: Dict, target_config: Dict):
        """
        初始化比对器
        
        Args:
            source_config: 源数据库配置
            target_config: 目标数据库配置
        """
        self.source_db = DatabaseManager(source_config)
        self.target_db = DatabaseManager(target_config)
        self.result = {
            'tables': {'added': [], 'removed': [], 'modified': []},
            'columns': {},
            'data': {}
        }
    
    def compare_all(self, table_names: List[str] = None, 
                   table_mapping: Dict[str, str] = None,
                   compare_structure: bool = True,
                   compare_columns: bool = True,
                   compare_data: bool = False) -> Dict:
        """
        执行全量比对
        
        Args:
            table_names: 指定比对的表名列表，None 表示比对所有表
            compare_structure: 是否比对表结构
            compare_columns: 是否比对字段信息
            compare_data: 是否比对数据内容
            
        Returns:
            比对结果
        """
        try:
            # 如果提供了表名映射，直接使用映射进行比对
            if table_mapping:
                for source_table, target_table in table_mapping.items():
                    # 比对表结构（如果表名不同，视为不同的表）
                    if compare_structure:
                        self._compare_mapped_tables(source_table, target_table)
                    
                    # 比对字段信息
                    if compare_columns:
                        self._compare_mapped_columns(source_table, target_table)
                    
                    # 比对数据内容
                    if compare_data:
                        self._compare_mapped_data(source_table, target_table)
            else:
                # 获取表列表
                source_tables = {t['name']: t for t in self.source_db.get_tables()}
                target_tables = {t['name']: t for t in self.target_db.get_tables()}
                
                if table_names:
                    source_tables = {k: v for k, v in source_tables.items() if k in table_names}
                    target_tables = {k: v for k, v in target_tables.items() if k in table_names}
                
                # 比对表结构
                if compare_structure:
                    self._compare_tables(source_tables, target_tables)
                
                # 比对字段信息
                if compare_columns:
                    common_tables = set(source_tables.keys()) & set(target_tables.keys())
                    for table_name in common_tables:
                        self._compare_columns(table_name)
                
                # 比对数据内容
                if compare_data:
                    common_tables = set(source_tables.keys()) & set(target_tables.keys())
                    for table_name in common_tables:
                        self._compare_data(table_name)
            
            return self.result
        finally:
            self.source_db.close()
            self.target_db.close()
    
    def _compare_tables(self, source_tables: Dict, target_tables: Dict):
        """比对表结构差异"""
        source_names = set(source_tables.keys())
        target_names = set(target_tables.keys())
        
        # 新增的表
        added = source_names - target_names
        for name in added:
            self.result['tables']['added'].append({
                'name': name,
                'info': source_tables[name]
            })
        
        # 删除的表
        removed = target_names - source_names
        for name in removed:
            self.result['tables']['removed'].append({
                'name': name,
                'info': target_tables[name]
            })
        
        # 共同存在的表，检查属性差异
        common = source_names & target_names
        for name in common:
            source_info = source_tables[name]
            target_info = target_tables[name]
            
            differences = []
            for key in ['comment', 'engine']:
                if source_info.get(key) != target_info.get(key):
                    differences.append({
                        'field': key,
                        'source': source_info.get(key),
                        'target': target_info.get(key)
                    })
            
            if differences:
                self.result['tables']['modified'].append({
                    'name': name,
                    'differences': differences
                })
    
    def _compare_columns(self, table_name: str):
        """比对表的字段信息"""
        source_structure = self.source_db.get_table_structure(table_name)
        target_structure = self.target_db.get_table_structure(table_name)
        
        source_columns = {c['name']: c for c in source_structure['columns']}
        target_columns = {c['name']: c for c in target_structure['columns']}
        
        column_diff = {
            'added': [],
            'removed': [],
            'modified': []
        }
        
        source_names = set(source_columns.keys())
        target_names = set(target_columns.keys())
        
        # 新增的字段
        for name in source_names - target_names:
            column_diff['added'].append(source_columns[name])
        
        # 删除的字段
        for name in target_names - source_names:
            column_diff['removed'].append(target_columns[name])
        
        # 修改的字段
        for name in source_names & target_names:
            source_col = source_columns[name]
            target_col = target_columns[name]
            
            differences = []
            compare_fields = ['type', 'max_length', 'precision', 'scale', 
                            'nullable', 'default_value', 'comment']
            
            for field in compare_fields:
                if source_col.get(field) != target_col.get(field):
                    differences.append({
                        'field': field,
                        'source': source_col.get(field),
                        'target': target_col.get(field)
                    })
            
            if differences:
                column_diff['modified'].append({
                    'name': name,
                    'differences': differences
                })
        
        if column_diff['added'] or column_diff['removed'] or column_diff['modified']:
            self.result['columns'][table_name] = column_diff
    
    def _compare_mapped_tables(self, source_table: str, target_table: str):
        """比对映射的表结构（表名可能不同）"""
        try:
            source_structure = self.source_db.get_table_structure(source_table)
            target_structure = self.target_db.get_table_structure(target_table)
            
            differences = []
            
            # 比对表注释
            if source_structure.get('comment') != target_structure.get('comment'):
                differences.append({
                    'field': 'comment',
                    'source': source_structure.get('comment'),
                    'target': target_structure.get('comment')
                })
            
            # 比对存储引擎（MySQL）
            if source_structure.get('engine') != target_structure.get('engine'):
                differences.append({
                    'field': 'engine',
                    'source': source_structure.get('engine'),
                    'target': target_structure.get('engine')
                })
            
            if differences:
                self.result['tables']['modified'].append({
                    'name': f'{source_table} → {target_table}',
                    'source_name': source_table,
                    'target_name': target_table,
                    'differences': differences
                })
        except Exception as e:
            self.result['tables']['modified'].append({
                'name': f'{source_table} → {target_table}',
                'source_name': source_table,
                'target_name': target_table,
                'error': str(e)
            })

    def _compare_mapped_columns(self, source_table: str, target_table: str):
        """比对映射表的字段信息"""
        try:
            source_structure = self.source_db.get_table_structure(source_table)
            target_structure = self.target_db.get_table_structure(target_table)
            
            source_columns = {c['name']: c for c in source_structure['columns']}
            target_columns = {c['name']: c for c in target_structure['columns']}
            
            column_diff = {
                'added': [],
                'removed': [],
                'modified': []
            }
            
            source_names = set(source_columns.keys())
            target_names = set(target_columns.keys())
            
            # 新增的字段
            for name in source_names - target_names:
                column_diff['added'].append(source_columns[name])
            
            # 删除的字段
            for name in target_names - source_names:
                column_diff['removed'].append(target_columns[name])
            
            # 修改的字段
            for name in source_names & target_names:
                source_col = source_columns[name]
                target_col = target_columns[name]
                
                differences = []
                compare_fields = ['type', 'max_length', 'precision', 'scale', 
                                'nullable', 'default_value', 'comment']
                
                for field in compare_fields:
                    if source_col.get(field) != target_col.get(field):
                        differences.append({
                            'field': field,
                            'source': source_col.get(field),
                            'target': target_col.get(field)
                        })
                
                if differences:
                    column_diff['modified'].append({
                        'name': name,
                        'differences': differences
                    })
            
            if column_diff['added'] or column_diff['removed'] or column_diff['modified']:
                self.result['columns'][f'{source_table} → {target_table}'] = column_diff
        except Exception as e:
            self.result['columns'][f'{source_table} → {target_table}'] = {
                'error': str(e)
            }

    def _compare_mapped_data(self, source_table: str, target_table: str, sample_size: int = 1000):
        """比对映射表的数据内容"""
        try:
            # 获取记录数
            source_count = self.source_db.get_table_row_count(source_table)
            target_count = self.target_db.get_table_row_count(target_table)
            
            data_diff = {
                'source_table': source_table,
                'target_table': target_table,
                'source_count': source_count,
                'target_count': target_count,
                'count_diff': source_count - target_count,
                'sample_differences': []
            }
            
            # 如果记录数差异不大，进行抽样比对
            if abs(data_diff['count_diff']) < sample_size * 2:
                source_data = self.source_db.get_table_data_sample(source_table, sample_size)
                target_data = self.target_db.get_table_data_sample(target_table, sample_size)
                
                # 简化的数据比对：基于主键或第一列
                if source_data and target_data:
                    key_column = list(source_data[0].keys())[0]
                    
                    source_dict = {str(row.get(key_column)): row for row in source_data}
                    target_dict = {str(row.get(key_column)): row for row in target_data}
                    
                    # 找出差异行
                    for key, source_row in source_dict.items():
                        if key not in target_dict:
                            data_diff['sample_differences'].append({
                                'type': 'missing_in_target',
                                'key': key,
                                'source_row': source_row
                            })
                        elif source_row != target_dict[key]:
                            data_diff['sample_differences'].append({
                                'type': 'different',
                                'key': key,
                                'source_row': source_row,
                                'target_row': target_dict[key]
                            })
                    
                    for key, target_row in target_dict.items():
                        if key not in source_dict:
                            data_diff['sample_differences'].append({
                                'type': 'missing_in_source',
                                'key': key,
                                'target_row': target_row
                            })
            
            if data_diff['count_diff'] != 0 or data_diff['sample_differences']:
                self.result['data'][f'{source_table} → {target_table}'] = data_diff
        except Exception as e:
            self.result['data'][f'{source_table} → {target_table}'] = {
                'error': str(e)
            }

    def _compare_data(self, table_name: str, sample_size: int = 1000):
        """比对表数据内容"""
        # 获取记录数
        source_count = self.source_db.get_table_row_count(table_name)
        target_count = self.target_db.get_table_row_count(table_name)
        
        data_diff = {
            'source_count': source_count,
            'target_count': target_count,
            'count_diff': source_count - target_count,
            'sample_differences': []
        }
        
        # 如果记录数差异不大，进行抽样比对
        if abs(data_diff['count_diff']) < sample_size * 2:
            source_data = self.source_db.get_table_data_sample(table_name, sample_size)
            target_data = self.target_db.get_table_data_sample(table_name, sample_size)
            
            # 简化的数据比对：基于主键或第一列
            if source_data and target_data:
                key_column = list(source_data[0].keys())[0]
                
                source_dict = {str(row.get(key_column)): row for row in source_data}
                target_dict = {str(row.get(key_column)): row for row in target_data}
                
                # 找出差异行
                for key, source_row in source_dict.items():
                    if key not in target_dict:
                        data_diff['sample_differences'].append({
                            'type': 'missing_in_target',
                            'key': key,
                            'source_row': source_row
                        })
                    elif source_row != target_dict[key]:
                        data_diff['sample_differences'].append({
                            'type': 'different',
                            'key': key,
                            'source_row': source_row,
                            'target_row': target_dict[key]
                        })
                
                for key, target_row in target_dict.items():
                    if key not in source_dict:
                        data_diff['sample_differences'].append({
                            'type': 'missing_in_source',
                            'key': key,
                            'target_row': target_row
                        })
        
        if data_diff['count_diff'] != 0 or data_diff['sample_differences']:
            self.result['data'][table_name] = data_diff
