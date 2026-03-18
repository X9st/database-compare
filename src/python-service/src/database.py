#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
支持多种数据库类型的连接和操作
"""

import pymysql
import psycopg2
import sqlite3
from typing import Dict, List, Tuple, Optional

# 尝试导入国产数据库驱动（可能未安装）
try:
    import dmPython
    DM_SUPPORT = True
except ImportError:
    DM_SUPPORT = False

try:
    from pyhive import hive
    from pyhive.exc import Error as HiveError
    HIVE_SUPPORT = True
except ImportError:
    HIVE_SUPPORT = False


class DatabaseManager:
    """数据库管理器"""
    
    # 数据库类型映射
    DRIVERS = {
        'mysql': 'pymysql',
        'mariadb': 'pymysql',
        'postgresql': 'psycopg2',
        'sqlite': 'sqlite3',
        'dameng': 'dmPython' if DM_SUPPORT else None,
        'inceptor': 'pyhive' if HIVE_SUPPORT else None,
        'kingbase': 'psycopg2',  # 人大金仓兼容 PostgreSQL 协议
    }
    
    # 数据库显示名称
    DB_NAMES = {
        'mysql': 'MySQL',
        'mariadb': 'MariaDB',
        'postgresql': 'PostgreSQL',
        'sqlite': 'SQLite',
        'dameng': '达梦数据库',
        'inceptor': 'Inceptor',
        'kingbase': '人大金仓'
    }
    
    def __init__(self, config: Dict):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库连接配置
                {
                    'type': 'mysql',
                    'host': 'localhost',
                    'port': 3306,
                    'database': 'test',
                    'username': 'root',
                    'password': 'password',
                    'charset': 'utf8mb4'
                }
        """
        self.config = config
        self.connection = None
        self.db_type = config.get('type', 'mysql').lower()
    
    @classmethod
    def check_driver_support(cls, db_type: str) -> Tuple[bool, str]:
        """
        检查数据库驱动是否支持
        
        Args:
            db_type: 数据库类型
            
        Returns:
            (是否支持, 提示信息)
        """
        db_type = db_type.lower()
        
        if db_type == 'dameng':
            if DM_SUPPORT:
                return True, '达梦数据库驱动已安装'
            else:
                return False, '达梦数据库驱动未安装，请安装 dmPython'
        
        elif db_type == 'inceptor':
            if HIVE_SUPPORT:
                return True, 'Inceptor 驱动已安装'
            else:
                return False, 'Inceptor 驱动未安装，请安装 pyhive'
        
        elif db_type in cls.DRIVERS:
            return True, f'{cls.DB_NAMES.get(db_type, db_type)} 支持'
        
        else:
            return False, f'不支持的数据库类型: {db_type}'
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试数据库连接
        
        Returns:
            (是否成功, 消息)
        """
        # 先检查驱动支持
        supported, message = self.check_driver_support(self.db_type)
        if not supported:
            return False, message
        
        try:
            conn = self._create_connection()
            conn.close()
            return True, '连接成功'
        except Exception as e:
            return False, f'连接失败: {str(e)}'
    
    def _create_connection(self):
        """创建数据库连接"""
        if self.db_type in ['mysql', 'mariadb']:
            return pymysql.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 3306),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password'),
                charset=self.config.get('charset', 'utf8mb4'),
                cursorclass=pymysql.cursors.DictCursor
            )
        elif self.db_type == 'postgresql':
            return psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password')
            )
        elif self.db_type == 'sqlite':
            return sqlite3.connect(self.config.get('database'))
        
        elif self.db_type == 'dameng':
            if not DM_SUPPORT:
                raise ImportError('达梦数据库驱动未安装，请安装 dmPython')
            return dmPython.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5236),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password')
            )
        
        elif self.db_type == 'inceptor':
            if not HIVE_SUPPORT:
                raise ImportError('Inceptor 驱动未安装，请安装 pyhive')
            return hive.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 10000),
                database=self.config.get('database'),
                username=self.config.get('username'),
                password=self.config.get('password'),
                auth='CUSTOM' if self.config.get('password') else 'NONE'
            )
        
        elif self.db_type == 'kingbase':
            # 人大金仓兼容 PostgreSQL 协议
            return psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 54321),
                database=self.config.get('database'),
                user=self.config.get('username'),
                password=self.config.get('password')
            )
        
        else:
            raise ValueError(f'不支持的数据库类型: {self.db_type}')
    
    def get_connection(self):
        """获取数据库连接（懒加载）"""
        if self.connection is None:
            self.connection = self._create_connection()
        return self.connection
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_tables(self) -> List[Dict]:
        """
        获取数据库中的所有表
        
        Returns:
            表信息列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if self.db_type in ['mysql', 'mariadb']:
                cursor.execute("""
                    SELECT 
                        TABLE_NAME as name,
                        TABLE_COMMENT as comment,
                        ENGINE as engine
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = %s
                    ORDER BY TABLE_NAME
                """, (self.config.get('database'),))
                return cursor.fetchall()
            
            elif self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT 
                        table_name as name,
                        obj_description((table_schema || '.' || table_name)::regclass) as comment
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                return [{'name': row[0], 'comment': row[1]} for row in cursor.fetchall()]
            
            elif self.db_type == 'sqlite':
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                return [{'name': row[0]} for row in cursor.fetchall()]
            
            elif self.db_type == 'dameng':
                # 达梦数据库获取表列表
                cursor.execute("""
                    SELECT 
                        TABLE_NAME as name,
                        COMMENTS as comment
                    FROM USER_TAB_COMMENTS
                    WHERE TABLE_TYPE = 'TABLE'
                    ORDER BY TABLE_NAME
                """)
                return [{'name': row[0], 'comment': row[1]} for row in cursor.fetchall()]
            
            elif self.db_type == 'inceptor':
                # Inceptor 获取表列表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                return [{'name': row[0]} for row in tables]
            
            elif self.db_type == 'kingbase':
                # 人大金仓兼容 PostgreSQL
                cursor.execute("""
                    SELECT 
                        table_name as name,
                        obj_description((table_schema || '.' || table_name)::regclass) as comment
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                return [{'name': row[0], 'comment': row[1]} for row in cursor.fetchall()]
            
            else:
                return []
        finally:
            cursor.close()
    
    def get_table_structure(self, table_name: str) -> Dict:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            表结构信息
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            structure = {
                'name': table_name,
                'columns': [],
                'indexes': [],
                'primary_key': []
            }
            
            if self.db_type in ['mysql', 'mariadb']:
                # 获取列信息
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME as name,
                        DATA_TYPE as type,
                        CHARACTER_MAXIMUM_LENGTH as max_length,
                        NUMERIC_PRECISION as precision,
                        NUMERIC_SCALE as scale,
                        IS_NULLABLE as nullable,
                        COLUMN_DEFAULT as default_value,
                        COLUMN_COMMENT as comment,
                        COLUMN_KEY as key_type
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (self.config.get('database'), table_name))
                structure['columns'] = cursor.fetchall()
                
                # 获取索引信息
                cursor.execute("""
                    SELECT 
                        INDEX_NAME as name,
                        COLUMN_NAME as column_name,
                        NON_UNIQUE as non_unique
                    FROM INFORMATION_SCHEMA.STATISTICS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY INDEX_NAME, SEQ_IN_INDEX
                """, (self.config.get('database'), table_name))
                structure['indexes'] = cursor.fetchall()
            
            elif self.db_type == 'postgresql':
                # 获取列信息
                cursor.execute("""
                    SELECT 
                        column_name as name,
                        data_type as type,
                        character_maximum_length as max_length,
                        numeric_precision as precision,
                        numeric_scale as scale,
                        is_nullable as nullable,
                        column_default as default_value
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                structure['columns'] = [
                    {
                        'name': col[0],
                        'type': col[1],
                        'max_length': col[2],
                        'precision': col[3],
                        'scale': col[4],
                        'nullable': col[5],
                        'default_value': col[6]
                    }
                    for col in columns
                ]
            
            elif self.db_type == 'dameng':
                # 达梦数据库获取列信息
                cursor.execute("""
                    SELECT 
                        COLUMN_NAME as name,
                        DATA_TYPE as type,
                        DATA_LENGTH as max_length,
                        DATA_PRECISION as precision,
                        DATA_SCALE as scale,
                        NULLABLE as nullable,
                        DATA_DEFAULT as default_value,
                        COMMENTS as comment
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = %s
                    ORDER BY COLUMN_ID
                """, (table_name.upper(),))
                columns = cursor.fetchall()
                structure['columns'] = [
                    {
                        'name': col[0],
                        'type': col[1],
                        'max_length': col[2],
                        'precision': col[3],
                        'scale': col[4],
                        'nullable': col[5],
                        'default_value': col[6],
                        'comment': col[7]
                    }
                    for col in columns
                ]
            
            elif self.db_type == 'inceptor':
                # Inceptor 获取列信息
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                structure['columns'] = [
                    {
                        'name': col[0],
                        'type': col[1],
                        'comment': col[2] if len(col) > 2 else ''
                    }
                    for col in columns
                ]
            
            elif self.db_type == 'kingbase':
                # 人大金仓兼容 PostgreSQL
                cursor.execute("""
                    SELECT 
                        column_name as name,
                        data_type as type,
                        character_maximum_length as max_length,
                        numeric_precision as precision,
                        numeric_scale as scale,
                        is_nullable as nullable,
                        column_default as default_value
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                structure['columns'] = [
                    {
                        'name': col[0],
                        'type': col[1],
                        'max_length': col[2],
                        'precision': col[3],
                        'scale': col[4],
                        'nullable': col[5],
                        'default_value': col[6]
                    }
                    for col in columns
                ]
            
            return structure
        finally:
            cursor.close()
    
    def get_table_data_sample(self, table_name: str, limit: int = 100) -> List[Dict]:
        """
        获取表数据样本
        
        Args:
            table_name: 表名
            limit: 返回记录数限制
            
        Returns:
            数据样本
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 使用参数化查询防止 SQL 注入
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s", (limit,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()
    
    def get_table_row_count(self, table_name: str) -> int:
        """
        获取表记录数
        
        Args:
            table_name: 表名
            
        Returns:
            记录数
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            cursor.close()
