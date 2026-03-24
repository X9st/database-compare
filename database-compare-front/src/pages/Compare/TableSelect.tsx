import React from 'react';
import { Radio, Select, Form } from 'antd';
import { useCompareStore } from '@/stores/compareStore';

const TableSelect: React.FC = () => {
  const { currentTask, setTables } = useCompareStore();
  const mode = currentTask?.tableSelection.mode || 'all';
  const tables = currentTask?.tableSelection.tables || [];

  // Mock tables
  const mockTables = [
    { label: 'users', value: 'users' }, 
    { label: 'orders', value: 'orders' },
    { label: 'products', value: 'products' }
  ];

  return (
    <div style={{ marginTop: 24 }}>
      <Form layout="vertical">
        <Form.Item label="比对范围">
          <Radio.Group 
            value={mode} 
            onChange={e => setTables({ mode: e.target.value, tables: [] })}
          >
            <Radio.Button value="all">全库比对</Radio.Button>
            <Radio.Button value="include">指定表比对</Radio.Button>
            <Radio.Button value="exclude">排除表比对</Radio.Button>
          </Radio.Group>
        </Form.Item>

        {mode !== 'all' && (
          <Form.Item label={mode === 'include' ? '选择要比对的表' : '选择要排除的表'}>
            <Select
              mode="multiple"
              style={{ width: '100%' }}
              placeholder="请选择表"
              options={mockTables}
              value={tables}
              onChange={val => setTables({ mode, tables: val })}
            />
          </Form.Item>
        )}
      </Form>
    </div>
  );
};

export default TableSelect;
