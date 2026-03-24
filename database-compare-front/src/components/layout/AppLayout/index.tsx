import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DatabaseOutlined,
  SwapOutlined,
  HistoryOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import TitleBar from '../TitleBar';
import styles from './index.module.less';

const { Sider, Content } = Layout;

const menuItems = [
  { key: '/datasource', icon: <DatabaseOutlined />, label: '数据源' },
  { key: '/compare', icon: <SwapOutlined />, label: '比对任务' },
  { key: '/history', icon: <HistoryOutlined />, label: '历史记录' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

const AppLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const selectedKey = '/' + location.pathname.split('/')[1];

  return (
    <Layout className={styles.layout}>
      <TitleBar />
      <Layout className={styles.main}>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="light"
          width={200}
          className={styles.sider}
        >
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
          />
        </Sider>
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
