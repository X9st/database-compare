"""MySQL数据库连接器"""
import pymysql
from typing import List, Dict, Any
import time
from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class MySQLConnector(BaseConnector):
    """MySQL数据库连接器"""
    
    def connect(self) -> bool:
        try:
            self._connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset=self.charset.replace('-', '').lower() if self.charset else 'utf8mb4',
                connect_timeout=self.timeout,
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            raise ConnectionError(f"MySQL连接失败: {str(e)}")
    
    def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def test_connection(self) -> Dict[str, Any]:
        start_time = time.time()
        try:
            self.connect()
            version = self.get_version()
            latency = int((time.time() - start_time) * 1000)
            self.disconnect()
            return {
                "success": True,
                "message": "连接成功",
                "version": f"MySQL {version}",
                "latency": latency
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "version": None,
                "latency": None
            }
    
    def get_tables(self) -> List[TableInfo]:
        sql = """
            SELECT 
                TABLE_NAME as name,
                TABLE_SCHEMA as `schema`,
                TABLE_COMMENT as comment,
                TABLE_ROWS as row_count
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = %s
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (self.database,))
            results = cursor.fetchall()
        
        return [TableInfo(
            name=row['name'],
            schema=row['schema'],
            comment=row['comment'],
            row_count=row['row_count'] or 0
        ) for row in results]
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        sql = """
            SELECT 
                COLUMN_NAME as name,
                DATA_TYPE as data_type,
                CHARACTER_MAXIMUM_LENGTH as length,
                NUMERIC_PRECISION as `precision`,
                NUMERIC_SCALE as scale,
                IS_NULLABLE = 'YES' as nullable,
                COLUMN_DEFAULT as default_value,
                COLUMN_COMMENT as comment,
                COLUMN_KEY = 'PRI' as is_primary_key
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (self.database, table_name))
            results = cursor.fetchall()
        
        return [ColumnInfo(
            name=row['name'],
            data_type=row['data_type'],
            length=row['length'],
            precision=row['precision'],
            scale=row['scale'],
            nullable=bool(row['nullable']),
            default_value=row['default_value'],
            comment=row['comment'],
            is_primary_key=bool(row['is_primary_key'])
        ) for row in results]
    
    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        sql = """
            SELECT 
                INDEX_NAME as name,
                GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                NON_UNIQUE = 0 as is_unique,
                INDEX_NAME = 'PRIMARY' as is_primary,
                INDEX_TYPE as index_type
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            GROUP BY INDEX_NAME, NON_UNIQUE, INDEX_TYPE
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (self.database, table_name))
            results = cursor.fetchall()
        
        indexes = []
        for row in results:
            indexes.append(IndexInfo(
                name=row['name'],
                columns=row['columns'].split(',') if row['columns'] else [],
                is_unique=bool(row['is_unique']),
                is_primary=bool(row['is_primary']),
                index_type=row['index_type'] or 'BTREE'
            ))
        return indexes
    
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        sql = """
            SELECT 
                tc.CONSTRAINT_NAME as name,
                tc.CONSTRAINT_TYPE as constraint_type,
                GROUP_CONCAT(kcu.COLUMN_NAME ORDER BY kcu.ORDINAL_POSITION) as columns,
                kcu.REFERENCED_TABLE_NAME as reference_table,
                GROUP_CONCAT(kcu.REFERENCED_COLUMN_NAME) as reference_columns
            FROM information_schema.TABLE_CONSTRAINTS tc
            JOIN information_schema.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
                AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA
                AND tc.TABLE_NAME = kcu.TABLE_NAME
            WHERE tc.TABLE_SCHEMA = %s AND tc.TABLE_NAME = %s
            GROUP BY tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE, 
                     kcu.REFERENCED_TABLE_NAME
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (self.database, table_name))
            results = cursor.fetchall()
        
        constraints = []
        for row in results:
            constraints.append(ConstraintInfo(
                name=row['name'],
                constraint_type=row['constraint_type'],
                columns=row['columns'].split(',') if row['columns'] else [],
                reference_table=row['reference_table'],
                reference_columns=row['reference_columns'].split(',') if row['reference_columns'] else None
            ))
        return constraints
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        sql = """
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = %s 
            AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (self.database, table_name))
            results = cursor.fetchall()
        return [row['COLUMN_NAME'] for row in results]
    
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        sql = f"SELECT COUNT(*) as cnt FROM `{table_name}`"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        with self._connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
        return result['cnt']
    
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        cols = ', '.join([f'`{c}`' for c in columns]) if columns else '*'
        sql = f"SELECT {cols} FROM `{table_name}`"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"
        
        sql += f" LIMIT {limit} OFFSET {offset}"
        
        with self._connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    
    def get_version(self) -> str:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            result = cursor.fetchone()
        return result['VERSION()']
