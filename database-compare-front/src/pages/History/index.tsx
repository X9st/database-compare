import React, { useState } from 'react';
import { Table, Button, Tag, Space, Card, Popconfirm, message } from 'antd';
import { useNavigate } from 'react-router-dom';

const History: React.FC = () => {
  const navigate = useNavigate();

  const [data, setData] = useState([
    { id: 'task_1711234567', sourceDb: '生产环境-MySQL', targetDb: '测试环境-MySQL', status: 'completed', startTime: '2026-03-24 10:00:00' },
    { id: 'task_1711234111', sourceDb: '生产环境-Oracle', targetDb: '测试环境-Oracle', status: 'failed', startTime: '2026-03-23 15:30:00' },
  ]);

  const handleDelete = (id: string) => {
    setData(data.filter(item => item.id !== id));
    message.success('删除成功');
  };

  const columns = [
    { title: '任务ID', dataIndex: 'id' },
    { title: '源数据库', dataIndex: 'sourceDb' },
    { title: '目标数据库', dataIndex: 'targetDb' },
    { title: '状态', dataIndex: 'status', render: (s: string) => <Tag color={s === 'completed' ? 'green' : 'red'}>{s}</Tag> },
    { title: '比对时间', dataIndex: 'startTime' },
    { 
      title: '操作', 
      key: 'action', 
      render: (_: any, record: any) => (
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
        <Table columns={columns} dataSource={data} rowKey="id" />
      </Card>
    </div>
  );
};

export default History;
