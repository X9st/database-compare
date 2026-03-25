import React from 'react';
import { Form, Switch, InputNumber, Radio, Divider } from 'antd';
import { useCompareStore } from '@/stores/compareStore';

const CompareConfig: React.FC = () => {
  const { current_task, setCompareOptions } = useCompareStore();
  const options = current_task?.options;

  if (!options) return null;

  const updateStructure = (key: string, val: boolean) => {
    setCompareOptions({ ...options, structure_options: { ...options.structure_options, [key]: val } });
  };

  const updateData = (key: string, val: any) => {
    setCompareOptions({ ...options, data_options: { ...options.data_options, [key]: val } });
  };

  return (
    <div style={{ marginTop: 24 }}>
      <Form layout="horizontal" labelCol={{ span: 6 }} wrapperCol={{ span: 18 }} style={{ maxWidth: 600 }}>
        <Divider orientation="left">比对模式</Divider>
        <Form.Item label="模式">
          <Radio.Group 
            value={options.mode} 
            onChange={e => setCompareOptions({ ...options, mode: e.target.value })}
          >
            <Radio value="full">全量比对</Radio>
            <Radio value="incremental">增量比对</Radio>
          </Radio.Group>
        </Form.Item>

        <Divider orientation="left">结构比对选项</Divider>
        <Form.Item label="比对索引">
          <Switch checked={options.structure_options.compare_index} onChange={v => updateStructure('compare_index', v)} />
        </Form.Item>
        <Form.Item label="比对约束">
          <Switch checked={options.structure_options.compare_constraint} onChange={v => updateStructure('compare_constraint', v)} />
        </Form.Item>
        <Form.Item label="比对注释">
          <Switch checked={options.structure_options.compare_comment} onChange={v => updateStructure('compare_comment', v)} />
        </Form.Item>

        <Divider orientation="left">数据比对选项</Divider>
        <Form.Item label="浮点数精度 (小数位)">
          <InputNumber min={0} max={10} value={options.data_options.float_precision} onChange={v => updateData('float_precision', v)} />
        </Form.Item>
        <Form.Item label="忽略大小写">
          <Switch checked={options.data_options.ignore_case} onChange={v => updateData('ignore_case', v)} />
        </Form.Item>
        <Form.Item label="去除前后空格">
          <Switch checked={options.data_options.trim_whitespace} onChange={v => updateData('trim_whitespace', v)} />
        </Form.Item>
        <Form.Item label="跳过大字段 (LOB/TEXT)">
          <Switch checked={options.data_options.skip_large_fields} onChange={v => updateData('skip_large_fields', v)} />
        </Form.Item>
      </Form>
    </div>
  );
};

export default CompareConfig;
