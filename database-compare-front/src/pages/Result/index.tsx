import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Card, Row, Col, Statistic, Button, Table, Tag, message, Spin, Pagination, Select, Modal } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined } from '@ant-design/icons';
import { resultApi, CompareResultSummary, StructureDiff, DataDiff, PageInfo } from '@/services/resultApi';
import { resolveApiUrl } from '@/services/api';

const { Option } = Select;

const Result: React.FC = () => {
  const { result_id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<CompareResultSummary | null>(null);
  const [structureDiffs, setStructureDiffs] = useState<StructureDiff[]>([]);
  const [structurePageInfo, setStructurePageInfo] = useState<PageInfo>({ page: 1, page_size: 20, total: 0, total_pages: 0 });
  const [dataDiffs, setDataDiffs] = useState<DataDiff[]>([]);
  const [dataPageInfo, setDataPageInfo] = useState<PageInfo>({ page: 1, page_size: 20, total: 0, total_pages: 0 });
  const [exportLoading, setExportLoading] = useState(false);
  const [exportModalVisible, setExportModalVisible] = useState(false);
  const [exportFormat, setExportFormat] = useState<'excel' | 'html' | 'txt'>('excel');

  useEffect(() => {
    if (result_id) {
      fetchResult();
      fetchStructureDiffs(1);
      fetchDataDiffs(1);
    }
  }, [result_id]);

  const fetchResult = async () => {
    if (!result_id) {
      return;
    }
    setLoading(true);
    try {
      const response = await resultApi.getResult(result_id);
      setSummary(response.data?.data || null);
    } catch (e) {
      console.error('Failed to fetch result:', e);
      message.error('获取比对结果失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchStructureDiffs = async (page: number, page_size = 20) => {
    if (!result_id) {
      return;
    }
    try {
      const response = await resultApi.getStructureDiffs(result_id, { page, page_size });
      setStructureDiffs(response.data?.data || []);
      if (response.data?.page_info) {
        setStructurePageInfo(response.data.page_info);
      }
    } catch (e) {
      console.error('Failed to fetch structure diffs:', e);
    }
  };

  const fetchDataDiffs = async (page: number, page_size = 20) => {
    if (!result_id) {
      return;
    }
    try {
      const response = await resultApi.getDataDiffs(result_id, { page, page_size });
      setDataDiffs(response.data?.data || []);
      if (response.data?.page_info) {
        setDataPageInfo(response.data.page_info);
      }
    } catch (e) {
      console.error('Failed to fetch data diffs:', e);
    }
  };

  const handleExport = async () => {
    if (!result_id) {
      return;
    }
    setExportLoading(true);
    try {
      const response = await resultApi.exportReport(result_id, {
        format: exportFormat,
        options: {
          include_structure_diffs: true,
          include_data_diffs: true,
        },
      });
      const result = response.data?.data;
      if (result?.download_url) {
        window.open(resolveApiUrl(result.download_url), '_blank');
      }
      message.success('报告导出成功');
      setExportModalVisible(false);
    } catch (e) {
      message.error('导出失败');
    } finally {
      setExportLoading(false);
    }
  };

  const getDiffTypeColor = (type: string) => {
    switch (type) {
      case 'column_missing': return 'red';
      case 'column_extra': return 'orange';
      case 'column_type_diff': return 'gold';
      case 'index_diff': return 'blue';
      case 'constraint_diff': return 'purple';
      case 'value_diff': return 'orange';
      case 'row_missing_in_target': return 'red';
      case 'row_missing_in_source': return 'volcano';
      default: return 'default';
    }
  };

  const getDiffTypeText = (type: string) => {
    switch (type) {
      case 'column_missing': return '字段缺失';
      case 'column_extra': return '多余字段';
      case 'column_type_diff': return '类型不一致';
      case 'index_diff': return '索引差异';
      case 'constraint_diff': return '约束差异';
      case 'value_diff': return '值不一致';
      case 'row_missing_in_target': return '目标库缺失';
      case 'row_missing_in_source': return '源库缺失';
      default: return type;
    }
  };

  const structureColumns = [
    { title: '表名', dataIndex: 'table_name', width: 150 },
    {
      title: '差异类型',
      dataIndex: 'diff_type',
      width: 120,
      render: (type: string) => <Tag color={getDiffTypeColor(type)}>{getDiffTypeText(type)}</Tag>
    },
    { title: '字段名', dataIndex: 'field_name', width: 150 },
    { title: '源库值', dataIndex: 'source_value' },
    { title: '目标库值', dataIndex: 'target_value' },
    { title: '详情', dataIndex: 'diff_detail', ellipsis: true },
  ];

  const dataColumns = [
    { title: '表名', dataIndex: 'table_name', width: 150 },
    { title: '主键', dataIndex: 'primary_key', width: 200, render: (primary_key: any) => JSON.stringify(primary_key) },
    {
      title: '差异类型',
      dataIndex: 'diff_type',
      width: 120,
      render: (type: string) => <Tag color={getDiffTypeColor(type)}>{getDiffTypeText(type)}</Tag>
    },
    { title: '差异字段', dataIndex: 'diff_columns', render: (diff_columns: string[]) => diff_columns?.join(', ') || '-' },
  ];

  if (loading) {
    return (
      <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%', textAlign: 'center' }}>
        <Spin size="large" tip="加载比对结果中..." />
      </div>
    );
  }

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%' }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/history')}>返回历史记录</Button>
        <Button type="primary" icon={<DownloadOutlined />} onClick={() => setExportModalVisible(true)}>导出报告</Button>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={5}>
          <Card>
            <Statistic title="总表数" value={summary?.summary?.total_tables || 0} />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="结构一致"
              value={summary?.summary?.structure_match_tables || 0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="结构差异"
              value={summary?.summary?.structure_diff_tables || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={5}>
          <Card>
            <Statistic
              title="数据一致"
              value={summary?.summary?.data_match_tables || 0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="数据差异"
              value={summary?.summary?.data_diff_tables || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      <Card bordered={false}>
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab={`结构差异 (${structurePageInfo.total})`} key="1">
            <Table
              columns={structureColumns}
              dataSource={structureDiffs}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: '无结构差异' }}
            />
            {structurePageInfo.total > 0 && (
              <div style={{ marginTop: 16, textAlign: 'right' }}>
                <Pagination
                  current={structurePageInfo.page}
                  pageSize={structurePageInfo.page_size}
                  total={structurePageInfo.total}
                  showSizeChanger
                  onChange={(page, page_size) => fetchStructureDiffs(page, page_size)}
                />
              </div>
            )}
          </Tabs.TabPane>
          <Tabs.TabPane tab={`数据差异 (${dataPageInfo.total})`} key="2">
            <Table
              columns={dataColumns}
              dataSource={dataDiffs}
              rowKey="id"
              pagination={false}
              locale={{ emptyText: '无数据差异' }}
            />
            {dataPageInfo.total > 0 && (
              <div style={{ marginTop: 16, textAlign: 'right' }}>
                <Pagination
                  current={dataPageInfo.page}
                  pageSize={dataPageInfo.page_size}
                  total={dataPageInfo.total}
                  showSizeChanger
                  onChange={(page, page_size) => fetchDataDiffs(page, page_size)}
                />
              </div>
            )}
          </Tabs.TabPane>
        </Tabs>
      </Card>

      <Modal
        title="导出比对报告"
        open={exportModalVisible}
        onOk={handleExport}
        onCancel={() => setExportModalVisible(false)}
        confirmLoading={exportLoading}
      >
        <div style={{ marginBottom: 16 }}>
          <span style={{ marginRight: 8 }}>导出格式：</span>
          <Select value={exportFormat} onChange={setExportFormat} style={{ width: 200 }}>
            <Option value="excel">Excel (.xlsx)</Option>
            <Option value="html">HTML 报告</Option>
            <Option value="txt">文本文件 (.txt)</Option>
          </Select>
        </div>
      </Modal>
    </div>
  );
};

export default Result;
