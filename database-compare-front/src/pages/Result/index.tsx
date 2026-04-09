import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tabs, Card, Row, Col, Statistic, Button, Table, Tag, message, Spin, Pagination, Select, Modal, Input, Alert } from 'antd';
import { ArrowLeftOutlined, DownloadOutlined } from '@ant-design/icons';
import { resultApi, CompareResultSummary, StructureDiff, DataDiff, PageInfo, ResultCompareResponse } from '@/services/resultApi';
import { resolveApiUrl } from '@/services/api';

const { Option } = Select;

type DiffCategory = 'structure' | 'data';

interface DiffTypeMeta {
  text: string;
  color: string;
  category: DiffCategory;
}

const DIFF_TYPE_META: Record<string, DiffTypeMeta> = {
  table_missing_in_target: { text: '目标缺表', color: 'red', category: 'structure' },
  table_extra_in_target: { text: '目标多表', color: 'orange', category: 'structure' },
  column_missing: { text: '字段缺失', color: 'red', category: 'structure' },
  column_extra: { text: '字段多余', color: 'orange', category: 'structure' },
  column_type_diff: { text: '字段类型差异', color: 'gold', category: 'structure' },
  column_length_diff: { text: '字段长度差异', color: 'geekblue', category: 'structure' },
  column_precision_diff: { text: '字段精度/小数位差异', color: 'cyan', category: 'structure' },
  column_nullable_diff: { text: '字段可空性差异', color: 'magenta', category: 'structure' },
  column_default_diff: { text: '字段默认值差异', color: 'purple', category: 'structure' },
  index_diff: { text: '索引差异', color: 'blue', category: 'structure' },
  constraint_diff: { text: '约束差异', color: 'volcano', category: 'structure' },
  comment_diff: { text: '注释差异', color: 'lime', category: 'structure' },
  row_count_diff: { text: '行数不一致', color: 'gold', category: 'data' },
  row_missing_in_target: { text: '目标缺行', color: 'red', category: 'data' },
  row_extra_in_target: { text: '目标多行', color: 'volcano', category: 'data' },
  value_diff: { text: '字段值差异', color: 'orange', category: 'data' },
  null_diff: { text: '空值差异', color: 'purple', category: 'data' },
  primary_key_missing: { text: '缺少主键', color: 'red', category: 'data' },
  table_compare_error: { text: '表比对异常', color: 'red', category: 'data' },
};

const STRUCTURE_DIFF_TYPE_ORDER = [
  'table_missing_in_target',
  'table_extra_in_target',
  'column_missing',
  'column_extra',
  'column_type_diff',
  'column_length_diff',
  'column_precision_diff',
  'column_nullable_diff',
  'column_default_diff',
  'index_diff',
  'constraint_diff',
  'comment_diff',
] as const;

const DATA_DIFF_TYPE_ORDER = [
  'row_count_diff',
  'row_missing_in_target',
  'row_extra_in_target',
  'value_diff',
  'null_diff',
  'primary_key_missing',
  'table_compare_error',
] as const;

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

  const getDiffTypeColor = (type: string) => DIFF_TYPE_META[type]?.color || 'default';
  const getDiffTypeText = (type: string) => DIFF_TYPE_META[type]?.text || ('未知差异（' + type + '）');

  const normalizeDisplayValue = (value: unknown) => {
    if (value === null || value === undefined) {
      return '-';
    }
    const text = String(value).trim();
    return text ? text : '-';
  };

  const parseMappedTableName = (tableName?: string) => {
    const raw = normalizeDisplayValue(tableName);
    if (raw === '-') {
      return { source: '-', target: '-' };
    }
    const parts = String(raw).split('->').map((item) => item.trim()).filter(Boolean);
    if (parts.length === 2) {
      return { source: parts[0], target: parts[1] };
    }
    return { source: raw, target: raw };
  };

  const renderMultilineText = (text: string) => (
    <div
      style={{
        whiteSpace: 'normal',
        wordBreak: 'break-word',
        lineHeight: 1.6,
      }}
    >
      {text}
    </div>
  );

  const formatStructureSideValue = (record: StructureDiff, side: 'source' | 'target') => {
    const value = normalizeDisplayValue(side === 'source' ? record.source_value : record.target_value);
    const isSource = side === 'source';

    switch (record.diff_type) {
      case 'column_missing':
        return isSource
          ? `源字段类型：${value}`
          : `目标当前状态：字段不存在（期望字段名：${value}）`;
      case 'column_extra':
        return isSource
          ? '源当前状态：字段不存在'
          : `目标字段类型：${value}`;
      case 'column_type_diff':
        return isSource ? `源字段类型：${value}` : `目标字段类型：${value}`;
      case 'column_length_diff':
        return isSource ? `源字段长度：${value}` : `目标字段长度：${value}`;
      case 'column_precision_diff':
        return isSource ? `源精度/小数位：${value}` : `目标精度/小数位：${value}`;
      case 'column_nullable_diff':
        return isSource ? `源可空性：${value}` : `目标可空性：${value}`;
      case 'column_default_diff':
        return isSource ? `源默认值：${value}` : `目标默认值：${value}`;
      case 'comment_diff':
        return isSource ? `源注释：${value}` : `目标注释：${value}`;
      default:
        return isSource ? `源侧：${value}` : `目标侧：${value}`;
    }
  };

  const formatStructureDetail = (record: StructureDiff) => {
    const tableName = parseMappedTableName(record.table_name);
    const fieldName = normalizeDisplayValue(record.field_name);
    const targetField = normalizeDisplayValue(record.target_value) === '-' ? fieldName : normalizeDisplayValue(record.target_value);
    const targetCurrent = normalizeDisplayValue(record.target_value);

    switch (record.diff_type) {
      case 'table_missing_in_target':
        return `目标库缺少表：${tableName.target}。目标库当前状态：未找到该表。`;
      case 'table_extra_in_target':
        return `目标库多出表：${tableName.target}。目标库当前状态：该表存在，但源库不存在。`;
      case 'column_missing':
        return `目标表 ${tableName.target} 缺少字段：${fieldName}。期望目标字段名：${targetField}；目标库当前状态：未找到该字段。`;
      case 'column_extra':
        return `目标表 ${tableName.target} 存在源侧没有的字段：${fieldName}。目标库当前信息：字段类型为 ${targetCurrent}；源库当前状态：无该字段。`;
      default:
        return normalizeDisplayValue(record.diff_detail);
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
    { title: '字段名', dataIndex: 'field_name', width: 150, render: (field_name: string) => normalizeDisplayValue(field_name) },
    {
      title: '源侧信息',
      dataIndex: 'source_value',
      render: (_: string, record: StructureDiff) => renderMultilineText(formatStructureSideValue(record, 'source')),
    },
    {
      title: '目标侧信息',
      dataIndex: 'target_value',
      render: (_: string, record: StructureDiff) => renderMultilineText(formatStructureSideValue(record, 'target')),
    },
    {
      title: '差异说明',
      dataIndex: 'diff_detail',
      width: 420,
      render: (_: string, record: StructureDiff) => renderMultilineText(formatStructureDetail(record)),
    },
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
                {STRUCTURE_DIFF_TYPE_ORDER.map((type) => (
                  <Option key={type} value={type}>
                    {getDiffTypeText(type)}
                  </Option>
                ))}
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
                {DATA_DIFF_TYPE_ORDER.map((type) => (
                  <Option key={type} value={type}>
                    {getDiffTypeText(type)}
                  </Option>
                ))}
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
