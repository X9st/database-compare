import React, { useEffect, useState } from 'react';
import { Button, Space, Input, message, Select, Modal, List } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import DataSourceList from './DataSourceList';
import DataSourceForm from './DataSourceForm';
import styles from './index.module.less';

const DataSource: React.FC = () => {
  const { dataSources, groups, loading, fetchDataSources, deleteDataSource, testConnection, refreshRemoteDataset, fetchGroups, addGroup, updateGroup, deleteGroup } = 
    useDataSourceStore();
  const [formVisible, setFormVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedGroupId, setSelectedGroupId] = useState<string | undefined>(undefined);
  const [groupModalVisible, setGroupModalVisible] = useState(false);
  const [groupInput, setGroupInput] = useState('');
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null);

  useEffect(() => {
    fetchDataSources().catch(() => {});
    fetchGroups().catch(() => {});
  }, [fetchDataSources, fetchGroups]);

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

  const handleRefresh = async (id: string) => {
    try {
      const result = await refreshRemoteDataset(id);
      const failedCount = result.failed_files?.length || 0;
      message.success(`刷新完成：文件 ${result.file_count}，表 ${result.table_count}，失败 ${failedCount}`);
    } catch (e: any) {
      const backendMessage = e?.response?.data?.detail || e?.response?.data?.message || e?.message;
      message.error(`刷新失败: ${backendMessage || '未知错误'}`);
    }
  };

  const filteredDataSources = dataSources.filter(
    (ds) =>
      (ds.name.includes(searchKeyword) || ds.host.includes(searchKeyword)) &&
      (!selectedGroupId || ds.group_id === selectedGroupId)
  );

  const handleSaveGroup = async () => {
    if (!groupInput.trim()) {
      message.warning('请输入分组名称');
      return;
    }
    if (editingGroupId) {
      await updateGroup(editingGroupId, groupInput.trim());
      message.success('分组已更新');
    } else {
      await addGroup(groupInput.trim());
      message.success('分组已创建');
    }
    setGroupInput('');
    setEditingGroupId(null);
    fetchGroups().catch(() => {});
  };

  const handleDeleteGroup = async (id: string) => {
    await deleteGroup(id);
    message.success('分组已删除');
    fetchDataSources().catch(() => {});
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>数据源管理</h2>
        <Space>
          <Select
            allowClear
            style={{ width: 180 }}
            placeholder="按分组筛选"
            value={selectedGroupId}
            onChange={(value) => setSelectedGroupId(value)}
            options={groups.map((group) => ({ label: `${group.name} (${group.count})`, value: group.id }))}
          />
          <Input
            placeholder="搜索数据源"
            prefix={<SearchOutlined />}
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            style={{ width: 200 }}
          />
          <Button onClick={() => setGroupModalVisible(true)}>管理分组</Button>
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
        onRefresh={handleRefresh}
      />

      <DataSourceForm
        visible={formVisible}
        editingId={editingId}
        onClose={() => setFormVisible(false)}
        onSuccess={() => {
          setFormVisible(false);
        }}
      />

      <Modal
        title="数据源分组管理"
        open={groupModalVisible}
        onCancel={() => {
          setGroupModalVisible(false);
          setGroupInput('');
          setEditingGroupId(null);
        }}
        onOk={handleSaveGroup}
        okText={editingGroupId ? '保存修改' : '新增分组'}
      >
        <Space style={{ width: '100%', marginBottom: 12 }}>
          <Input
            value={groupInput}
            onChange={(e) => setGroupInput(e.target.value)}
            placeholder="输入分组名称"
          />
          <Button onClick={() => {
            setGroupInput('');
            setEditingGroupId(null);
          }}>
            清空
          </Button>
        </Space>
        <List
          size="small"
          bordered
          dataSource={groups}
          renderItem={(group) => (
            <List.Item
              actions={[
                <Button type="link" key="edit" onClick={() => {
                  setEditingGroupId(group.id);
                  setGroupInput(group.name);
                }}>
                  编辑
                </Button>,
                <Button type="link" danger key="delete" onClick={() => handleDeleteGroup(group.id)}>
                  删除
                </Button>,
              ]}
            >
              {group.name}（{group.count}）
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
};

export default DataSource;
