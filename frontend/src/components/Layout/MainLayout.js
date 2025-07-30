import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  VideoCameraOutlined,
  AppstoreOutlined,
  UploadOutlined,
} from '@ant-design/icons';

const { Header, Sider } = Layout;

const MainLayout = ({ children }) => {
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/dashboard">대시보드</Link>,
    },
    {
      key: '/videos',
      icon: <VideoCameraOutlined />,
      label: <Link to="/videos">영상 관리</Link>,
    },
    {
      key: '/videos/upload',
      icon: <UploadOutlined />,
      label: <Link to="/videos/upload">영상 업로드</Link>,
    },
    {
      key: '/hands',
      icon: <AppstoreOutlined />,
      label: <Link to="/hands">핸드 라이브러리</Link>,
    },
  ];

  return (
    <Layout>
      <Header style={{ display: 'flex', alignItems: 'center', background: '#001529' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          Poker MAM
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <Layout style={{ padding: '0' }}>
          {children}
        </Layout>
      </Layout>
    </Layout>
  );
};

export default MainLayout;