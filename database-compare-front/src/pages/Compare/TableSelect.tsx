import React, { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Form, Radio, Select, Space } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { useCompareStore } from '@/stores/compareStore';
import { dataSourceApi } from '@/services/dataSourceApi';
import { TableInfo, TableMapping } from '@/types';

const TableSelect: React.FC = () => {
  const { current_task, setTables, setCompareOptions } = useCompareStore();
  const mode = current_task?.table_selection.mode || 'all';
  const tables = current_task?.table_selection.tables || [];
  const options = current_task?.options;
  const mappings = options?.table_mappings || [];

  const sourceId = current_task?.source_id;
  const targetId = current_task?.target_id;

  const [sourceTables, setSourceTables] = useState<TableInfo[]>([]);
  const [targetTables, setTargetTables] = useState<TableInfo[]>([]);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [targetLoading, setTargetLoading] = useState(false);
  const [sourceLoaded, setSourceLoaded] = useState(false);
  const [targetLoaded, setTargetLoaded] = useState(false);

  const sourceOptions = useMemo(
    () => sourceTables.map((t) => ({ label: t.name, value: t.name })),
    [sourceTables]
  );
  const targetOptions = useMemo(
    () => targetTables.map((t) => ({ label: t.name, value: t.name })),
    [targetTables]
  );

  const updateMappings = (nextMappings: TableMapping[]) => {
    if (!options) {
      return;
    }
    setCompareOptions({
      ...options,
      table_mappings: nextMappings
    });
  };

  const fetchSourceTables = async (keyword = '') => {
    if (!sourceId) {
      setSourceTables([]);
      setSourceLoaded(false);
      return;
    }

    setSourceLoading(true);
    try {
      const resp = await dataSourceApi.getTables(sourceId, undefined, keyword || undefined);
      setSourceTables(resp.data?.data || []);
      setSourceLoaded(true);
    } finally {
      setSourceLoading(false);
    }
  };

  const fetchTargetTables = async (keyword = '') => {
    if (!targetId) {
      setTargetTables([]);
      setTargetLoaded(false);
      return;
    }

    setTargetLoading(true);
    try {
      const resp = await dataSourceApi.getTables(targetId, undefined, keyword || undefined);
      setTargetTables(resp.data?.data || []);
      setTargetLoaded(true);
    } finally {
      setTargetLoading(false);
    }
  };

  useEffect(() => {
    fetchSourceTables();
  }, [sourceId]);

  useEffect(() => {
    fetchTargetTables();
  }, [targetId]);

  useEffect(() => {
    if (!options) {
      return;
    }

    if ((mode === 'include' || mode === 'exclude') && sourceLoaded) {
      const sourceSet = new Set(sourceTables.map((t) => t.name));
      const filteredTables = tables.filter((table) => sourceSet.has(table));
      if (filteredTables.length !== tables.length) {
        setTables({ mode, tables: filteredTables });
      }
    }

    if (mode === 'mapping' && sourceLoaded && targetLoaded) {
      const sourceSet = new Set(sourceTables.map((t) => t.name));
      const targetSet = new Set(targetTables.map((t) => t.name));
      const filteredMappings = mappings.filter(
        (m) => sourceSet.has(m.source_table) && targetSet.has(m.target_table)
      );

      if (filteredMappings.length !== mappings.length) {
        updateMappings(filteredMappings);
      }
    }
  }, [mode, sourceLoaded, targetLoaded, sourceTables, targetTables]);

  const handleModeChange = (nextMode: 'all' | 'include' | 'exclude' | 'mapping') => {
    setTables({ mode: nextMode, tables: [] });
    if (nextMode === 'mapping' && mappings.length === 0) {
      updateMappings([{ source_table: '', target_table: '', column_mappings: [] }]);
    }
  };

  const addMapping = () => {
    updateMappings([...mappings, { source_table: '', target_table: '', column_mappings: [] }]);
  };

  const removeMapping = (index: number) => {
    const next = mappings.filter((_, idx) => idx !== index);
    updateMappings(next);
  };

  const updateMapping = (index: number, patch: Partial<TableMapping>) => {
    const next = mappings.map((item, idx) => (idx === index ? { ...item, ...patch } : item));
    updateMappings(next);
  };

  const localFilter = (input: string, option?: { label: string; value: string }) =>
    String(option?.label || '').toLowerCase().includes(input.toLowerCase());

  return (
    <div style={{ marginTop: 24 }}>
      <Form layout="vertical">
        <Form.Item label="比对范围">
          <Radio.Group value={mode} onChange={(e) => handleModeChange(e.target.value)}>
            <Radio.Button value="all">全库比对</Radio.Button>
            <Radio.Button value="include">指定表比对</Radio.Button>
            <Radio.Button value="exclude">排除表比对</Radio.Button>
            <Radio.Button value="mapping">映射比对</Radio.Button>
          </Radio.Group>
        </Form.Item>

        {(mode === 'include' || mode === 'exclude') && (
          <Form.Item label={mode === 'include' ? '选择要比对的表' : '选择要排除的表'}>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="请输入表名检索"
              options={sourceOptions}
              value={tables}
              loading={sourceLoading}
              showSearch
              filterOption={localFilter}
              onSearch={(value) => fetchSourceTables(value)}
              onChange={(value) => setTables({ mode, tables: value })}
            />
          </Form.Item>
        )}

        {mode === 'mapping' && (
          <>
            {(!sourceId || !targetId) && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 12 }}
                message="请先在上一步选择源数据库和目标数据库"
              />
            )}

            {mappings.map((mapping, index) => (
              <Space key={`${index}-${mapping.source_table}-${mapping.target_table}`} style={{ display: 'flex', marginBottom: 8 }}>
                <Select
                  style={{ width: 360 }}
                  placeholder="选择源表"
                  options={sourceOptions}
                  value={mapping.source_table || undefined}
                  loading={sourceLoading}
                  showSearch
                  filterOption={localFilter}
                  onSearch={(value) => fetchSourceTables(value)}
                  onChange={(value) => updateMapping(index, { source_table: value })}
                />
                <span>→</span>
                <Select
                  style={{ width: 360 }}
                  placeholder="选择目标表"
                  options={targetOptions}
                  value={mapping.target_table || undefined}
                  loading={targetLoading}
                  showSearch
                  filterOption={localFilter}
                  onSearch={(value) => fetchTargetTables(value)}
                  onChange={(value) => updateMapping(index, { target_table: value })}
                />
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeMapping(index)}
                  disabled={mappings.length <= 1}
                />
              </Space>
            ))}

            <Button type="dashed" icon={<PlusOutlined />} onClick={addMapping}>
              新增表映射
            </Button>
          </>
        )}
      </Form>
    </div>
  );
};

export default TableSelect;
