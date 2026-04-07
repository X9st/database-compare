import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Select, InputNumber, Button, Space, message, Upload, Typography } from 'antd';
import { EyeInvisibleOutlined, EyeTwoTone, UploadOutlined } from '@ant-design/icons';
import { dataSourceApi } from '@/services/dataSourceApi';
import { CreateRemoteDatasetDto, DatabaseType, FileSourceMode, FileUploadResult } from '@/types';
import { useDataSourceStore } from '@/stores/dataSourceStore';

const DB_TYPE_OPTIONS = [
  { label: 'MySQL', value: 'mysql', defaultPort: 3306 },
  { label: 'Oracle', value: 'oracle', defaultPort: 1521 },
  { label: '达梦 (DM)', value: 'dm', defaultPort: 5236 },
  { label: 'Inceptor', value: 'inceptor', defaultPort: 10000 },
  { label: 'Excel (.xlsx/.xls)', value: 'excel' },
  { label: 'DBF', value: 'dbf' },
] as const;

const INCEPTOR_AUTH_OPTIONS = [
  { label: '自动（默认）', value: '' },
  { label: 'LDAP', value: 'LDAP' },
  { label: 'NOSASL', value: 'NOSASL' },
  { label: 'NONE', value: 'NONE' },
  { label: 'CUSTOM', value: 'CUSTOM' },
];

const INCEPTOR_TRANSPORT_OPTIONS = [
  { label: '自动（默认）', value: '' },
  { label: 'BINARY', value: 'BINARY' },
  { label: 'HTTP', value: 'HTTP' },
  { label: 'HTTPS', value: 'HTTPS' },
];

interface Props {
  visible: boolean;
  editingId: string | null;
  onClose: () => void;
  onSuccess: () => void;
}

const FILE_DB_TYPES: DatabaseType[] = ['excel', 'dbf'];

