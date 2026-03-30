import React, { useEffect, useState } from 'react';
import { Tabs, Form, InputNumber, Switch, Button, Card, message, Spin, Table, Modal, Input, Space, Upload, Typography } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import IgnoreRules from './IgnoreRules';
import { settingsApi, CompareTemplate } from '@/services/settingsApi';
import { resolveApiUrl } from '@/services/api';

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState<CompareTemplate[]>([]);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [templateConfig, setTemplateConfig] = useState('{\n  "source_id": "",\n  "target_id": "",\n  "table_selection": { "mode": "all", "tables": [] },\n  "options": { "mode": "full" }\n}');
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null);
  const [exportingConfig, setExportingConfig] = useState(false);
  const [importingConfig, setImportingConfig] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [exportConfigOptions, setExportConfigOptions] = useState({
    include_datasources: true,
    include_templates: true,
    include_rules: true,
    include_system_settings: true,
  });

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
          history_max_count: data.history_max_count || 500,
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
        history_max_count: 500,
        auto_cleanup_enabled: true,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    setTemplateLoading(true);
    try {
      const response = await settingsApi.getTemplates();
      setTemplates(response.data?.data || []);
    } catch (e) {
      setTemplates([]);
    } finally {
      setTemplateLoading(false);
    }
  };

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
        history_max_count: values.history_max_count,
        auto_cleanup_enabled: values.auto_cleanup_enabled,
      });
      message.success('设置保存成功');
    } catch (e) {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const openCreateTemplate = () => {
    setEditingTemplateId(null);
    setTemplateName('');
    setTemplateDescription('');
    setTemplateConfig('{\n  "source_id": "",\n  "target_id": "",\n  "table_selection": { "mode": "all", "tables": [] },\n  "options": { "mode": "full" }\n}');
    setTemplateModalVisible(true);
  };

  const openEditTemplate = (template: CompareTemplate) => {
    setEditingTemplateId(template.id);
    setTemplateName(template.name);
    setTemplateDescription(template.description || '');
    setTemplateConfig(JSON.stringify(template.config || {}, null, 2));
    setTemplateModalVisible(true);
  };

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) {
      message.warning('请输入模板名称');
      return;
    }
    let parsedConfig: Record<string, any> = {};
    try {
      parsedConfig = JSON.parse(templateConfig);
    } catch {
      message.error('模板配置 JSON 格式不合法');
      return;
    }
    try {
      if (editingTemplateId) {
        await settingsApi.updateTemplate(editingTemplateId, {
          name: templateName.trim(),
          description: templateDescription || undefined,
          config: parsedConfig,
        });
        message.success('模板更新成功');
      } else {
        await settingsApi.createTemplate({
          name: templateName.trim(),
          description: templateDescription || undefined,
          config: parsedConfig,
        });
        message.success('模板创建成功');
      }
      setTemplateModalVisible(false);
      fetchTemplates();
    } catch {
      message.error('模板保存失败');
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    try {
      await settingsApi.deleteTemplate(id);
      message.success('模板删除成功');
      fetchTemplates();
    } catch {
      message.error('模板删除失败');
    }
  };

  const handleCreateTaskByTemplate = async (id: string) => {
    try {
      const response = await settingsApi.createTaskFromTemplate(id, {});
      const task_id = response.data?.data?.task_id;
      message.success(`任务已创建: ${task_id}`);
    } catch {
      message.error('按模板建任务失败');
    }
  };

  const handleExportConfig = async () => {
    setExportingConfig(true);
    try {
      const response = await settingsApi.exportConfig(exportConfigOptions);
      const payload = response.data?.data;
      if (payload?.download_url) {
        window.open(resolveApiUrl(payload.download_url), '_blank');
      }
      message.success('配置导出成功');
    } catch {
      message.error('配置导出失败');
    } finally {
      setExportingConfig(false);
    }
  };

  const handleImportConfig = async () => {
    if (!importFile) {
      message.warning('请先选择配置文件');
      return;
    }
    setImportingConfig(true);
    try {
      const response = await settingsApi.importConfig(importFile);
      const payload = response.data?.data;
      message.success(
        `导入完成：数据源${payload?.datasources_imported || 0}，模板${payload?.templates_imported || 0}，规则${payload?.rules_imported || 0}`
      );
      setImportFile(null);
      fetchSettings();
      fetchTemplates();
    } catch {
      message.error('配置导入失败');
    } finally {
      setImportingConfig(false);
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
                <Form.Item
                  name="history_max_count"
                  label="历史记录最大保留条数"
                  tooltip="超过条数上限后，自动删除更旧的历史记录"
                >
                  <InputNumber min={50} max={50000} style={{ width: '100%' }} />
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
          <Tabs.TabPane tab="比对模板" key="3">
            <div style={{ marginBottom: 12 }}>
              <Button type="primary" onClick={openCreateTemplate}>新增模板</Button>
            </div>
            <Table
              rowKey="id"
              loading={templateLoading}
              dataSource={templates}
              columns={[
                { title: '模板名称', dataIndex: 'name' },
                { title: '描述', dataIndex: 'description', render: (value: string) => value || '-' },
                { title: '创建时间', dataIndex: 'created_at', width: 180 },
                {
                  title: '操作',
                  width: 280,
                  render: (_: unknown, record: CompareTemplate) => (
                    <Space>
                      <Button type="link" onClick={() => openEditTemplate(record)}>编辑</Button>
                      <Button type="link" onClick={() => handleCreateTaskByTemplate(record.id)}>按模板建任务</Button>
                      <Button type="link" danger onClick={() => handleDeleteTemplate(record.id)}>删除</Button>
                    </Space>
                  ),
                },
              ]}
            />
            <Modal
              title={editingTemplateId ? '编辑模板' : '新增模板'}
              open={templateModalVisible}
              onCancel={() => setTemplateModalVisible(false)}
              onOk={handleSaveTemplate}
              width={780}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <Input
                  placeholder="模板名称"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                />
                <Input
                  placeholder="模板描述（可选）"
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                />
                <Input.TextArea
                  rows={14}
                  value={templateConfig}
                  onChange={(e) => setTemplateConfig(e.target.value)}
                />
              </Space>
            </Modal>
          </Tabs.TabPane>
          <Tabs.TabPane tab="配置迁移" key="4">
            <Space direction="vertical" size={16} style={{ width: '100%', maxWidth: 720 }}>
              <Card size="small" title="导出配置">
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Space wrap>
                    <span>导出数据源</span>
                    <Switch
                      checked={exportConfigOptions.include_datasources}
                      onChange={(checked) =>
                        setExportConfigOptions((prev) => ({ ...prev, include_datasources: checked }))
                      }
                    />
                  </Space>
                  <Space wrap>
                    <span>导出模板</span>
                    <Switch
                      checked={exportConfigOptions.include_templates}
                      onChange={(checked) =>
                        setExportConfigOptions((prev) => ({ ...prev, include_templates: checked }))
                      }
                    />
                  </Space>
                  <Space wrap>
                    <span>导出忽略规则</span>
                    <Switch
                      checked={exportConfigOptions.include_rules}
                      onChange={(checked) =>
                        setExportConfigOptions((prev) => ({ ...prev, include_rules: checked }))
                      }
                    />
                  </Space>
                  <Space wrap>
                    <span>导出系统设置</span>
                    <Switch
                      checked={exportConfigOptions.include_system_settings}
                      onChange={(checked) =>
                        setExportConfigOptions((prev) => ({ ...prev, include_system_settings: checked }))
                      }
                    />
                  </Space>
                  <Button type="primary" loading={exportingConfig} onClick={handleExportConfig}>
                    导出配置文件
                  </Button>
                </Space>
              </Card>

              <Card size="small" title="导入配置">
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <Upload
                    beforeUpload={(file) => {
                      setImportFile(file);
                      return false;
                    }}
                    maxCount={1}
                    accept=".json,application/json"
                    onRemove={() => {
                      setImportFile(null);
                      return true;
                    }}
                    fileList={importFile ? [{ uid: '-1', name: importFile.name, status: 'done' as const }] : []}
                  >
                    <Button icon={<UploadOutlined />}>选择配置文件</Button>
                  </Upload>
                  <Typography.Text type="secondary">
                    支持 UTF-8 编码的 JSON 配置文件
                  </Typography.Text>
                  <Button type="primary" loading={importingConfig} onClick={handleImportConfig}>
                    导入配置
                  </Button>
                </Space>
              </Card>
            </Space>
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Settings;
