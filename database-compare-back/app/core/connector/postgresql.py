"""PostgreSQL数据库连接器"""
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any
import time
from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class PostgreSQLConnector(BaseConnector):
    """PostgreSQL数据库连接器"""
    
    def connect(self) -> bool:
        try:
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                connect_timeout=self.timeout,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return True
        except Exception as e:
            raise ConnectionError(f"PostgreSQL连接失败: {str(e)}")
    
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
                "version": f"PostgreSQL {version}",
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
        schema = self.schema or 'public'
        sql = """
            SELECT 
                t.table_name as name,
                t.table_schema as schema,
                obj_description(c.oid) as comment,
                COALESCE(s.n_live_tup, 0) as row_count
            FROM information_schema.tables t
            LEFT JOIN pg_class c ON c.relname = t.table_name
            LEFT JOIN pg_stat_user_tables s ON s.relname = t.table_name
            WHERE t.table_schema = %s
            AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (schema,))
            results = cursor.fetchall()
        
        return [TableInfo(
            name=row['name'],
            schema=row['schema'],
            comment=row['comment'],
            row_count=row['row_count'] or 0
        ) for row in results]
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        schema = self.schema or 'public'
        sql = """
            SELECT 
                c.column_name as name,
                c.data_type as data_type,
                c.character_maximum_length as length,
                c.numeric_precision as precision,
                c.numeric_scale as scale,
                c.is_nullable = 'YES' as nullable,
                c.column_default as default_value,
                col_description(t.oid, c.ordinal_position) as comment,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key
            FROM information_schema.columns c
            JOIN pg_class t ON t.relname = c.table_name
            LEFT JOIN (
                SELECT ku.column_name, ku.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage ku
                    ON tc.constraint_name = ku.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
            ) pk ON pk.table_name = c.table_name AND pk.column_name = c.column_name
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (schema, table_name))
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
        schema = self.schema or 'public'
        sql = """
            SELECT
                i.relname as name,
                array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as columns,
                ix.indisunique as is_unique,
                ix.indisprimary as is_primary,
                am.amname as index_type
            FROM pg_index ix
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_am am ON am.oid = i.relam
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE n.nspname = %s AND t.relname = %s
            GROUP BY i.relname, ix.indisunique, ix.indisprimary, am.amname
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (schema, table_name))
            results = cursor.fetchall()
        
        return [IndexInfo(
            name=row['name'],
            columns=list(row['columns']) if row['columns'] else [],
            is_unique=bool(row['is_unique']),
            is_primary=bool(row['is_primary']),
            index_type=row['index_type'] or 'btree'
        ) for row in results]
    
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        schema = self.schema or 'public'
        sql = """
            SELECT
                tc.constraint_name as name,
                tc.constraint_type as constraint_type,
                array_agg(kcu.column_name ORDER BY kcu.ordinal_position) as columns,
                ccu.table_name as reference_table,
                array_agg(ccu.column_name) as reference_columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            LEFT JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name AND tc.constraint_type = 'FOREIGN KEY'
            WHERE tc.table_schema = %s AND tc.table_name = %s
            GROUP BY tc.constraint_name, tc.constraint_type, ccu.table_name
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (schema, table_name))
            results = cursor.fetchall()
        
        return [ConstraintInfo(
            name=row['name'],
            constraint_type=row['constraint_type'],
            columns=list(row['columns']) if row['columns'] else [],
            reference_table=row['reference_table'],
            reference_columns=list(row['reference_columns']) if row['reference_columns'] and row['reference_columns'][0] else None
        ) for row in results]
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        schema = self.schema or 'public'
        sql = """
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = %s
            AND tc.table_name = %s
            AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """
        with self._connection.cursor() as cursor:
            cursor.execute(sql, (schema, table_name))
            results = cursor.fetchall()
        return [row['column_name'] for row in results]
    
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        schema = self.schema or 'public'
        sql = f'SELECT COUNT(*) as cnt FROM "{schema}"."{table_name}"'
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        with self._connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchone()
        return result['cnt']
    
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        schema = self.schema or 'public'
        cols = ', '.join([f'"{c}"' for c in columns]) if columns else '*'
        sql = f'SELECT {cols} FROM "{schema}"."{table_name}"'
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"
        
        sql += f" LIMIT {limit} OFFSET {offset}"
        
        with self._connection.cursor() as cursor:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_version(self) -> str:
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            result = cursor.fetchone()
        return result['version'].split(',')[0] if result else ''
