import React from 'react';
import { Tabs, Form, InputNumber, Switch, Button, Card, message } from 'antd';
import IgnoreRules from './IgnoreRules';

const Settings: React.FC = () => {
  const handleSave = () => {
    message.success('设置保存成功');
  };

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%' }}>
      <Card title="系统设置" bordered={false}>
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab="常规设置" key="1">
            <Form layout="vertical" style={{ maxWidth: 600 }}>
              <Form.Item label="默认比对线程数">
                <InputNumber min={1} max={16} defaultValue={4} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item label="数据库查询超时时间 (秒)">
                <InputNumber min={10} max={600} defaultValue={60} style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item label="开启断点续比">
                <Switch defaultChecked />
              </Form.Item>
              <Form.Item>
                <Button type="primary" onClick={handleSave}>保存设置</Button>
              </Form.Item>
            </Form>
          </Tabs.TabPane>
          <Tabs.TabPane tab="全局忽略规则" key="2">
            <IgnoreRules />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Settings;
