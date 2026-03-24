import React, { useEffect, useState } from 'react';
import { Button, Space, Input, message } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import DataSourceList from './DataSourceList';
import DataSourceForm from './DataSourceForm';
import styles from './index.module.less';

const DataSource: React.FC = () => {
  const { dataSources, loading, fetchDataSources, deleteDataSource, testConnection } = 
    useDataSourceStore();
  const [formVisible, setFormVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');

  useEffect(() => {
    fetchDataSources();
  }, [fetchDataSources]);

  const handleAdd = () => {
    setEditingId(null);
    setFormVisible(true);
  };

  const handleEdit = (id: string) => {
    setEditingId(id);
    setFormVisible(true);
  };

  const handleDelete = async (id: string) => {
    await deleteDataSource(id);
    message.success('删除成功');
  };

  const handleTest = async (id: string) => {
    const result = await testConnection(id);
    if (result.success) {
      message.success(`连接成功，延迟: ${result.latency}ms`);
    } else {
      message.error(`连接失败: ${result.message}`);
    }
  };

  const filteredDataSources = dataSources.filter(
    (ds) => ds.name.includes(searchKeyword) || ds.host.includes(searchKeyword)
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>数据源管理</h2>
        <Space>
          <Input
            placeholder="搜索数据源"
            prefix={<SearchOutlined />}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ width: 200 }}
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增数据源
          </Button>
        </Space>
      </div>

      <DataSourceList
        dataSource={filteredDataSources}
        loading={loading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onTest={handleTest}
      />

      <DataSourceForm
        visible={formVisible}
        editingId={editingId}
        onClose={() => setFormVisible(false)}
        onSuccess={() => {
          setFormVisible(false);
          fetchDataSources();
        }}
      />
    </div>
  );
};

export default DataSource;
