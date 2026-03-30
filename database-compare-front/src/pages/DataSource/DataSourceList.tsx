import React from 'react';
import { Table, Button, Space, Popconfirm, Tag } from 'antd';
import { DataSource } from '@/types';

interface Props {
  dataSource: DataSource[];
  loading: boolean;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onTest: (id: string) => void;
  onRefresh: (id: string) => void;
}

const DataSourceList: React.FC<Props> = ({ dataSource, loading, onEdit, onDelete, onTest, onRefresh }) => {
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
      render: (_: string, record: DataSource) => record.database || record.extra_config?.original_name || '-',
    },
    {
      title: '数据集状态',
      key: 'dataset_status',
      render: (_: any, record: DataSource) => {
        const mode = record.extra_config?.mode;
        const snapshot = record.extra_config?.snapshot;
        if (mode !== 'remote_dataset') {
          return '-';
        }
        return (
          <span>
            文件 {snapshot?.file_count || 0} / 表 {snapshot?.table_count || 0}
            <br />
            最近刷新: {snapshot?.last_refresh_at ? new Date(snapshot.last_refresh_at).toLocaleString() : '-'}
            {snapshot?.failed_files?.length ? (
              <>
                <br />
                失败: {snapshot.failed_files.length}
              </>
            ) : null}
          </span>
        );
      },
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
          {record.extra_config?.mode === 'remote_dataset' ? (
            <Button type="link" onClick={() => onRefresh(record.id)}>
              刷新数据集
            </Button>
          ) : null}
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
