"""数据源服务"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid

from app.models.datasource import DataSource, DataSourceGroup
from app.schemas.datasource import (
    CreateDataSourceRequest, UpdateDataSourceRequest,
    DataSourceResponse, TestConnectionRequest, TestConnectionResult,
    TableInfo, TableSchema, ColumnInfo, IndexInfo, ConstraintInfo,
    CreateGroupRequest, UpdateGroupRequest, DataSourceGroupResponse
)
from app.core.connector import ConnectorFactory
from app.utils.crypto import encrypt, decrypt


class DataSourceService:
    """数据源服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 数据源操作 ====================
    
    def get_list(self, group_id: str = None, keyword: str = None, 
                 db_type: str = None) -> List[DataSourceResponse]:
        """获取数据源列表"""
        query = self.db.query(DataSource)
        
        if group_id:
            query = query.filter(DataSource.group_id == group_id)
        if db_type:
            query = query.filter(DataSource.db_type == db_type)
        if keyword:
            query = query.filter(
                DataSource.name.contains(keyword) | 
                DataSource.host.contains(keyword)
            )
        
        datasources = query.order_by(DataSource.created_at.desc()).all()
        
        result = []
        for ds in datasources:
            group_name = None
            if ds.group_id:
                group = self.db.query(DataSourceGroup).filter(
                    DataSourceGroup.id == ds.group_id
                ).first()
                group_name = group.name if group else None
            
            result.append(DataSourceResponse(
                id=ds.id,
                name=ds.name,
                group_id=ds.group_id,
                group_name=group_name,
                db_type=ds.db_type,
                host=ds.host,
                port=ds.port,
                database=ds.database,
                schema=ds.schema,
                username=ds.username,
                charset=ds.charset,
                timeout=ds.timeout,
                created_at=ds.created_at,
                updated_at=ds.updated_at
            ))
        
        return result
    
    def get_by_id(self, ds_id: str) -> Optional[DataSourceResponse]:
        """获取单个数据源"""
        ds = self.db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return None
        
        group_name = None
        if ds.group_id:
            group = self.db.query(DataSourceGroup).filter(
                DataSourceGroup.id == ds.group_id
            ).first()
            group_name = group.name if group else None
        
        return DataSourceResponse(
            id=ds.id,
            name=ds.name,
            group_id=ds.group_id,
            group_name=group_name,
            db_type=ds.db_type,
            host=ds.host,
            port=ds.port,
            database=ds.database,
            schema=ds.schema,
            username=ds.username,
            charset=ds.charset,
            timeout=ds.timeout,
            created_at=ds.created_at,
            updated_at=ds.updated_at
        )
    
    def create(self, data: CreateDataSourceRequest) -> DataSourceResponse:
        """创建数据源"""
        ds = DataSource(
            id=str(uuid.uuid4()),
            name=data.name,
            group_id=data.group_id,
            db_type=data.db_type,
            host=data.host,
            port=data.port,
            database=data.database,
            schema=data.schema,
            username=data.username,
            password_encrypted=encrypt(data.password),
            charset=data.charset,
            timeout=data.timeout
        )
        
        self.db.add(ds)
        self.db.commit()
        self.db.refresh(ds)
        
        return self.get_by_id(ds.id)
    
    def update(self, ds_id: str, data: UpdateDataSourceRequest) -> Optional[DataSourceResponse]:
        """更新数据源"""
        ds = self.db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        
        # 处理密码加密
        if 'password' in update_data:
            update_data['password_encrypted'] = encrypt(update_data.pop('password'))
        
        for key, value in update_data.items():
            if hasattr(ds, key):
                setattr(ds, key, value)
        
        self.db.commit()
        self.db.refresh(ds)
        
        return self.get_by_id(ds.id)
    
    def delete(self, ds_id: str) -> bool:
        """删除数据源"""
        ds = self.db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return False
        
        self.db.delete(ds)
        self.db.commit()
        return True
    
    def test_connection_by_id(self, ds_id: str) -> TestConnectionResult:
        """测试已保存数据源的连接"""
        ds = self.db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return TestConnectionResult(
                success=False,
                message="数据源不存在"
            )
        
        return self._test_connection(
            db_type=ds.db_type,
            host=ds.host,
            port=ds.port,
            database=ds.database,
            schema=ds.schema,
            username=ds.username,
            password=decrypt(ds.password_encrypted),
            charset=ds.charset,
            timeout=ds.timeout
        )
    
    def test_connection_direct(self, data: TestConnectionRequest) -> TestConnectionResult:
        """直接测试连接（不保存）"""
        return self._test_connection(
            db_type=data.db_type,
            host=data.host,
            port=data.port,
            database=data.database,
            schema=data.schema,
            username=data.username,
            password=data.password,
            charset=data.charset,
            timeout=data.timeout
        )
    
    def _test_connection(self, **kwargs) -> TestConnectionResult:
        """测试连接实现"""
        try:
            connector = ConnectorFactory.create(**kwargs)
            result = connector.test_connection()
            return TestConnectionResult(**result)
        except ValueError as e:
            return TestConnectionResult(
                success=False,
                message=str(e)
            )
        except Exception as e:
            return TestConnectionResult(
                success=False,
                message=f"连接失败: {str(e)}"
            )
    
    def get_tables(self, ds_id: str, schema: str = None) -> List[TableInfo]:
        """获取表列表"""
        ds = self.db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return []
        
        try:
            connector = ConnectorFactory.create(
                db_type=ds.db_type,
                host=ds.host,
                port=ds.port,
                database=ds.database,
                schema=schema or ds.schema,
                username=ds.username,
                password=decrypt(ds.password_encrypted),
                charset=ds.charset,
                timeout=ds.timeout
            )
            
            with connector:
                tables = connector.get_tables()
                return [TableInfo(
                    name=t.name,
                    schema=t.schema,
                    comment=t.comment,
                    row_count=t.row_count
                ) for t in tables]
        except Exception as e:
            raise ValueError(f"获取表列表失败: {str(e)}")
    
    def get_table_schema(self, ds_id: str, table_name: str) -> Optional[TableSchema]:
        """获取表结构"""
        ds = self.db.query(DataSource).filter(DataSource.id == ds_id).first()
        if not ds:
            return None
        
        try:
            connector = ConnectorFactory.create(
                db_type=ds.db_type,
                host=ds.host,
                port=ds.port,
                database=ds.database,
                schema=ds.schema,
                username=ds.username,
                password=decrypt(ds.password_encrypted),
                charset=ds.charset,
                timeout=ds.timeout
            )
            
            with connector:
                columns = connector.get_columns(table_name)
                indexes = connector.get_indexes(table_name)
                constraints = connector.get_constraints(table_name)
                
                return TableSchema(
                    table_name=table_name,
                    columns=[ColumnInfo(
                        name=c.name,
                        data_type=c.data_type,
                        length=c.length,
                        precision=c.precision,
                        scale=c.scale,
                        nullable=c.nullable,
                        default_value=c.default_value,
                        comment=c.comment,
                        is_primary_key=c.is_primary_key
                    ) for c in columns],
                    indexes=[IndexInfo(
                        name=i.name,
                        columns=i.columns,
                        is_unique=i.is_unique,
                        is_primary=i.is_primary,
                        index_type=i.index_type
                    ) for i in indexes],
                    constraints=[ConstraintInfo(
                        name=c.name,
                        constraint_type=c.constraint_type,
                        columns=c.columns,
                        reference_table=c.reference_table,
                        reference_columns=c.reference_columns
                    ) for c in constraints]
                )
        except Exception as e:
            raise ValueError(f"获取表结构失败: {str(e)}")
    
    def get_datasource_model(self, ds_id: str) -> Optional[DataSource]:
        """获取数据源模型（内部使用）"""
        return self.db.query(DataSource).filter(DataSource.id == ds_id).first()
    
    # ==================== 分组操作 ====================
    
    def get_groups(self) -> List[DataSourceGroupResponse]:
        """获取分组列表"""
        groups = self.db.query(DataSourceGroup).order_by(
            DataSourceGroup.sort_order, DataSourceGroup.name
        ).all()
        
        result = []
        for group in groups:
            count = self.db.query(DataSource).filter(
                DataSource.group_id == group.id
            ).count()
            
            result.append(DataSourceGroupResponse(
                id=group.id,
                name=group.name,
                count=count,
                sort_order=group.sort_order
            ))
        
        return result
    
    def create_group(self, data: CreateGroupRequest) -> DataSourceGroupResponse:
        """创建分组"""
        # 获取最大排序号
        max_order = self.db.query(DataSourceGroup).count()
        
        group = DataSourceGroup(
            id=str(uuid.uuid4()),
            name=data.name,
            sort_order=max_order + 1
        )
        
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        return DataSourceGroupResponse(
            id=group.id,
            name=group.name,
            count=0,
            sort_order=group.sort_order
        )
    
    def update_group(self, group_id: str, data: UpdateGroupRequest) -> Optional[DataSourceGroupResponse]:
        """更新分组"""
        group = self.db.query(DataSourceGroup).filter(
            DataSourceGroup.id == group_id
        ).first()
        
        if not group:
            return None
        
        if data.name is not None:
            group.name = data.name
        if data.sort_order is not None:
            group.sort_order = data.sort_order
        
        self.db.commit()
        self.db.refresh(group)
        
        count = self.db.query(DataSource).filter(
            DataSource.group_id == group.id
        ).count()
        
        return DataSourceGroupResponse(
            id=group.id,
            name=group.name,
            count=count,
            sort_order=group.sort_order
        )
    
    def delete_group(self, group_id: str) -> bool:
        """删除分组"""
        group = self.db.query(DataSourceGroup).filter(
            DataSourceGroup.id == group_id
        ).first()
        
        if not group:
            return False
        
        # 将该分组下的数据源的group_id置为null
        self.db.query(DataSource).filter(
            DataSource.group_id == group_id
        ).update({DataSource.group_id: None})
        
        self.db.delete(group)
        self.db.commit()
        return True
