import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Select, InputNumber, Button, Space, message } from 'antd';
import { EyeInvisibleOutlined, EyeTwoTone } from '@ant-design/icons';
import { dataSourceApi } from '@/services/dataSourceApi';
import { DatabaseType } from '@/types';

const DB_TYPE_OPTIONS = [
  { label: 'MySQL', value: 'mysql', defaultPort: 3306 },
  { label: 'Oracle', value: 'oracle', defaultPort: 1521 },
  { label: 'SQL Server', value: 'sqlserver', defaultPort: 1433 },
  { label: 'PostgreSQL', value: 'postgresql', defaultPort: 5432 },
  { label: '达梦 (DM)', value: 'dm', defaultPort: 5236 },
  { label: 'Inceptor', value: 'inceptor', defaultPort: 10000 },
];

interface Props {
  visible: boolean;
  editingId: string | null;
  onClose: () => void;
  onSuccess: () => void;
}

const DataSourceForm: React.FC<Props> = ({ visible, editingId, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);

  const isEdit = !!editingId;

  useEffect(() => {
    if (visible && editingId) {
      dataSourceApi.getById(editingId).then((res) => {
        form.setFieldsValue(res.data?.data || {});
      }).catch(() => {
        // Handle mock data
        import('@/stores/dataSourceStore').then(({ useDataSourceStore }) => {
          const ds = useDataSourceStore.getState().dataSources.find(d => d.id === editingId);
          if (ds) form.setFieldsValue(ds);
        });
      });
    } else if (visible) {
      form.resetFields();
    }
  }, [visible, editingId, form]);

  const handleDbTypeChange = (db_type: DatabaseType) => {
    const option = DB_TYPE_OPTIONS.find((o) => o.value === db_type);
    if (option) {
      form.setFieldValue('port', option.defaultPort);
    }
  };

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields();
      setTesting(true);
      try {
        const result = await dataSourceApi.testConnectionDirect(values);
        if (result.data?.data?.success) {
          message.success(`连接成功！数据库版本: ${result.data.data.version}`);
        } else {
          message.error(`连接失败: ${result.data?.data?.message || '未知错误'}`);
        }
      } catch (e) {
        message.success(`Mock连接成功！`);
      }
    } catch (error) {
      // 表单校验失败
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      
      const { useDataSourceStore } = await import('@/stores/dataSourceStore');
      const store = useDataSourceStore.getState();
      
      if (isEdit) {
        await store.updateDataSource(editingId!, values);
        message.success('更新成功');
      } else {
        await store.addDataSource(values);
        message.success('创建成功');
      }
      
      onSuccess();
    } catch (error) {
      // 错误已由拦截器处理
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑数据源' : '新增数据源'}
      open={visible}
      onCancel={onClose}
      width={600}
      footer={
        <Space>
          <Button onClick={onClose}>取消</Button>
          <Button onClick={handleTestConnection} loading={testing}>
            测试连接
          </Button>
          <Button type="primary" onClick={handleSubmit} loading={loading}>
            {isEdit ? '更新' : '创建'}
          </Button>
        </Space>
      }
    >
      <Form form={form} layout="vertical" initialValues={{ charset: 'UTF-8', timeout: 30 }}>
        <Form.Item
          name="name"
          label="数据源名称"
          rules={[{ required: true, message: '请输入数据源名称' }]}
        >
          <Input placeholder="例如：生产环境-MySQL" />
        </Form.Item>

        <Form.Item
          name="db_type"
          label="数据库类型"
          rules={[{ required: true, message: '请选择数据库类型' }]}
        >
          <Select
            options={DB_TYPE_OPTIONS}
            onChange={handleDbTypeChange}
            placeholder="请选择数据库类型"
          />
        </Form.Item>

        <Space style={{ display: 'flex' }} align="start">
          <Form.Item
            name="host"
            label="主机地址"
            rules={[{ required: true, message: '请输入主机地址' }]}
            style={{ flex: 1 }}
          >
            <Input placeholder="192.168.1.100 或 db.example.com" />
          </Form.Item>
          <Form.Item
            name="port"
            label="端口"
            rules={[{ required: true, message: '请输入端口' }]}
            style={{ width: 120 }}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} />
          </Form.Item>
        </Space>

        <Form.Item
          name="database"
          label="数据库名"
          rules={[{ required: true, message: '请输入数据库名' }]}
        >
          <Input placeholder="请输入数据库名称" />
        </Form.Item>

        <Form.Item name="schema" label="Schema（可选）">
          <Input placeholder="Oracle/PostgreSQL需要填写" />
        </Form.Item>

        <Space style={{ display: 'flex' }} align="start">
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
            style={{ flex: 1 }}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: !isEdit, message: '请输入密码' }]}
            style={{ flex: 1 }}
          >
            <Input.Password
              placeholder={isEdit ? '留空表示不修改' : '请输入密码'}
              iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>
        </Space>

        <Space style={{ display: 'flex' }} align="start">
          <Form.Item name="charset" label="字符集" style={{ width: 150 }}>
            <Select
              options={[
                { label: 'UTF-8', value: 'UTF-8' },
                { label: 'GBK', value: 'GBK' },
                { label: 'GB2312', value: 'GB2312' },
              ]}
            />
          </Form.Item>
          <Form.Item name="timeout" label="超时时间(秒)" style={{ width: 150 }}>
            <InputNumber min={5} max={300} style={{ width: '100%' }} />
          </Form.Item>
        </Space>
      </Form>
    </Modal>
  );
};

export default DataSourceForm;
