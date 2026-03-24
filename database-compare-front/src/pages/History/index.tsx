import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Space, Card, Popconfirm, message, Pagination } from 'antd';
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

  const fetchHistory = async (page = 1, pageSize = 20) => {
    setLoading(true);
    try {
      const response = await historyApi.getList({ page, page_size: pageSize });
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
    fetchHistory();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await historyApi.delete(id);
      message.success('删除成功');
      fetchHistory(pageInfo.page, pageInfo.page_size);
    } catch (e) {
      message.error('删除失败');
    }
  };

  const handlePageChange = (page: number, pageSize: number) => {
    fetchHistory(page, pageSize);
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
      default: return status;
    }
  };

  const columns = [
    { title: '任务ID', dataIndex: 'id', width: 200 },
    { title: '源数据库', dataIndex: 'sourceName', render: (v: string, r: HistoryItem) => v || r.sourceId },
    { title: '目标数据库', dataIndex: 'targetName', render: (v: string, r: HistoryItem) => v || r.targetId },
    { 
      title: '状态', 
      dataIndex: 'status', 
      width: 100,
      render: (s: string) => <Tag color={getStatusColor(s)}>{getStatusText(s)}</Tag> 
    },
    { title: '开始时间', dataIndex: 'startedAt', width: 180 },
    { title: '完成时间', dataIndex: 'completedAt', width: 180 },
    { 
      title: '操作', 
      key: 'action',
      width: 150,
      render: (_: any, record: HistoryItem) => (
        <Space>
          <Button type="link" onClick={() => navigate(`/result/${record.id}`)}>查看结果</Button>
          <Popconfirm title="确定删除此记录吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%' }}>
      <Card title="历史记录" bordered={false}>
        <Table 
          columns={columns} 
          dataSource={data} 
          rowKey="id" 
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
