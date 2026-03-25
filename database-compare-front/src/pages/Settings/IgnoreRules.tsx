import React, { useState, useEffect } from 'react';
import { Table, Button, Popconfirm, Modal, Form, Input, Select, Switch, message, Spin } from 'antd';
import { settingsApi, IgnoreRule } from '@/services/settingsApi';

const IgnoreRules: React.FC = () => {
  const [rules, setRules] = useState<IgnoreRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm();

  const fetchRules = async () => {
    setLoading(true);
    try {
      const response = await settingsApi.getIgnoreRules();
      const data = response.data?.data || [];
      setRules(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to fetch ignore rules:', e);
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await settingsApi.deleteIgnoreRule(id);
      message.success('删除成功');
      fetchRules();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    try {
      await settingsApi.toggleIgnoreRule(id, enabled);
      message.success(enabled ? '已启用' : '已禁用');
      fetchRules();
    } catch (e) {
      message.error('操作失败');
    }
  };

  const handleAdd = async () => {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      await settingsApi.createIgnoreRule({
        name: values.name,
        rule_type: values.rule_type,
        pattern: values.pattern,
        enabled: true,
      });
      setVisible(false);
      form.resetFields();
      message.success('添加成功');
      fetchRules();
    } catch (e) {
      message.error('添加失败');
    } finally {
      setSubmitting(false);
    }
  };

  const getRuleTypeText = (type: string) => {
    switch (type) {
      case 'table': return '表名规则';
      case 'column': return '字段规则';
      case 'dataType': return '数据类型规则';
      case 'diffType': return '差异类型规则';
      default: return type;
    }
  };

  const columns = [
    { 
      title: '规则名称', 
      dataIndex: 'name',
      width: 150,
    },
    { 
      title: '规则类型', 
      dataIndex: 'rule_type', 
      width: 120,
      render: (t: string) => getRuleTypeText(t),
    },
    { title: '匹配模式', dataIndex: 'pattern' },
    {
      title: '状态',
      dataIndex: 'enabled',
      width: 100,
      render: (enabled: boolean, record: IgnoreRule) => (
        <Switch 
          checked={enabled} 
          onChange={(checked) => handleToggle(record.id, checked)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: any, record: IgnoreRule) => (
        <Popconfirm title="确定删除此规则？" onConfirm={() => handleDelete(record.id)}>
          <Button type="link" danger>删除</Button>
        </Popconfirm>
      )
    }
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={() => setVisible(true)}>新增规则</Button>
      </div>
      <Spin spinning={loading}>
        <Table 
          columns={columns} 
          dataSource={rules} 
          rowKey="id" 
          pagination={false}
          locale={{ emptyText: '暂无忽略规则' }}
        />
      </Spin>
      
      <Modal 
        title="新增忽略规则" 
        open={visible} 
        onOk={handleAdd}
        confirmLoading={submitting}
        onCancel={() => {
          setVisible(false);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="name" 
            label="规则名称" 
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="例如: 忽略临时表" />
          </Form.Item>
          <Form.Item 
            name="rule_type" 
            label="规则类型" 
            rules={[{ required: true, message: '请选择规则类型' }]}
          >
            <Select 
              options={[
                { label: '表名规则', value: 'table' }, 
                { label: '字段规则', value: 'column' },
                { label: '数据类型规则', value: 'dataType' },
                { label: '差异类型规则', value: 'diffType' },
              ]} 
              placeholder="请选择规则类型" 
            />
          </Form.Item>
          <Form.Item 
            name="pattern" 
            label="匹配模式" 
            rules={[{ required: true, message: '请输入匹配模式' }]}
            tooltip="支持通配符: % 匹配任意字符, _ 匹配单个字符"
          >
            <Input placeholder="例如: temp_%, %_bak, update_time" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default IgnoreRules;
