import React, { useState } from 'react';
import { Table, Button, Popconfirm, Modal, Form, Input, Select, message } from 'antd';

interface IgnoreRule {
  id: string;
  type: 'table' | 'column';
  pattern: string;
  description: string;
}

const IgnoreRules: React.FC = () => {
  const [rules, setRules] = useState<IgnoreRule[]>([
    { id: '1', type: 'table', pattern: 'temp_%', description: '忽略所有以temp_开头的临时表' },
    { id: '2', type: 'table', pattern: 'bak_%', description: '忽略所有备份表' },
    { id: '3', type: 'column', pattern: 'create_time', description: '忽略创建时间字段的比对' },
    { id: '4', type: 'column', pattern: 'update_time', description: '忽略更新时间字段的比对' },
  ]);
  const [visible, setVisible] = useState(false);
  const [form] = Form.useForm();

  const handleDelete = (id: string) => {
    setRules(rules.filter(r => r.id !== id));
    message.success('删除成功');
  };

  const handleAdd = async () => {
    try {
      const values = await form.validateFields();
      setRules([...rules, { id: Date.now().toString(), ...values }]);
      setVisible(false);
      form.resetFields();
      message.success('添加成功');
    } catch (e) {
      // 表单校验失败
    }
  };

  const columns = [
    { 
      title: '规则类型', 
      dataIndex: 'type', 
      render: (t: string) => t === 'table' ? '表名规则' : '字段规则' 
    },
    { title: '匹配模式', dataIndex: 'pattern' },
    { title: '描述', dataIndex: 'description' },
    {
      title: '操作',
      key: 'action',
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
      <Table columns={columns} dataSource={rules} rowKey="id" pagination={false} />
      
      <Modal 
        title="新增忽略规则" 
        open={visible} 
        onOk={handleAdd} 
        onCancel={() => {
          setVisible(false);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="type" label="规则类型" rules={[{ required: true, message: '请选择规则类型' }]}>
            <Select options={[
              { label: '表名规则', value: 'table' }, 
              { label: '字段规则', value: 'column' }
            ]} placeholder="请选择规则类型" />
          </Form.Item>
          <Form.Item name="pattern" label="匹配模式 (支持通配符 %)" rules={[{ required: true, message: '请输入匹配模式' }]}>
            <Input placeholder="例如: temp_%" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input placeholder="规则说明" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default IgnoreRules;
