import React, { useState, useEffect } from 'react';
import { Card, Button, Descriptions, Tag, Space, Spin, message, Modal, Progress, Row, Col } from 'antd';
import { DownloadOutlined, PlayCircleOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import ReactPlayer from 'react-player';
import { handAPI, clipAPI } from '../services/api';

const HandDetail = () => {
  const { handId } = useParams();
  const navigate = useNavigate();
  const [hand, setHand] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clipGenerating, setClipGenerating] = useState(false);
  const [clipTaskId, setClipTaskId] = useState(null);
  const [clipProgress, setClipProgress] = useState(0);

  useEffect(() => {
    fetchHandDetail();
  }, [handId]);

  useEffect(() => {
    if (clipTaskId) {
      const interval = setInterval(checkClipStatus, 1000);
      return () => clearInterval(interval);
    }
  }, [clipTaskId]);

  const fetchHandDetail = async () => {
    try {
      const response = await handAPI.getHand(handId);
      setHand(response.data);
    } catch (error) {
      message.error('핸드 정보를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateClip = async () => {
    setClipGenerating(true);
    setClipProgress(0);
    
    try {
      const response = await clipAPI.generateClip(handId);
      setClipTaskId(response.data.task_id);
      message.info('클립 생성을 시작했습니다...');
    } catch (error) {
      message.error('클립 생성에 실패했습니다.');
      setClipGenerating(false);
    }
  };

  const checkClipStatus = async () => {
    if (!clipTaskId) return;
    
    try {
      const response = await clipAPI.getClipStatus(clipTaskId);
      const { state, info } = response.data;
      
      if (state === 'SUCCESS') {
        setClipGenerating(false);
        setClipProgress(100);
        message.success('클립 생성이 완료되었습니다!');
        
        // 다운로드 시작
        const clipUrl = clipAPI.downloadClip(info.output_path.split('/').pop());
        window.open(clipUrl, '_blank');
        
        setClipTaskId(null);
      } else if (state === 'FAILURE') {
        setClipGenerating(false);
        message.error('클립 생성에 실패했습니다.');
        setClipTaskId(null);
      } else if (state === 'PROGRESS') {
        setClipProgress(info?.current || 50);
      }
    } catch (error) {
      console.error('Error checking clip status:', error);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getMaxPotSize = (potHistory) => {
    if (!potHistory || potHistory.length === 0) return 0;
    return Math.max(...potHistory.map(p => p.pot || 0));
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!hand) {
    return <div>핸드를 찾을 수 없습니다.</div>;
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <Space>
          <Button 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate(-1)}
          >
            뒤로
          </Button>
          <h1 className="page-title" style={{ margin: 0 }}>Hand #{hand.id} 상세정보</h1>
        </Space>
      </div>

      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card title="핸드 정보">
            <Descriptions bordered column={{ xs: 1, sm: 2 }}>
              <Descriptions.Item label="영상 파일">
                {hand.video_filename}
              </Descriptions.Item>
              <Descriptions.Item label="시작 시간">
                {formatTime(hand.start_time_s)}
              </Descriptions.Item>
              <Descriptions.Item label="종료 시간">
                {formatTime(hand.end_time_s || hand.start_time_s)}
              </Descriptions.Item>
              <Descriptions.Item label="최대 팟 사이즈">
                {getMaxPotSize(hand.pot_size_history).toLocaleString()}
              </Descriptions.Item>
              <Descriptions.Item label="참여 플레이어" span={2}>
                <Space wrap>
                  {hand.participating_players.map((player, idx) => (
                    <Tag key={idx} color="blue">{player}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="분석 일시" span={2}>
                {new Date(hand.analysis_date).toLocaleString()}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col span={24}>
          <Card 
            title="팟 사이즈 변화"
            extra={
              <Button
                type="primary"
                icon={<DownloadOutlined />}
                onClick={handleGenerateClip}
                loading={clipGenerating}
                disabled={clipGenerating}
              >
                클립 다운로드
              </Button>
            }
          >
            {clipGenerating && (
              <div style={{ marginBottom: 16 }}>
                <Progress percent={clipProgress} status="active" />
                <p style={{ textAlign: 'center', marginTop: 8 }}>
                  클립을 생성하고 있습니다...
                </p>
              </div>
            )}
            
            <div style={{ maxHeight: 300, overflowY: 'auto' }}>
              {hand.pot_size_history.map((pot, idx) => (
                <div key={idx} style={{ padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                  <Space>
                    <span>시간: {formatTime(pot.time_s)}</span>
                    <span>|</span>
                    <span>팟: {pot.pot.toLocaleString()}</span>
                  </Space>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default HandDetail;