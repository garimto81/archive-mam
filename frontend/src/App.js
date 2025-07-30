import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Layout } from 'antd';
import MainLayout from './components/Layout/MainLayout';
import Dashboard from './pages/Dashboard';
import VideoList from './pages/VideoList';
import VideoUpload from './pages/VideoUpload';
import HandLibrary from './pages/HandLibrary';
import HandDetail from './pages/HandDetail';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <Router>
        <MainLayout>
          <Content style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/videos" element={<VideoList />} />
              <Route path="/videos/upload" element={<VideoUpload />} />
              <Route path="/hands" element={<HandLibrary />} />
              <Route path="/hands/:handId" element={<HandDetail />} />
            </Routes>
          </Content>
        </MainLayout>
      </Router>
    </ConfigProvider>
  );
}

export default App;