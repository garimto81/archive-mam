import React, { useState, useEffect } from 'react';
import { Card, Row, Col, InputNumber, Input, Button, Space, Spin, message, Tag, Empty } from 'antd';
import { SearchOutlined, DollarOutlined, UserOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { handAPI } from '../services/api';

const HandLibrary = () => {
  const [hands, setHands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    min_pot_size: null,
    max_pot_size: null,
    player_name: '',
    video_filename: '',
  });
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const videoId = searchParams.get('video_id');
    if (videoId) {
      fetchHandsByVideo(videoId);
    } else {
      fetchHands();
    }
  }, [searchParams]);

  const fetchHands = async () => {
    setLoading(true);
    try {
      const response = await handAPI.getHands({ limit: 100 });
      setHands(response.data);
    } catch (error) {
      message.error('핸드 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchHandsByVideo = async (videoId) => {
    setLoading(true);
    try {
      const response = await handAPI.getHands({ video_id: videoId, limit: 100 });
      setHands(response.data);
    } catch (error) {
      message.error('핸드 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const searchFilters = {
        ...filters,
        min_pot_size: filters.min_pot_size || undefined,
        max_pot_size: filters.max_pot_size || undefined,
        player_name: filters.player_name || undefined,
        video_filename: filters.video_filename || undefined,
      };
      
      const response = await handAPI.searchHands(searchFilters);
      setHands(response.data);
      message.success(`${response.data.length}개의 핸드를 찾았습니다.`);
    } catch (error) {
      message.error('검색에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFilters({
      min_pot_size: null,
      max_pot_size: null,
      player_name: '',
      video_filename: '',
    });
    fetchHands();
  };

  const getMaxPotSize = (potHistory) => {
    if (!potHistory || potHistory.length === 0) return 0;
    return Math.max(...potHistory.map(p => p.pot || 0));
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
        <h1 className="page-title">핸드 라이브러리</h1>
      </div>

      {/* 검색 필터 */}
      <Card className="filter-container" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span>최소 팟 사이즈</span>
              <InputNumber
                style={{ width: '100%' }}
                placeholder="최소값"
                prefix={<DollarOutlined />}
                value={filters.min_pot_size}
                onChange={(value) => setFilters({ ...filters, min_pot_size: value })}
              />
            </Space>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span>최대 팟 사이즈</span>
              <InputNumber
                style={{ width: '100%' }}
                placeholder="최대값"
                prefix={<DollarOutlined />}
                value={filters.max_pot_size}
                onChange={(value) => setFilters({ ...filters, max_pot_size: value })}
              />
            </Space>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span>플레이어 이름</span>
              <Input
                placeholder="플레이어 검색"
                prefix={<UserOutlined />}
                value={filters.player_name}
                onChange={(e) => setFilters({ ...filters, player_name: e.target.value })}
              />
            </Space>
          </Col>
          
          <Col xs={24} sm={12} md={6}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <span>&nbsp;</span>
              <Space>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>
                  검색
                </Button>
                <Button onClick={handleReset}>초기화</Button>
              </Space>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 핸드 그리드 */}
      {hands.length === 0 ? (
        <Empty description="검색 결과가 없습니다" />
      ) : (
        <Row gutter={[16, 16]}>
          {hands.map((hand) => {
            const maxPot = getMaxPotSize(hand.pot_size_history);
            const duration = hand.end_time_s ? hand.end_time_s - hand.start_time_s : 0;
            
            return (
              <Col key={hand.id} xs={24} sm={12} md={8} lg={6}>
                <Card
                  hoverable
                  onClick={() => navigate(`/hands/${hand.id}`)}
                  cover={
                    <div style={{ 
                      height: 150, 
                      background: '#f0f0f0', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      fontSize: 48,
                      color: '#999'
                    }}>
                      🃏
                    </div>
                  }
                >
                  <Card.Meta
                    title={`Hand #${hand.id}`}
                    description={
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                          <DollarOutlined /> 팟: {maxPot.toLocaleString()}
                        </div>
                        <div>
                          <ClockCircleOutlined /> {formatTime(hand.start_time_s)} - {formatTime(hand.end_time_s || hand.start_time_s)}
                        </div>
                        <div>
                          <UserOutlined /> {hand.participating_players.length}명 참여
                        </div>
                        <div style={{ marginTop: 8 }}>
                          {hand.participating_players.slice(0, 2).map((player, idx) => (
                            <Tag key={idx} size="small">{player}</Tag>
                          ))}
                          {hand.participating_players.length > 2 && (
                            <Tag size="small">+{hand.participating_players.length - 2}</Tag>
                          )}
                        </div>
                      </Space>
                    }
                  />
                </Card>
              </Col>
            );
          })}
        </Row>
      )}
    </div>
  );
};

export default HandLibrary;