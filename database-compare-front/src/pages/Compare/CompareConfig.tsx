import React, { useEffect, useMemo, useState } from 'react';
import { Form, Switch, InputNumber, Radio, Divider, Input, Space, Button, Select, Alert } from 'antd';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { useCompareStore } from '@/stores/compareStore';
import { dataSourceApi } from '@/services/dataSourceApi';
import { TableInfo } from '@/types';

const CompareConfig: React.FC = () => {
  const { current_task, setCompareOptions } = useCompareStore();
  const options = current_task?.options;

  const sourceId = current_task?.source_id;
  const targetId = current_task?.target_id;
  const tableSelectionMode = current_task?.table_selection.mode;
  const selectedTables = current_task?.table_selection.tables || [];
  const tableMappings = options?.table_mappings || [];

  const [sourceTables, setSourceTables] = useState<TableInfo[]>([]);
  const [targetTables, setTargetTables] = useState<TableInfo[]>([]);

  useEffect(() => {
    const fetchTables = async () => {
      if (!sourceId) {
        setSourceTables([]);
        return;
      }
      try {
        const resp = await dataSourceApi.getTables(sourceId);
        setSourceTables(resp.data?.data || []);
      } catch {
        setSourceTables([]);
      }
    };
    fetchTables();
  }, [sourceId]);

  useEffect(() => {
    const fetchTables = async () => {
      if (!targetId) {
        setTargetTables([]);
        return;
      }
      try {
        const resp = await dataSourceApi.getTables(targetId);
        setTargetTables(resp.data?.data || []);
      } catch {
        setTargetTables([]);
      }
    };
    fetchTables();
  }, [targetId]);

  const sourceTableOptions = useMemo(
    () => sourceTables.map((t) => ({ label: t.name, value: t.name })),
    [sourceTables]
  );
  const targetTableOptions = useMemo(
    () => targetTables.map((t) => ({ label: t.name, value: t.name })),
    [targetTables]
  );

  const sourceTableCandidates = useMemo(() => {
    if (tableSelectionMode === 'mapping') {
      return Array.from(new Set(tableMappings.map((m) => m.source_table).filter(Boolean)));
    }
    if (tableSelectionMode === 'include') {
      return selectedTables;
    }
    return sourceTables.map((t) => t.name);
  }, [tableSelectionMode, tableMappings, selectedTables, sourceTables]);

  if (!options) return null;

  const updateStructure = (key: string, val: boolean) => {
    setCompareOptions({ ...options, structure_options: { ...options.structure_options, [key]: val } });
  };

  const updateData = (key: string, val: any) => {
    setCompareOptions({ ...options, data_options: { ...options.data_options, [key]: val } });
  };

  const updateIncremental = (patch: Record<string, string>) => {
    setCompareOptions({
      ...options,
      incremental_config: {
        ...(options.incremental_config || {}),
        ...patch,
      },
    });
  };

  const updatePkConfigs = (nextConfigs: any[]) => {
    setCompareOptions({
      ...options,
      table_primary_keys: nextConfigs,
    });
  };

  const addPkConfig = () => {
    const current = options.table_primary_keys || [];
    const defaultSource = sourceTableCandidates[0] || '';
    updatePkConfigs([
      ...current,
      {
        source_table: defaultSource,
        primary_keys: [],
        target_table: tableSelectionMode === 'mapping' ? '' : defaultSource,
        target_primary_keys: [],
      },
    ]);
  };

  const removePkConfig = (idx: number) => {
    const current = options.table_primary_keys || [];
    updatePkConfigs(current.filter((_, i) => i !== idx));
  };

  const updatePkConfig = (idx: number, patch: Record<string, any>) => {
    const current = options.table_primary_keys || [];
    const next = current.map((item, i) => (i === idx ? { ...item, ...patch } : item));
    updatePkConfigs(next);
  };

  const pkConfigs = options.table_primary_keys || [];

  return (
    <div style={{ marginTop: 24 }}>
      <Form layout="horizontal" labelCol={{ span: 6 }} wrapperCol={{ span: 18 }} style={{ maxWidth: 860 }}>
        <Divider orientation="left">比对模式</Divider>
        <Form.Item label="模式">
          <Radio.Group
            value={options.mode}
            onChange={(e) =>
              setCompareOptions({
                ...options,
                mode: e.target.value,
                incremental_config:
                  e.target.value === 'incremental' ? (options.incremental_config || {}) : undefined,
              })
            }
          >
            <Radio value="full">全量比对</Radio>
            <Radio value="incremental">增量比对</Radio>
          </Radio.Group>
        </Form.Item>
        <Form.Item label="断点续比">
          <Switch
            checked={options.resume_from_checkpoint ?? true}
            onChange={(v) => setCompareOptions({ ...options, resume_from_checkpoint: v })}
          />
        </Form.Item>
        <Form.Item label=" ">
          <Alert
            type="info"
            showIcon
            message="启用后：若 7 天内存在同配置失败/取消任务，将自动跳过已完成表并续跑。"
          />
        </Form.Item>

        {options.mode === 'incremental' && (
          <>
            <Alert
              type="info"
              showIcon
              style={{ marginBottom: 12 }}
              message="增量模式下，至少配置一组条件（时间条件或批次条件）"
            />
            <Form.Item label="源时间字段">
              <Input
                value={options.incremental_config?.time_column}
                placeholder="例如：updated_at"
                onChange={(e) => updateIncremental({ time_column: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="目标时间字段">
              <Input
                value={options.incremental_config?.target_time_column}
                placeholder="可选，默认同名"
                onChange={(e) => updateIncremental({ target_time_column: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="开始时间">
              <Input
                value={options.incremental_config?.start_time}
                placeholder="例如：2026-03-01 00:00:00"
                onChange={(e) => updateIncremental({ start_time: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="结束时间">
              <Input
                value={options.incremental_config?.end_time}
                placeholder="例如：2026-03-31 23:59:59"
                onChange={(e) => updateIncremental({ end_time: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="源批次字段">
              <Input
                value={options.incremental_config?.batch_column}
                placeholder="例如：batch_no"
                onChange={(e) => updateIncremental({ batch_column: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="目标批次字段">
              <Input
                value={options.incremental_config?.target_batch_column}
                placeholder="可选，默认同名"
                onChange={(e) => updateIncremental({ target_batch_column: e.target.value })}
              />
            </Form.Item>
            <Form.Item label="批次值">
              <Input
                value={options.incremental_config?.batch_value}
                placeholder="例如：B20260327"
                onChange={(e) => updateIncremental({ batch_value: e.target.value })}
              />
            </Form.Item>
          </>
        )}

        <Divider orientation="left">业务主键配置</Divider>
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 12 }}
          message="当目标库（如 Inceptor）没有物理主键时，配置业务主键用于数据行定位。"
        />
        {pkConfigs.map((item, idx) => (
          <Space key={`${idx}-${item.source_table}`} direction="vertical" style={{ width: '100%', marginBottom: 12 }}>
            <Space wrap>
              <Select
                style={{ width: 220 }}
                placeholder="源表"
                options={sourceTableOptions}
                value={item.source_table || undefined}
                showSearch
                optionFilterProp="label"
                onChange={(value) => {
                  const patch: Record<string, any> = { source_table: value };
                  if (tableSelectionMode !== 'mapping') {
                    patch.target_table = value;
                  }
                  updatePkConfig(idx, patch);
                }}
              />
              <Select
                style={{ width: 220 }}
                placeholder="目标表（可选）"
                options={targetTableOptions}
                value={item.target_table || undefined}
                showSearch
                optionFilterProp="label"
                allowClear
                onChange={(value) => updatePkConfig(idx, { target_table: value })}
              />
              <Button danger icon={<DeleteOutlined />} onClick={() => removePkConfig(idx)} />
            </Space>
            <Select
              mode="tags"
              style={{ width: 460 }}
              placeholder="源业务主键字段（可多选）"
              value={item.primary_keys || []}
              onChange={(value) => updatePkConfig(idx, { primary_keys: value })}
            />
            <Select
              mode="tags"
              style={{ width: 460 }}
              placeholder="目标业务主键字段（可选，字段名不同再填）"
              value={item.target_primary_keys || []}
              onChange={(value) => updatePkConfig(idx, { target_primary_keys: value })}
            />
          </Space>
        ))}
        <Form.Item label=" ">
          <Button type="dashed" icon={<PlusOutlined />} onClick={addPkConfig}>
            新增业务主键规则
          </Button>
        </Form.Item>

        <Divider orientation="left">结构比对选项</Divider>
        <Form.Item label="比对索引">
          <Switch checked={options.structure_options.compare_index} onChange={(v) => updateStructure('compare_index', v)} />
        </Form.Item>
        <Form.Item label="比对约束">
          <Switch checked={options.structure_options.compare_constraint} onChange={(v) => updateStructure('compare_constraint', v)} />
        </Form.Item>
        <Form.Item label="比对注释">
          <Switch checked={options.structure_options.compare_comment} onChange={(v) => updateStructure('compare_comment', v)} />
        </Form.Item>

        <Divider orientation="left">数据比对选项</Divider>
        <Form.Item label="浮点数精度 (小数位)">
          <InputNumber min={0} max={10} value={options.data_options.float_precision} onChange={(v) => updateData('float_precision', v)} />
        </Form.Item>
        <Form.Item label="忽略大小写">
          <Switch checked={options.data_options.ignore_case} onChange={(v) => updateData('ignore_case', v)} />
        </Form.Item>
        <Form.Item label="去除前后空格">
          <Switch checked={options.data_options.trim_whitespace} onChange={(v) => updateData('trim_whitespace', v)} />
        </Form.Item>
        <Form.Item label="跳过大字段 (LOB/TEXT)">
          <Switch checked={options.data_options.skip_large_fields} onChange={(v) => updateData('skip_large_fields', v)} />
        </Form.Item>
      </Form>
    </div>
  );
};

export default CompareConfig;
