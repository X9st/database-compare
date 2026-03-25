import React from 'react';
import { Table, Button, Space, Popconfirm, Tag } from 'antd';
import { DataSource } from '@/types';

interface Props {
  dataSource: DataSource[];
  loading: boolean;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
}

const DataSourceList: React.FC<Props> = ({ dataSource, loading, onEdit, onDelete, onTest }) => {
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'db_type',
      key: 'db_type',
      render: (type?: string) => <Tag color="blue">{(type || '-').toUpperCase()}</Tag>,
    },
    {
      title: '主机地址',
      dataIndex: 'host',
      key: 'host',
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
    },
    {
      title: '数据库',
      dataIndex: 'database',
      key: 'database',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: DataSource) => (
        <Space size="middle">
          <Button type="link" onClick={() => onTest(record.id)}>
            测试
          </Button>
          <Button type="link" onClick={() => onEdit(record.id)}>
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个数据源吗？"
            onConfirm={() => onDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={dataSource}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 10 }}
    />
  );
};

export default DataSourceList;
