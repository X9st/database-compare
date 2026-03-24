"""SQL Server数据库连接器"""
from typing import List, Dict, Any, Optional
from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class SQLServerConnector(BaseConnector):
    """SQL Server数据库连接器"""
    
    def __init__(self, host: str, port: int, database: str,
                 username: str, password: str, schema: str = None,
                 charset: str = "UTF-8", timeout: int = 30):
        super().__init__(host, port, database, username, password, schema, charset, timeout)
        self.schema = schema or 'dbo'
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            import pymssql
            
            self._connection = pymssql.connect(
                server=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset=self.charset.replace('-', '').lower(),
                login_timeout=self.timeout,
                as_dict=True
            )
            return True
        except ImportError:
            raise ConnectionError("未安装pymssql驱动，请执行: pip install pymssql")
        except Exception as e:
            raise ConnectionError(f"SQL Server连接失败: {str(e)}")
    
    def disconnect(self) -> None:
        """断开连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        try:
            self.connect()
            version = self.get_version()
            self.disconnect()
            return {
                "success": True,
                "message": "连接成功",
                "version": version
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "version": None
            }
    
    def get_tables(self) -> List[TableInfo]:
        """获取表列表"""
        sql = """
            SELECT 
                t.TABLE_NAME as name,
                t.TABLE_SCHEMA as [schema],
                ep.value as comment,
                p.rows as row_count
            FROM INFORMATION_SCHEMA.TABLES t
            LEFT JOIN sys.tables st ON t.TABLE_NAME = st.name
            LEFT JOIN sys.extended_properties ep ON st.object_id = ep.major_id 
                AND ep.minor_id = 0 AND ep.name = 'MS_Description'
            LEFT JOIN sys.partitions p ON st.object_id = p.object_id AND p.index_id IN (0, 1)
            WHERE t.TABLE_SCHEMA = %s AND t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, (self.schema,))
        results = cursor.fetchall()
        cursor.close()
        
        tables = []
        for row in results:
            tables.append(TableInfo(
                name=row['name'],
                schema=row['schema'],
                comment=row['comment'],
                row_count=row['row_count'] or 0
            ))
        return tables
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """获取表字段"""
        sql = """
            SELECT 
                c.COLUMN_NAME as name,
                c.DATA_TYPE as data_type,
                c.CHARACTER_MAXIMUM_LENGTH as length,
                c.NUMERIC_PRECISION as precision,
                c.NUMERIC_SCALE as scale,
                CASE WHEN c.IS_NULLABLE = 'YES' THEN 1 ELSE 0 END as nullable,
                c.COLUMN_DEFAULT as default_value,
                ep.value as comment,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as is_primary_key
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN sys.columns sc ON sc.name = c.COLUMN_NAME
            LEFT JOIN sys.tables st ON st.name = c.TABLE_NAME AND st.object_id = sc.object_id
            LEFT JOIN sys.extended_properties ep ON st.object_id = ep.major_id 
                AND sc.column_id = ep.minor_id AND ep.name = 'MS_Description'
            LEFT JOIN (
                SELECT ku.COLUMN_NAME, ku.TABLE_NAME, ku.TABLE_SCHEMA
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE ku
                    ON tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ) pk ON c.TABLE_NAME = pk.TABLE_NAME 
                AND c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
                AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE c.TABLE_SCHEMA = %s AND c.TABLE_NAME = %s
            ORDER BY c.ORDINAL_POSITION
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, (self.schema, table_name))
        results = cursor.fetchall()
        cursor.close()
        
        columns = []
        for row in results:
            columns.append(ColumnInfo(
                name=row['name'],
                data_type=row['data_type'],
                length=row['length'],
                precision=row['precision'],
                scale=row['scale'],
                nullable=bool(row['nullable']),
                default_value=row['default_value'],
                comment=row['comment'],
                is_primary_key=bool(row['is_primary_key'])
            ))
        return columns
    
    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        """获取表索引"""
        sql = """
            SELECT 
                i.name as index_name,
                STRING_AGG(c.name, ',') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns,
                i.is_unique,
                i.is_primary_key,
                i.type_desc as index_type
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN sys.tables t ON i.object_id = t.object_id
            JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = %s AND t.name = %s AND i.name IS NOT NULL
            GROUP BY i.name, i.is_unique, i.is_primary_key, i.type_desc
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, (self.schema, table_name))
        results = cursor.fetchall()
        cursor.close()
        
        indexes = []
        for row in results:
            indexes.append(IndexInfo(
                name=row['index_name'],
                columns=row['columns'].split(',') if row['columns'] else [],
                is_unique=bool(row['is_unique']),
                is_primary=bool(row['is_primary_key']),
                index_type=row['index_type']
            ))
        return indexes
    
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """获取表约束"""
        sql = """
            SELECT 
                tc.CONSTRAINT_NAME as name,
                tc.CONSTRAINT_TYPE as constraint_type,
                STRING_AGG(kcu.COLUMN_NAME, ',') as columns,
                rc.UNIQUE_CONSTRAINT_NAME as reference_constraint,
                NULL as reference_table
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu 
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            LEFT JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc 
                ON tc.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = %s AND tc.TABLE_NAME = %s
            GROUP BY tc.CONSTRAINT_NAME, tc.CONSTRAINT_TYPE, rc.UNIQUE_CONSTRAINT_NAME
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, (self.schema, table_name))
        results = cursor.fetchall()
        cursor.close()
        
        constraints = []
        for row in results:
            constraints.append(ConstraintInfo(
                name=row['name'],
                constraint_type=row['constraint_type'],
                columns=row['columns'].split(',') if row['columns'] else [],
                reference_table=row['reference_table'],
                reference_columns=None
            ))
        return constraints
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键字段"""
        sql = """
            SELECT kcu.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
            JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
            WHERE tc.TABLE_SCHEMA = %s 
            AND tc.TABLE_NAME = %s 
            AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
            ORDER BY kcu.ORDINAL_POSITION
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, (self.schema, table_name))
        results = cursor.fetchall()
        cursor.close()
        return [row['COLUMN_NAME'] for row in results]
    
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        """获取行数"""
        sql = f"SELECT COUNT(*) as cnt FROM [{self.schema}].[{table_name}]"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        cursor = self._connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return result['cnt']
    
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取数据"""
        cols = ', '.join([f'[{c}]' for c in columns]) if columns else '*'
        sql = f"SELECT {cols} FROM [{self.schema}].[{table_name}]"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"
        else:
            # SQL Server 需要 ORDER BY 才能使用 OFFSET
            sql += " ORDER BY (SELECT NULL)"
        
        sql += f" OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        cursor = self._connection.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        cursor.close()
        
        return results
    
    def get_version(self) -> str:
        """获取数据库版本"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT @@VERSION")
        result = cursor.fetchone()
        cursor.close()
        # 返回第一行
        for key, value in result.items():
            return str(value).split('\n')[0]
        return "Unknown"
