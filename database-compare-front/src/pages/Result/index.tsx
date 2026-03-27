import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Card, Row, Col, Statistic, Button, Table, Tag, message, Spin, Pagination, Select, Modal, Input, Alert } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined } from '@ant-design/icons';
import { resultApi, CompareResultSummary, StructureDiff, DataDiff, PageInfo, ResultCompareResponse } from '@/services/resultApi';
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
  const [structureFilterTable, setStructureFilterTable] = useState('');
  const [structureFilterType, setStructureFilterType] = useState<string | undefined>(undefined);
  const [dataFilterTable, setDataFilterTable] = useState('');
  const [dataFilterType, setDataFilterType] = useState<string | undefined>(undefined);
  const [baselineResultId, setBaselineResultId] = useState('');
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareResult, setCompareResult] = useState<ResultCompareResponse | null>(null);
  const [compareExportLoading, setCompareExportLoading] = useState(false);
  const [compareExportFormat, setCompareExportFormat] = useState<'txt' | 'html' | 'excel'>('txt');

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

  const fetchStructureDiffs = async (
    page: number,
    page_size = 20,
    table_name: string = structureFilterTable,
    diff_type: string | undefined = structureFilterType
  ) => {
    if (!result_id) {
      return;
    }
    try {
      const response = await resultApi.getStructureDiffs(result_id, {
        page,
        page_size,
        table_name: table_name || undefined,
        diff_type: diff_type || undefined,
      });
      setStructureDiffs(response.data?.data || []);
      if (response.data?.page_info) {
        setStructurePageInfo(response.data.page_info);
      }
    } catch (e) {
      console.error('Failed to fetch structure diffs:', e);
    }
  };

  const fetchDataDiffs = async (
    page: number,
    page_size = 20,
    table_name: string = dataFilterTable,
    diff_type: string | undefined = dataFilterType
  ) => {
    if (!result_id) {
      return;
    }
    try {
      const response = await resultApi.getDataDiffs(result_id, {
        page,
        page_size,
        table_name: table_name || undefined,
        diff_type: diff_type || undefined,
      });
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
          tables: Array.from(new Set([structureFilterTable, dataFilterTable].filter(Boolean))),
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

  const handleCompare = async () => {
    if (!result_id || !baselineResultId) {
      message.warning('请输入基线结果ID');
      return;
    }
    setCompareLoading(true);
    try {
      const resp = await resultApi.compareResults(baselineResultId, result_id);
      setCompareResult(resp.data?.data || null);
      message.success('结果对比完成');
    } catch {
      message.error('结果对比失败');
    } finally {
      setCompareLoading(false);
    }
  };

  const handleExportCompare = async () => {
    if (!result_id || !baselineResultId) {
      message.warning('请先输入基线结果ID并执行对比');
      return;
    }
    setCompareExportLoading(true);
    try {
      const resp = await resultApi.exportComparedResults({
        baseline_result_id: baselineResultId,
        current_result_id: result_id,
        format: compareExportFormat,
      });
      const payload = resp.data?.data;
      if (payload?.download_url) {
        window.open(resolveApiUrl(payload.download_url), '_blank');
      }
      message.success('对比结论导出成功');
    } catch {
      message.error('导出对比结论失败');
    } finally {
      setCompareExportLoading(false);
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
      case 'row_extra_in_target': return 'volcano';
      case 'row_count_diff': return 'gold';
      case 'null_diff': return 'purple';
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
      case 'row_extra_in_target': return '目标库多余';
      case 'row_count_diff': return '行数不一致';
      case 'null_diff': return '空值差异';
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
        <Col span={4}>
          <Card>
            <Statistic title="总表数" value={summary?.summary?.total_tables || 0} />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="结构一致"
              value={summary?.summary?.structure_match_tables || 0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="结构差异"
              value={summary?.summary?.structure_diff_tables || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={4}>
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
        <Col span={4}>
          <Card>
            <Statistic
              title="完全一致"
              value={summary?.summary?.no_diff_tables || 0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Card bordered={false} style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <Input
            placeholder="输入基线结果ID"
            value={baselineResultId}
            onChange={(e) => setBaselineResultId(e.target.value)}
          />
          <Button loading={compareLoading} onClick={handleCompare}>对比当前结果</Button>
          <Select value={compareExportFormat} onChange={setCompareExportFormat} style={{ width: 120 }}>
            <Option value="txt">TXT</Option>
            <Option value="html">HTML</Option>
            <Option value="excel">Excel</Option>
          </Select>
          <Button loading={compareExportLoading} onClick={handleExportCompare}>导出对比结论</Button>
        </div>
        {compareResult && (
          <Alert
            style={{ marginTop: 12 }}
            type="info"
            message={`新增差异 ${compareResult.summary.added}，已消除差异 ${compareResult.summary.resolved}，不变差异 ${compareResult.summary.unchanged}`}
          />
        )}
      </Card>

      <Card bordered={false}>
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab={`结构差异 (${structurePageInfo.total})`} key="1">
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <Input
                placeholder="按表名筛选"
                value={structureFilterTable}
                onChange={(e) => setStructureFilterTable(e.target.value)}
                allowClear
              />
              <Select
                style={{ width: 220 }}
                allowClear
                placeholder="差异类型"
                value={structureFilterType}
                onChange={setStructureFilterType}
              >
                <Option value="table_missing_in_target">目标缺表</Option>
                <Option value="table_extra_in_target">目标多表</Option>
                <Option value="column_missing">字段缺失</Option>
                <Option value="column_extra">字段多余</Option>
                <Option value="column_type_diff">字段类型差异</Option>
                <Option value="column_length_diff">字段长度差异</Option>
                <Option value="column_precision_diff">字段精度差异</Option>
                <Option value="comment_diff">注释差异</Option>
              </Select>
              <Button onClick={() => fetchStructureDiffs(1, structurePageInfo.page_size)}>筛选</Button>
            </div>
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
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <Input
                placeholder="按表名筛选"
                value={dataFilterTable}
                onChange={(e) => setDataFilterTable(e.target.value)}
                allowClear
              />
              <Select
                style={{ width: 220 }}
                allowClear
                placeholder="差异类型"
                value={dataFilterType}
                onChange={setDataFilterType}
              >
                <Option value="row_count_diff">行数不一致</Option>
                <Option value="row_missing_in_target">目标缺行</Option>
                <Option value="row_extra_in_target">目标多行</Option>
                <Option value="value_diff">值差异</Option>
                <Option value="null_diff">空值差异</Option>
              </Select>
              <Button onClick={() => fetchDataDiffs(1, dataPageInfo.page_size)}>筛选</Button>
            </div>
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
