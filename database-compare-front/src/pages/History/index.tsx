import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Space, Card, Popconfirm, message, Pagination, Input } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { historyApi, HistoryItem, PageInfo } from '@/services/historyApi';

const History: React.FC = () => {
  const navigate = useNavigate();
  const [data, setData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [pageInfo, setPageInfo] = useState<PageInfo>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  });
  const [keyword, setKeyword] = useState('');

  const fetchHistory = async (page = 1, page_size = 20, keywordValue = keyword) => {
    setLoading(true);
    try {
      const response = await historyApi.getList({
        page,
        page_size,
        keyword: keywordValue || undefined,
      });
      const result = response.data;
      setData(result.data || []);
      if (result.page_info) {
        setPageInfo(result.page_info);
      }
    } catch (e) {
      console.error('Failed to fetch history:', e);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(1, pageInfo.page_size, '');
  }, []);

  const handleDelete = async (task_id: string) => {
    try {
      await historyApi.delete(task_id);
      message.success('删除成功');
      fetchHistory(pageInfo.page, pageInfo.page_size);
    } catch (e) {
      message.error('删除失败');
    }
  };

  const handlePageChange = (page: number, page_size: number) => {
    fetchHistory(page, page_size);
  };

  const handleSearch = () => {
    fetchHistory(1, pageInfo.page_size);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green';
      case 'running': return 'blue';
      case 'paused': return 'orange';
      case 'failed': return 'red';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'running': return '运行中';
      case 'paused': return '已暂停';
      case 'failed': return '失败';
      case 'pending': return '等待中';
      case 'cancelled': return '已取消';
      default: return status;
    }
  };

  const columns = [
    { title: '任务ID', dataIndex: 'task_id', width: 220 },
    { title: '源数据库', key: 'source_db', render: (_: unknown, record: HistoryItem) => record.source_db?.name || record.source_db?.id || '-' },
    { title: '目标数据库', key: 'target_db', render: (_: unknown, record: HistoryItem) => record.target_db?.name || record.target_db?.id || '-' },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: string) => <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
    },
    { title: '表数量', dataIndex: 'table_count', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: HistoryItem) => (
        <Space>
          <Button
            type="link"
            disabled={!record.result_id}
            onClick={() => record.result_id && navigate(`/result/${record.result_id}`)}
          >
            查看结果
          </Button>
          <Popconfirm title="确定删除此记录吗？" onConfirm={() => handleDelete(record.task_id)}>
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%' }}>
      <Card title="历史记录" bordered={false}>
        <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between' }}>
          <Input
            style={{ width: 360 }}
            placeholder="搜索任务ID / 源库名称 / 目标库名称"
            prefix={<SearchOutlined />}
            value={keyword}
            allowClear
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={handleSearch}
          />
          <Button type="primary" onClick={handleSearch}>搜索</Button>
        </div>
        <Table
          columns={columns}
          dataSource={data}
          rowKey="task_id"
          loading={loading}
          pagination={false}
        />
        {pageInfo.total > 0 && (
          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <Pagination
              current={pageInfo.page}
              pageSize={pageInfo.page_size}
              total={pageInfo.total}
              showSizeChanger
              showQuickJumper
              showTotal={(total) => `共 ${total} 条记录`}
              onChange={handlePageChange}
            />
          </div>
        )}
      </Card>
    </div>
  );
};

export default History;
