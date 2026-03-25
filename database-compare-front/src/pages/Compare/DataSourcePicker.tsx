import React, { useEffect } from 'react';
import { Select, Row, Col, Card } from 'antd';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import { useCompareStore } from '@/stores/compareStore';

const DataSourcePicker: React.FC = () => {
  const { dataSources, fetchDataSources } = useDataSourceStore();
  const { current_task, setSourceDb, setTargetDb } = useCompareStore();

  useEffect(() => {
    fetchDataSources();
  }, [fetchDataSources]);

  const options = dataSources.map(ds => ({ label: ds.name, value: ds.id }));

  return (
    <Row gutter={24} style={{ marginTop: 24 }}>
      <Col span={12}>
        <Card title="源数据库 (基准)">
          <Select
            style={{ width: '100%' }}
            placeholder="请选择源数据库"
            options={options}
            value={current_task?.source_id || undefined}
            onChange={setSourceDb}
          />
        </Card>
      </Col>
      <Col span={12}>
        <Card title="目标数据库 (校验)">
          <Select
            style={{ width: '100%' }}
            placeholder="请选择目标数据库"
            options={options}
            value={current_task?.target_id || undefined}
            onChange={setTargetDb}
          />
        </Card>
      </Col>
    </Row>
  );
};

export default DataSourcePicker;