const DataSourceForm: React.FC<Props> = ({ visible, editingId, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<FileUploadResult | null>(null);
  const { groups, fetchGroups } = useDataSourceStore();

  const isEdit = !!editingId;
  const dbType = Form.useWatch('db_type', form) as DatabaseType | undefined;
  const isInceptor = dbType === 'inceptor';
  const inceptorAuthMode = Form.useWatch('inceptor_auth_mode', form) as string | undefined;
  const isFileSource = !!dbType && FILE_DB_TYPES.includes(dbType);
  const fileMode = (Form.useWatch('file_mode', form) as FileSourceMode | undefined) || 'single_file';
  const isRemoteDataset = isFileSource && fileMode === 'remote_dataset';

  useEffect(() => {
    if (visible) {
      fetchGroups().catch(() => {});
    }
  }, [visible, fetchGroups]);

  useEffect(() => {
    if (visible && editingId) {
      dataSourceApi
        .getById(editingId)
        .then((res) => {
          const data = res.data?.data;
          const mode: FileSourceMode =
            data?.extra_config?.mode || (data?.extra_config?.sftp ? 'remote_dataset' : 'single_file');
          form.setFieldsValue({
            ...(data || {}),
            file_mode: mode,
            inceptor_auth_mode:
              data?.extra_config?.inceptor_auth_mode || data?.extra_config?.auth_mode || undefined,
            inceptor_auth_fallback_modes: Array.isArray(data?.extra_config?.inceptor_auth_fallback_modes)
              ? data.extra_config.inceptor_auth_fallback_modes.join(',')
              : Array.isArray(data?.extra_config?.auth_fallback_modes)
                ? data.extra_config.auth_fallback_modes.join(',')
                : undefined,
            inceptor_transport_mode:
              data?.extra_config?.inceptor_transport_mode || data?.extra_config?.transport_mode || undefined,
            inceptor_transport_fallback_modes: Array.isArray(data?.extra_config?.inceptor_transport_fallback_modes)
              ? data.extra_config.inceptor_transport_fallback_modes.join(',')
              : Array.isArray(data?.extra_config?.transport_fallback_modes)
                ? data.extra_config.transport_fallback_modes.join(',')
                : undefined,
            remote_host: data?.extra_config?.sftp?.host,
            remote_port: data?.extra_config?.sftp?.port || 22,
            remote_username: data?.extra_config?.sftp?.username,
            remote_base_dir: data?.extra_config?.sftp?.base_dir,
            remote_password: undefined,
          });
          if (mode === 'single_file' && data?.extra_config?.storage_key) {
            setUploadedFile({
              file_id: String(data.extra_config.file_id || ''),
              storage_key: data.extra_config.storage_key,
              original_name: String(data.extra_config.original_name || ''),
              file_type: data.extra_config.file_type || 'xlsx',
              file_size: Number(data.extra_config.file_size || 0),
            });
          } else {
            setUploadedFile(null);
          }
        })
        .catch(() => {
          const ds = useDataSourceStore.getState().dataSources.find((d) => d.id === editingId);
          if (ds) {
            const mode: FileSourceMode =
              ds?.extra_config?.mode || (ds?.extra_config?.sftp ? 'remote_dataset' : 'single_file');
            form.setFieldsValue({
              ...ds,
              file_mode: mode,
              inceptor_auth_mode:
                ds?.extra_config?.inceptor_auth_mode || ds?.extra_config?.auth_mode || undefined,
              inceptor_auth_fallback_modes: Array.isArray(ds?.extra_config?.inceptor_auth_fallback_modes)
                ? ds.extra_config.inceptor_auth_fallback_modes.join(',')
                : Array.isArray(ds?.extra_config?.auth_fallback_modes)
                  ? ds.extra_config.auth_fallback_modes.join(',')
                  : undefined,
              inceptor_transport_mode:
                ds?.extra_config?.inceptor_transport_mode || ds?.extra_config?.transport_mode || undefined,
              inceptor_transport_fallback_modes: Array.isArray(ds?.extra_config?.inceptor_transport_fallback_modes)
                ? ds.extra_config.inceptor_transport_fallback_modes.join(',')
                : Array.isArray(ds?.extra_config?.transport_fallback_modes)
                  ? ds.extra_config.transport_fallback_modes.join(',')
                  : undefined,
              remote_host: ds?.extra_config?.sftp?.host,
              remote_port: ds?.extra_config?.sftp?.port || 22,
              remote_username: ds?.extra_config?.sftp?.username,
              remote_base_dir: ds?.extra_config?.sftp?.base_dir,
              remote_password: undefined,
            });
            if (mode === 'single_file' && ds.extra_config?.storage_key) {
              setUploadedFile({
                file_id: String(ds.extra_config.file_id || ''),
                storage_key: ds.extra_config.storage_key,
                original_name: String(ds.extra_config.original_name || ''),
                file_type: ds.extra_config.file_type || 'xlsx',
                file_size: Number((ds.extra_config as any).file_size || 0),
              });
            } else {
              setUploadedFile(null);
            }
          }
        });
    } else if (visible) {
      setUploadedFile(null);
      form.resetFields();
      form.setFieldsValue({
        charset: 'UTF-8',
        timeout: 30,
        file_mode: 'single_file',
        remote_port: 22,
        inceptor_auth_mode: undefined,
        inceptor_auth_fallback_modes: undefined,
        inceptor_transport_mode: undefined,
        inceptor_transport_fallback_modes: undefined,
      });
    }
  }, [visible, editingId, form]);

  const handleDbTypeChange = (nextDbType: DatabaseType) => {
    const option = DB_TYPE_OPTIONS.find((o) => o.value === nextDbType);
    if (option && 'defaultPort' in option && option.defaultPort) {
      form.setFieldValue('port', option.defaultPort);
    }
    if (FILE_DB_TYPES.includes(nextDbType)) {
      form.setFieldsValue({
        file_mode: form.getFieldValue('file_mode') || 'single_file',
        host: undefined,
        port: undefined,
        username: undefined,
        password: undefined,
      });
    } else {
      setUploadedFile(null);
      if (nextDbType !== 'inceptor') {
        form.setFieldsValue({
          inceptor_auth_mode: undefined,
          inceptor_auth_fallback_modes: undefined,
          inceptor_transport_mode: undefined,
          inceptor_transport_fallback_modes: undefined,
        });
      }
    }
  };

  const handleFileModeChange = (nextMode: FileSourceMode) => {
    form.setFieldValue('file_mode', nextMode);
    if (nextMode === 'single_file') {
      form.setFieldsValue({
        remote_host: undefined,
        remote_port: 22,
        remote_username: undefined,
        remote_password: undefined,
        remote_base_dir: undefined,
      });
      return;
    }
    setUploadedFile(null);
  };

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    try {
      const response = await dataSourceApi.uploadFile(file);
      const payload = response.data?.data;
      if (!payload) {
        message.error('上传失败：服务未返回文件信息');
        return Upload.LIST_IGNORE;
      }
      setUploadedFile(payload);

      const nextDbType: DatabaseType = payload.file_type === 'dbf' ? 'dbf' : 'excel';
      form.setFieldsValue({
        db_type: nextDbType,
        database: form.getFieldValue('database') || payload.original_name,
      });
      setUploadedFile(payload);
      message.success('文件上传成功');
    } catch (e: any) {
      const backendMessage = e?.response?.data?.detail || e?.response?.data?.message || e?.message;
      message.error(`上传失败: ${backendMessage || '未知错误'}`);
    } finally {
      setUploading(false);
    }
    return Upload.LIST_IGNORE;
  };

  const handleTestConnection = async () => {
    try {
      const values = await form.validateFields();
      const testPayload: any = { ...values };
      if (isRemoteDataset) {
        if (!values.remote_password) {
          message.warning('远程目录测试连接需要输入 SFTP 密码');
          return;
        }
        testPayload.extra_config = {
          mode: 'remote_dataset',
          file_type: values.db_type === 'dbf' ? 'dbf' : 'xlsx',
          sftp: {
            host: values.remote_host,
            port: values.remote_port || 22,
            username: values.remote_username,
            password: values.remote_password,
            base_dir: values.remote_base_dir,
          },
        };
      }
      if (isFileSource) {
        if (!isRemoteDataset && !uploadedFile?.storage_key) {
          message.warning('请先上传文件');
          return;
        }
        if (!isRemoteDataset) {
          testPayload.extra_config = {
            mode: 'single_file',
            file_id: uploadedFile?.file_id,
            storage_key: uploadedFile?.storage_key,
            original_name: uploadedFile?.original_name,
            file_type: uploadedFile?.file_type,
            sheet_mode: 'all',
            header_row: 1,
          };
        }
      }
      if (values.db_type === 'inceptor') {
        const fallbackModes = String(values.inceptor_auth_fallback_modes || '')
          .split(',')
          .map((item: string) => item.trim().toUpperCase())
          .filter(Boolean);
        const transportFallbackModes = String(values.inceptor_transport_fallback_modes || '')
          .split(',')
          .map((item: string) => item.trim().toUpperCase())
          .filter(Boolean);
        testPayload.extra_config = {
          ...(testPayload.extra_config || {}),
          ...(values.inceptor_auth_mode
            ? { inceptor_auth_mode: String(values.inceptor_auth_mode).trim().toUpperCase() }
            : {}),
          ...(fallbackModes.length > 0
            ? { inceptor_auth_fallback_modes: fallbackModes }
            : {}),
          ...(values.inceptor_transport_mode
            ? { inceptor_transport_mode: String(values.inceptor_transport_mode).trim().toUpperCase() }
            : {}),
          ...(transportFallbackModes.length > 0
            ? { inceptor_transport_fallback_modes: transportFallbackModes }
            : {}),
        };
      }
      if (isFileSource && !isRemoteDataset && !testPayload.extra_config?.storage_key) {
        message.warning('请先上传文件');
        return;
      }
      setTesting(true);
      try {
        const result = await dataSourceApi.testConnectionDirect(testPayload);
        if (result.data?.data?.success) {
          message.success(`连接成功！数据库版本: ${result.data.data.version}`);
        } else {
          message.error(`连接失败: ${result.data?.data?.message || '未知错误'}`);
        }
      } catch (e: any) {
        const backendMessage = e?.response?.data?.detail || e?.response?.data?.message || e?.message;
        message.error(`连接测试失败: ${backendMessage || '请检查网络或后端服务'}`);
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
      const payload: any = { ...values };
      const store = useDataSourceStore.getState();

      delete payload.file_mode;
      delete payload.remote_host;
      delete payload.remote_port;
      delete payload.remote_username;
      delete payload.remote_password;
      delete payload.remote_base_dir;
      delete payload.inceptor_auth_mode;
      delete payload.inceptor_auth_fallback_modes;
      delete payload.inceptor_transport_mode;
      delete payload.inceptor_transport_fallback_modes;

      if (!payload.password) {
        delete payload.password;
      }

      if (FILE_DB_TYPES.includes(payload.db_type)) {
        if (isRemoteDataset) {
          const remotePassword = values.remote_password;
          if (!isEdit && !remotePassword) {
            message.warning('创建远程目录数据集时必须输入 SFTP 密码');
            return;
          }

          const remoteExtraConfig: any = {
            mode: 'remote_dataset',
            file_type: payload.db_type === 'dbf' ? 'dbf' : 'xlsx',
            sftp: {
              host: values.remote_host,
              port: values.remote_port || 22,
              username: values.remote_username,
              base_dir: values.remote_base_dir,
            },
          };
          if (remotePassword) {
            remoteExtraConfig.sftp.password = remotePassword;
          }

          if (isEdit) {
            payload.extra_config = remoteExtraConfig;
          } else {
            const remoteCreatePayload: CreateRemoteDatasetDto = {
              name: values.name,
              group_id: values.group_id,
              db_type: values.db_type,
              database: values.database,
              charset: values.charset || 'UTF-8',
              timeout: values.timeout || 30,
              extra_config: remoteExtraConfig,
            };
            setLoading(true);
            await store.addRemoteDataset(remoteCreatePayload);
            message.success('创建并首次导入成功');
            onSuccess();
            return;
          }
        } else {
          const existingExtraConfig = uploadedFile
            ? {
                mode: 'single_file',
                file_id: uploadedFile.file_id,
                storage_key: uploadedFile.storage_key,
                original_name: uploadedFile.original_name,
                file_type: uploadedFile.file_type,
              }
            : {};
          if (!existingExtraConfig?.storage_key) {
            message.warning('请先上传文件');
            return;
          }
          payload.extra_config = {
            ...existingExtraConfig,
            sheet_mode: 'all',
            header_row: 1,
          };
          if (!payload.database) {
            payload.database = existingExtraConfig.original_name || 'file_source';
          }
        }
      }
      if (payload.db_type === 'inceptor') {
        const fallbackModes = String(values.inceptor_auth_fallback_modes || '')
          .split(',')
          .map((item: string) => item.trim().toUpperCase())
          .filter(Boolean);
        const transportFallbackModes = String(values.inceptor_transport_fallback_modes || '')
          .split(',')
          .map((item: string) => item.trim().toUpperCase())
          .filter(Boolean);
        const inceptorExtra = {
          ...(payload.extra_config || {}),
          ...(values.inceptor_auth_mode
            ? { inceptor_auth_mode: String(values.inceptor_auth_mode).trim().toUpperCase() }
            : {}),
          ...(fallbackModes.length > 0
            ? { inceptor_auth_fallback_modes: fallbackModes }
            : {}),
          ...(values.inceptor_transport_mode
            ? { inceptor_transport_mode: String(values.inceptor_transport_mode).trim().toUpperCase() }
            : {}),
          ...(transportFallbackModes.length > 0
            ? { inceptor_transport_fallback_modes: transportFallbackModes }
            : {}),
        };
        payload.extra_config = Object.keys(inceptorExtra).length > 0 ? inceptorExtra : undefined;
      }

      setLoading(true);

      if (isEdit) {
        await store.updateDataSource(editingId!, payload);
        message.success('更新成功');
      } else {
        await store.addDataSource(payload);
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
      width={640}
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
          <Input placeholder="例如：生产环境-MySQL / 销售报表-Excel" />
        </Form.Item>

        <Form.Item name="group_id" label="所属分组">
          <Select
            allowClear
            placeholder="可选：选择数据源分组"
            options={groups.map((group) => ({ label: group.name, value: group.id }))}
          />
        </Form.Item>

        <Form.Item
          name="db_type"
          label="数据库类型"
          rules={[{ required: true, message: '请选择数据库类型' }]}
        >
          <Select
            options={DB_TYPE_OPTIONS as any}
            onChange={handleDbTypeChange}
            placeholder="请选择数据库类型"
          />
        </Form.Item>

        {isFileSource ? (
          <>
            <Form.Item name="file_mode" label="文件源模式" initialValue="single_file">
              <Select
                onChange={handleFileModeChange}
                options={[
                  { label: '本地上传单文件', value: 'single_file' },
                  { label: '远程目录数据集 (SFTP)', value: 'remote_dataset' },
                ]}
              />
            </Form.Item>

            {isRemoteDataset ? (
              <>
                <Space style={{ display: 'flex' }} align="start">
                  <Form.Item
                    name="remote_host"
                    label="SFTP 主机"
                    rules={[{ required: true, message: '请输入 SFTP 主机地址' }]}
                    style={{ flex: 1 }}
                  >
                    <Input placeholder="192.168.1.100" />
                  </Form.Item>
                  <Form.Item
                    name="remote_port"
                    label="端口"
                    initialValue={22}
                    rules={[{ required: true, message: '请输入端口' }]}
                    style={{ width: 120 }}
                  >
                    <InputNumber min={1} max={65535} style={{ width: '100%' }} />
                  </Form.Item>
                </Space>

                <Space style={{ display: 'flex' }} align="start">
                  <Form.Item
                    name="remote_username"
                    label="SFTP 用户名"
                    rules={[{ required: true, message: '请输入 SFTP 用户名' }]}
                    style={{ flex: 1 }}
                  >
                    <Input placeholder="请输入用户名" />
                  </Form.Item>
                  <Form.Item
                    name="remote_password"
                    label="SFTP 密码"
                    rules={[{ required: !isEdit, message: '请输入 SFTP 密码' }]}
                    style={{ flex: 1 }}
                  >
                    <Input.Password
                      placeholder={isEdit ? '留空表示不修改' : '请输入 SFTP 密码'}
                      iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    />
                  </Form.Item>
                </Space>

                <Form.Item
                  name="remote_base_dir"
                  label="远程目录"
                  rules={[{ required: true, message: '请输入远程目录' }]}
                >
                  <Input placeholder="/data/inbound" />
                </Form.Item>
              </>
            ) : (
              <Form.Item label="上传文件">
                <Upload beforeUpload={handleFileUpload} showUploadList={false} accept=".xlsx,.xls,.dbf">
                  <Button icon={<UploadOutlined />} loading={uploading}>
                    选择文件并上传
                  </Button>
                </Upload>
                {uploadedFile ? (
                  <Typography.Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                    已上传: {uploadedFile.original_name} ({uploadedFile.file_type.toUpperCase()})
                  </Typography.Text>
                ) : (
                  <Typography.Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                    支持 .xlsx / .xls / .dbf
                  </Typography.Text>
                )}
              </Form.Item>
            )}

            <Form.Item name="database" label="数据集名称（可选）">
              <Input placeholder={isRemoteDataset ? '用于标识该目录数据集' : '默认使用文件名'} />
            </Form.Item>
          </>
        ) : (
          <>
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
              <Input placeholder="Oracle 需要填写" />
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
                rules={[
                  {
                    validator: async (_, value) => {
                      const authMode = String(inceptorAuthMode || '').trim().toUpperCase();
                      const passwordOptional = isInceptor && ['NONE', 'NOSASL'].includes(authMode);
                      if (isEdit && !value) {
                        return;
                      }
                      if (passwordOptional && !value) {
                        return;
                      }
                      if (!value) {
                        throw new Error('请输入密码');
                      }
                    },
                  },
                ]}
                style={{ flex: 1 }}
              >
                <Input.Password
                  placeholder={
                    isEdit
                      ? '留空表示不修改'
                      : (isInceptor && ['NONE', 'NOSASL'].includes(String(inceptorAuthMode || '').trim().toUpperCase())
                          ? 'NONE/NOSASL 可留空'
                          : '请输入密码')
                  }
                  iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                />
              </Form.Item>
            </Space>

            {isInceptor ? (
              <>
                <Space style={{ display: 'flex' }} align="start">
                  <Form.Item name="inceptor_auth_mode" label="Inceptor 认证模式" style={{ width: 220 }}>
                    <Select options={INCEPTOR_AUTH_OPTIONS} />
                  </Form.Item>
                  <Form.Item name="inceptor_auth_fallback_modes" label="认证回退模式（可选）" style={{ flex: 1 }}>
                    <Input placeholder="例如：NOSASL,NONE" />
                  </Form.Item>
                </Space>
                <Space style={{ display: 'flex' }} align="start">
                  <Form.Item name="inceptor_transport_mode" label="Inceptor 传输模式" style={{ width: 220 }}>
                    <Select options={INCEPTOR_TRANSPORT_OPTIONS} />
                  </Form.Item>
                  <Form.Item
                    name="inceptor_transport_fallback_modes"
                    label="传输回退模式（可选）"
                    style={{ flex: 1 }}
                  >
                    <Input placeholder="例如：HTTP,HTTPS" />
                  </Form.Item>
                </Space>
              </>
            ) : null}

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
          </>
        )}
      </Form>
    </Modal>
  );
};

export default DataSourceForm;
