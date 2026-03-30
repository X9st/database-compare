"""Oracle数据库连接器"""
from typing import List, Dict, Any, Optional
from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class OracleConnector(BaseConnector):
    """Oracle数据库连接器"""
    
    def __init__(self, host: str, port: int, database: str,
                 username: str, password: str, schema: str = None,
                 charset: str = "UTF-8", timeout: int = 30,
                 extra_config: Optional[Dict[str, Any]] = None):
        super().__init__(
            host,
            port,
            database,
            username,
            password,
            schema,
            charset,
            timeout,
            extra_config=extra_config,
        )
        self._cursor = None
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            import oracledb
            
            # 构建DSN
            dsn = oracledb.makedsn(self.host, self.port, service_name=self.database)
            
            self._connection = oracledb.connect(
                user=self.username,
                password=self.password,
                dsn=dsn
            )
            return True
        except ImportError:
            raise ConnectionError("未安装oracledb驱动，请执行: pip install oracledb")
        except Exception as e:
            raise ConnectionError(f"Oracle连接失败: {str(e)}")
    
    def disconnect(self) -> None:
        """断开连接"""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
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
        schema = self.schema or self.username.upper()
        sql = """
            SELECT 
                t.TABLE_NAME as name,
                :schema as schema_name,
                tc.COMMENTS as comments,
                t.NUM_ROWS as row_count
            FROM ALL_TABLES t
            LEFT JOIN ALL_TAB_COMMENTS tc 
                ON t.OWNER = tc.OWNER AND t.TABLE_NAME = tc.TABLE_NAME
            WHERE t.OWNER = :schema
            ORDER BY t.TABLE_NAME
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, schema=schema)
        results = cursor.fetchall()
        cursor.close()
        
        tables = []
        for row in results:
            tables.append(TableInfo(
                name=row[0],
                schema=row[1],
                comment=row[2],
                row_count=row[3] or 0
            ))
        return tables
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """获取表字段"""
        schema = self.schema or self.username.upper()
        sql = """
            SELECT 
                c.COLUMN_NAME as name,
                c.DATA_TYPE as data_type,
                c.DATA_LENGTH as length,
                c.DATA_PRECISION as precision,
                c.DATA_SCALE as scale,
                CASE WHEN c.NULLABLE = 'Y' THEN 1 ELSE 0 END as nullable,
                c.DATA_DEFAULT as default_value,
                cc.COMMENTS as comments,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 1 ELSE 0 END as is_primary_key
            FROM ALL_TAB_COLUMNS c
            LEFT JOIN ALL_COL_COMMENTS cc 
                ON c.OWNER = cc.OWNER AND c.TABLE_NAME = cc.TABLE_NAME AND c.COLUMN_NAME = cc.COLUMN_NAME
            LEFT JOIN (
                SELECT cols.OWNER, cols.TABLE_NAME, cols.COLUMN_NAME
                FROM ALL_CONS_COLUMNS cols
                JOIN ALL_CONSTRAINTS cons 
                    ON cols.OWNER = cons.OWNER 
                    AND cols.CONSTRAINT_NAME = cons.CONSTRAINT_NAME
                WHERE cons.CONSTRAINT_TYPE = 'P'
            ) pk ON c.OWNER = pk.OWNER AND c.TABLE_NAME = pk.TABLE_NAME AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE c.OWNER = :schema AND c.TABLE_NAME = :table_name
            ORDER BY c.COLUMN_ID
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, schema=schema, table_name=table_name.upper())
        results = cursor.fetchall()
        cursor.close()
        
        columns = []
        for row in results:
            columns.append(ColumnInfo(
                name=row[0],
                data_type=row[1],
                length=row[2],
                precision=row[3],
                scale=row[4],
                nullable=bool(row[5]),
                default_value=str(row[6]).strip() if row[6] else None,
                comment=row[7],
                is_primary_key=bool(row[8])
            ))
        return columns
    
    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        """获取表索引"""
        schema = self.schema or self.username.upper()
        sql = """
            SELECT 
                i.INDEX_NAME as name,
                LISTAGG(ic.COLUMN_NAME, ',') WITHIN GROUP (ORDER BY ic.COLUMN_POSITION) as columns,
                CASE WHEN i.UNIQUENESS = 'UNIQUE' THEN 1 ELSE 0 END as is_unique,
                CASE WHEN c.CONSTRAINT_TYPE = 'P' THEN 1 ELSE 0 END as is_primary,
                i.INDEX_TYPE as index_type
            FROM ALL_INDEXES i
            JOIN ALL_IND_COLUMNS ic ON i.OWNER = ic.INDEX_OWNER AND i.INDEX_NAME = ic.INDEX_NAME
            LEFT JOIN ALL_CONSTRAINTS c ON i.OWNER = c.OWNER 
                AND i.INDEX_NAME = c.INDEX_NAME AND c.CONSTRAINT_TYPE = 'P'
            WHERE i.OWNER = :schema AND i.TABLE_NAME = :table_name
            GROUP BY i.INDEX_NAME, i.UNIQUENESS, c.CONSTRAINT_TYPE, i.INDEX_TYPE
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, schema=schema, table_name=table_name.upper())
        results = cursor.fetchall()
        cursor.close()
        
        indexes = []
        for row in results:
            indexes.append(IndexInfo(
                name=row[0],
                columns=row[1].split(',') if row[1] else [],
                is_unique=bool(row[2]),
                is_primary=bool(row[3]),
                index_type=row[4]
            ))
        return indexes
    
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """获取表约束"""
        schema = self.schema or self.username.upper()
        sql = """
            SELECT 
                c.CONSTRAINT_NAME as name,
                c.CONSTRAINT_TYPE as constraint_type,
                LISTAGG(cc.COLUMN_NAME, ',') WITHIN GROUP (ORDER BY cc.POSITION) as columns,
                r.TABLE_NAME as reference_table,
                NULL as reference_columns
            FROM ALL_CONSTRAINTS c
            JOIN ALL_CONS_COLUMNS cc ON c.OWNER = cc.OWNER AND c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
            LEFT JOIN ALL_CONSTRAINTS r ON c.R_OWNER = r.OWNER AND c.R_CONSTRAINT_NAME = r.CONSTRAINT_NAME
            WHERE c.OWNER = :schema AND c.TABLE_NAME = :table_name
            GROUP BY c.CONSTRAINT_NAME, c.CONSTRAINT_TYPE, r.TABLE_NAME
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, schema=schema, table_name=table_name.upper())
        results = cursor.fetchall()
        cursor.close()
        
        constraints = []
        for row in results:
            constraint_type_map = {
                'P': 'PRIMARY KEY',
                'U': 'UNIQUE',
                'R': 'FOREIGN KEY',
                'C': 'CHECK'
            }
            constraints.append(ConstraintInfo(
                name=row[0],
                constraint_type=constraint_type_map.get(row[1], row[1]),
                columns=row[2].split(',') if row[2] else [],
                reference_table=row[3],
                reference_columns=row[4].split(',') if row[4] else None
            ))
        return constraints
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键字段"""
        schema = self.schema or self.username.upper()
        sql = """
            SELECT cc.COLUMN_NAME
            FROM ALL_CONSTRAINTS c
            JOIN ALL_CONS_COLUMNS cc ON c.OWNER = cc.OWNER AND c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
            WHERE c.OWNER = :schema 
            AND c.TABLE_NAME = :table_name 
            AND c.CONSTRAINT_TYPE = 'P'
            ORDER BY cc.POSITION
        """
        cursor = self._connection.cursor()
        cursor.execute(sql, schema=schema, table_name=table_name.upper())
        results = cursor.fetchall()
        cursor.close()
        return [row[0] for row in results]
    
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        """获取行数"""
        schema = self.schema or self.username.upper()
        sql = f'SELECT COUNT(*) FROM "{schema}"."{table_name.upper()}"'
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        cursor = self._connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        return result[0]
    
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取数据"""
        schema = self.schema or self.username.upper()
        cols = ', '.join([f'"{c}"' for c in columns]) if columns else '*'
        
        sql = f'SELECT {cols} FROM "{schema}"."{table_name.upper()}"'
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"
        
        # Oracle 12c+ 使用 OFFSET/FETCH
        sql += f" OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY"
        
        cursor = self._connection.cursor()
        cursor.execute(sql)
        
        # 获取列名
        col_names = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        cursor.close()
        
        return [dict(zip(col_names, row)) for row in results]
    
    def get_version(self) -> str:
        """获取数据库版本"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT BANNER FROM V$VERSION WHERE ROWNUM = 1")
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else "Unknown"
