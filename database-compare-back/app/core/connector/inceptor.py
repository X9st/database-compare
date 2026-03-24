"""Inceptor数据库连接器"""
from typing import List, Dict, Any, Optional
from .base import BaseConnector, TableInfo, ColumnInfo, IndexInfo, ConstraintInfo


class InceptorConnector(BaseConnector):
    """Inceptor数据库连接器 (基于Hive兼容驱动)"""
    
    def __init__(self, host: str, port: int, database: str,
                 username: str, password: str, schema: str = None,
                 charset: str = "UTF-8", timeout: int = 30):
        super().__init__(host, port, database, username, password, schema, charset, timeout)
        self._cursor = None
    
    def connect(self) -> bool:
        """建立连接"""
        try:
            from pyhive import hive
            
            self._connection = hive.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database or 'default',
                auth='LDAP' if self.password else 'NONE'
            )
            self._cursor = self._connection.cursor()
            return True
        except ImportError:
            raise ConnectionError("未安装pyhive驱动，请执行: pip install pyhive")
        except Exception as e:
            raise ConnectionError(f"Inceptor连接失败: {str(e)}")
    
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
        self._cursor.execute("SHOW TABLES")
        results = self._cursor.fetchall()
        
        tables = []
        for row in results:
            table_name = row[0]
            # 获取表注释
            try:
                self._cursor.execute(f"DESCRIBE FORMATTED {table_name}")
                desc_results = self._cursor.fetchall()
                comment = None
                for desc_row in desc_results:
                    if desc_row[0] and 'Table Parameters' in str(desc_row[0]):
                        continue
                    if desc_row[0] and 'comment' in str(desc_row[0]).lower():
                        comment = desc_row[1] if len(desc_row) > 1 else None
                        break
            except:
                comment = None
            
            tables.append(TableInfo(
                name=table_name,
                schema=self.database,
                comment=comment,
                row_count=0  # Inceptor获取行数成本高，默认为0
            ))
        return tables
    
    def get_columns(self, table_name: str) -> List[ColumnInfo]:
        """获取表字段"""
        self._cursor.execute(f"DESCRIBE {table_name}")
        results = self._cursor.fetchall()
        
        columns = []
        is_partition_section = False
        
        for row in results:
            col_name = row[0].strip() if row[0] else ''
            
            # 跳过分区信息部分
            if col_name.startswith('#') or col_name == '' or 'Partition' in col_name:
                if 'Partition' in col_name:
                    is_partition_section = True
                continue
            
            if is_partition_section:
                continue
            
            data_type = row[1].strip() if len(row) > 1 and row[1] else 'string'
            comment = row[2].strip() if len(row) > 2 and row[2] else None
            
            # 解析数据类型和长度
            length = None
            precision = None
            scale = None
            
            if '(' in data_type:
                type_name = data_type.split('(')[0]
                params = data_type.split('(')[1].rstrip(')')
                if ',' in params:
                    precision = int(params.split(',')[0])
                    scale = int(params.split(',')[1])
                else:
                    length = int(params)
                data_type = type_name
            
            columns.append(ColumnInfo(
                name=col_name,
                data_type=data_type,
                length=length,
                precision=precision,
                scale=scale,
                nullable=True,  # Hive/Inceptor 默认允许空值
                default_value=None,
                comment=comment,
                is_primary_key=False  # Hive/Inceptor 不支持主键
            ))
        return columns
    
    def get_indexes(self, table_name: str) -> List[IndexInfo]:
        """获取表索引 (Inceptor不支持传统索引)"""
        return []
    
    def get_constraints(self, table_name: str) -> List[ConstraintInfo]:
        """获取表约束 (Inceptor不支持传统约束)"""
        return []
    
    def get_primary_keys(self, table_name: str) -> List[str]:
        """获取主键字段 (Inceptor不支持主键，返回空列表)"""
        return []
    
    def get_row_count(self, table_name: str, where_clause: str = None) -> int:
        """获取行数"""
        sql = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        self._cursor.execute(sql)
        result = self._cursor.fetchone()
        return result[0] if result else 0
    
    def fetch_data(self, table_name: str, columns: List[str] = None,
                   where_clause: str = None, order_by: List[str] = None,
                   offset: int = 0, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取数据"""
        cols = ', '.join([f'`{c}`' for c in columns]) if columns else '*'
        sql = f"SELECT {cols} FROM {table_name}"
        
        if where_clause:
            sql += f" WHERE {where_clause}"
        
        if order_by:
            sql += f" ORDER BY {', '.join(order_by)}"
        
        sql += f" LIMIT {limit}"
        
        if offset > 0:
            # Hive SQL 不直接支持 OFFSET，使用子查询模拟
            # 这里简化处理，对于大数据量应使用其他方案
            pass
        
        self._cursor.execute(sql)
        
        # 获取列名
        if columns:
            col_names = columns
        else:
            col_names = [desc[0] for desc in self._cursor.description]
        
        results = self._cursor.fetchall()
        return [dict(zip(col_names, row)) for row in results]
    
    def get_version(self) -> str:
        """获取数据库版本"""
        try:
            self._cursor.execute("SELECT version()")
            result = self._cursor.fetchone()
            return result[0] if result else "Unknown"
        except:
            return "Inceptor"
