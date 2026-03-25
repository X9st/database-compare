import React, { useEffect, useState } from 'react';
import { Tabs, Form, InputNumber, Switch, Button, Card, message, Spin } from 'antd';
import IgnoreRules from './IgnoreRules';
import { settingsApi } from '@/services/settingsApi';

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
          compare_thread_count: data.compare_thread_count || 4,
          db_query_timeout: data.db_query_timeout || 60,
          compare_timeout: data.compare_timeout || 3600,
          max_diff_display: data.max_diff_display || 1000,
          history_retention_days: data.history_retention_days || 90,
          auto_cleanup_enabled: data.auto_cleanup_enabled ?? true,
        });
      }
    } catch (e) {
      console.error('Failed to fetch settings:', e);
      // 使用默认值
      form.setFieldsValue({
        compare_thread_count: 4,
        db_query_timeout: 60,
        compare_timeout: 3600,
        max_diff_display: 1000,
        history_retention_days: 90,
        auto_cleanup_enabled: true,
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
        compare_thread_count: values.compare_thread_count,
        db_query_timeout: values.db_query_timeout,
        compare_timeout: values.compare_timeout,
        max_diff_display: values.max_diff_display,
        history_retention_days: values.history_retention_days,
        auto_cleanup_enabled: values.auto_cleanup_enabled,
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
                  name="compare_thread_count" 
                  label="默认比对线程数"
                  tooltip="并发比对的线程数量，值越大比对速度越快，但消耗资源更多"
                >
                  <InputNumber min={1} max={16} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="db_query_timeout" 
                  label="数据库查询超时时间 (秒)"
                  tooltip="单次数据库查询的最长等待时间"
                >
                  <InputNumber min={10} max={600} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="compare_timeout" 
                  label="比对任务总超时 (秒)"
                  tooltip="整次比对任务的最长等待时间"
                >
                  <InputNumber min={60} max={86400} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="auto_cleanup_enabled" 
                  label="开启自动清理历史" 
                  valuePropName="checked"
                  tooltip="自动清理超过保留期限的历史记录"
                >
                  <Switch />
                </Form.Item>
                <Form.Item 
                  name="max_diff_display" 
                  label="最大差异显示数量"
                  tooltip="单次比对结果最多显示的差异条数"
                >
                  <InputNumber min={100} max={10000} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item 
                  name="history_retention_days" 
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
