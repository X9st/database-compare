import React, { useEffect, useState } from 'react';
import { Tabs, Form, InputNumber, Switch, Button, Card, message, Spin } from 'antd';
import IgnoreRules from './IgnoreRules';
import { settingsApi, SystemSettings } from '@/services/settingsApi';

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsApi.getSystemSettings();
      const data = response.data?.data;
      if (data) {
        form.setFieldsValue({
          defaultThreadCount: data.defaultThreadCount || 4,
          queryTimeout: data.queryTimeout || 60,
          enableCheckpoint: data.enableCheckpoint ?? true,
          maxDiffDisplay: data.maxDiffDisplay || 1000,
          historyRetentionDays: data.historyRetentionDays || 90,
        });
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
      // 使用默认值
      form.setFieldsValue({
        defaultThreadCount: 4,
        queryTimeout: 60,
        enableCheckpoint: true,
        maxDiffDisplay: 1000,
        historyRetentionDays: 90,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await settingsApi.updateSystemSettings({
        default_thread_count: values.defaultThreadCount,
        query_timeout: values.queryTimeout,
        enable_checkpoint: values.enableCheckpoint,
        max_diff_display: values.maxDiffDisplay,
        history_retention_days: values.historyRetentionDays,
      });
      message.success('设置保存成功');
    } catch (e) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ background: '#fff', padding: 24, borderRadius: 8, minHeight: '100%' }}>
      <Card title="系统设置" bordered={false}>
        <Tabs defaultActiveKey="1">
          <Tabs.TabPane tab="常规设置" key="1">
            <Spin spinning={loading}>
              <Form form={form} layout="vertical" style={{ maxWidth: 600 }}>
                <Form.Item 
                  name="defaultThreadCount" 
                  label="默认比对线程数"
                  tooltip="并发比对的线程数量，值越大比对速度越快，但消耗资源更多"
                >
                  <InputNumber min={1} max={16} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="queryTimeout" 
                  label="数据库查询超时时间 (秒)"
                  tooltip="单次数据库查询的最长等待时间"
                >
                  <InputNumber min={10} max={600} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="enableCheckpoint" 
                  label="开启断点续比" 
                  valuePropName="checked"
                  tooltip="比对中断后可从断点继续，避免重新开始"
                >
                  <Switch />
                </Form.Item>
                <Form.Item 
                  name="maxDiffDisplay" 
                  label="最大差异显示数量"
                  tooltip="单次比对结果最多显示的差异条数"
                >
                  <InputNumber min={100} max={10000} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="historyRetentionDays" 
                  label="历史记录保留天数"
                  tooltip="超过此天数的历史记录将被自动清理"
                >
                  <InputNumber min={7} max={365} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" onClick={handleSave} loading={saving}>
                    保存设置
                  </Button>
                </Form.Item>
              </Form>
            </Spin>
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
