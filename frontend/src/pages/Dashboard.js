import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Spin, message } from 'antd';
import { VideoCameraOutlined, AppstoreOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { statsAPI } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await statsAPI.getStats();
      setStats(response.data);
    } catch (error) {
      message.error('통계를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">대시보드</h1>
      </div>
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="전체 영상"
              value={stats?.total_videos || 0}
              prefix={<VideoCameraOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="전체 핸드"
              value={stats?.total_hands || 0}
              prefix={<AppstoreOutlined />}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="평균 핸드/영상"
              value={stats?.average_hands_per_video || 0}
              precision={1}
            />
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="처리 중"
              value={stats?.videos_by_status?.processing || 0}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
      
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        <Col span={24}>
          <Card title="영상 처리 상태">
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="대기 중"
                  value={stats?.videos_by_status?.pending || 0}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="처리 중"
                  value={stats?.videos_by_status?.processing || 0}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="완료"
                  value={stats?.videos_by_status?.completed || 0}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="실패"
                  value={stats?.videos_by_status?.failed || 0}
                  valueStyle={{ color: '#f5222d' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;