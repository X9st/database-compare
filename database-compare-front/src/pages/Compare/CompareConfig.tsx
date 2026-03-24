import React from 'react';
import { Form, Switch, InputNumber, Radio, Divider } from 'antd';
import { useCompareStore } from '@/stores/compareStore';

const CompareConfig: React.FC = () => {
  const { currentTask, setCompareOptions } = useCompareStore();
  const options = currentTask?.options;

  if (!options) return null;

  const updateStructure = (key: string, val: boolean) => {
    setCompareOptions({ ...options, structureOptions: { ...options.structureOptions, [key]: val } });
  };

  const updateData = (key: string, val: any) => {
    setCompareOptions({ ...options, dataOptions: { ...options.dataOptions, [key]: val } });
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
          <Switch checked={options.structureOptions.compareIndex} onChange={v => updateStructure('compareIndex', v)} />
        </Form.Item>
        <Form.Item label="比对约束">
          <Switch checked={options.structureOptions.compareConstraint} onChange={v => updateStructure('compareConstraint', v)} />
        </Form.Item>
        <Form.Item label="比对注释">
          <Switch checked={options.structureOptions.compareComment} onChange={v => updateStructure('compareComment', v)} />
        </Form.Item>

        <Divider orientation="left">数据比对选项</Divider>
        <Form.Item label="浮点数精度 (小数位)">
          <InputNumber min={0} max={10} value={options.dataOptions.floatPrecision} onChange={v => updateData('floatPrecision', v)} />
        </Form.Item>
        <Form.Item label="忽略大小写">
          <Switch checked={options.dataOptions.ignoreCase} onChange={v => updateData('ignoreCase', v)} />
        </Form.Item>
        <Form.Item label="去除前后空格">
          <Switch checked={options.dataOptions.trimWhitespace} onChange={v => updateData('trimWhitespace', v)} />
        </Form.Item>
        <Form.Item label="跳过大字段 (LOB/TEXT)">
          <Switch checked={options.dataOptions.skipLargeFields} onChange={v => updateData('skipLargeFields', v)} />
        </Form.Item>
      </Form>
    </div>
  );
};

export default CompareConfig;
