import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Card, Row, Col, Statistic, Button, Table, Tag, message } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined } from '@ant-design/icons';

const Result: React.FC = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();

  const handleExport = () => {
    message.loading({ content: '正在生成报告...', key: 'export' });
    setTimeout(() => {
      message.success({ content: '报告导出成功！', key: 'export', duration: 2 });
    }, 1500);
  };

  const summary = {
    totalTables: 150,
    structureMatchTables: 148,
    structureDiffTables: 2,
    dataMatchTables: 145,
    dataDiffTables: 5,
  };

  const structureColumns = [
    { title: '表名', dataIndex: 'tableName' },
    { title: '差异类型', dataIndex: 'diffType', render: (t: string) => <Tag color="orange">{t}</Tag> },
    { title: '字段名', dataIndex: 'fieldName' },
    { title: '源库值', dataIndex: 'sourceValue' },
    { title: '目标库值', dataIndex: 'targetValue' },
  ];

  const structureData = [
    { id: '1', tableName: 'users', diffType: 'column_type_diff', fieldName: 'age', sourceValue: 'INT', targetValue: 'VARCHAR(10)' },
    { id: '2', tableName: 'orders', diffType: 'index_diff', fieldName: 'idx_status', sourceValue: '存在', targetValue: '缺失' },
  ];

  const dataColumns = [
    { title: '表名', dataIndex: 'tableName' },
    { title: '主键', dataIndex: 'primaryKey', render: (pk: any) => JSON.stringify(pk) },
    { title: '差异类型', dataIndex: 'diffType', render: (t: string) => <Tag color="red">{t}</Tag> },
    { title: '差异字段', dataIndex: 'diffColumns', render: (cols: string[]) => cols.join(', ') },
  ];

  const dataDiffs = [
    { id: '1', tableName: 'users', primaryKey: { id: 1001 }, diffType: 'value_diff', diffColumns: ['status'] },
    { id: '2', tableName: 'orders', primaryKey: { id: 5002 }, diffType: 'row_missing_in_target', diffColumns: [] },
  ];

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%' }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/history')}>返回历史记录</Button>
        <Button type="primary" icon={<DownloadOutlined />} onClick={handleExport}>导出报告</Button>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}><Card><Statistic title="总表数" value={summary.totalTables} /></Card></Col>
        <Col span={6}><Card><Statistic title="结构差异表" value={summary.structureDiffTables} valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="数据差异表" value={summary.dataDiffTables} valueStyle={{ color: '#cf1322' }} /></Card></Col>
        <Col span={6}><Card><Statistic title="完全一致表" value={summary.dataMatchTables} valueStyle={{ color: '#3f8600' }} /></Card></Col>
      </Row>

      <Card bordered={false}>
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab="结构差异" key="1">
            <Table columns={structureColumns} dataSource={structureData} rowKey="id" />
          </Tabs.TabPane>
          <Tabs.TabPane tab="数据差异" key="2">
            <Table columns={dataColumns} dataSource={dataDiffs} rowKey="id" />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Result;
