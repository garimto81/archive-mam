import React, { useState, useEffect } from 'react';
import { Table, Tag, Button, Space, message, Progress, Tooltip } from 'antd';
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { videoAPI } from '../services/api';

const VideoList = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchVideos();
    // 5초마다 자동 새로고침 (처리 중인 영상이 있을 수 있으므로)
    const interval = setInterval(fetchVideos, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await videoAPI.getVideos({});
      setVideos(response.data);
    } catch (error) {
      message.error('영상 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status) => {
    const statusConfig = {
      pending: { color: 'orange', text: '대기 중' },
      processing: { color: 'blue', text: '처리 중' },
      completed: { color: 'green', text: '완료' },
      failed: { color: 'red', text: '실패' },
    };

    const config = statusConfig[status] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '파일명',
      dataIndex: 'filename',
      key: 'filename',
      ellipsis: true,
    },
    {
      title: '업로드 일시',
      dataIndex: 'upload_date',
      key: 'upload_date',
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
      width: 180,
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status),
      width: 100,
    },
    {
      title: '진행률',
      key: 'progress',
      width: 200,
      render: (_, record) => {
        if (record.status === 'processing') {
          // 실제로는 task_info에서 진행률을 가져와야 함
          return <Progress percent={50} size="small" />;
        } else if (record.status === 'completed') {
          return <Progress percent={100} size="small" status="success" />;
        } else if (record.status === 'failed') {
          return <Progress percent={0} size="small" status="exception" />;
        }
        return <Progress percent={0} size="small" />;
      },
    },
    {
      title: '액션',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space size="middle">
          <Tooltip title="핸드 보기">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/hands?video_id=${record.id}`)}
              disabled={record.status !== 'completed'}
            >
              핸드 보기
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 className="page-title">영상 관리</h1>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchVideos}
          >
            새로고침
          </Button>
          <Button 
            type="primary" 
            onClick={() => navigate('/videos/upload')}
          >
            영상 업로드
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={videos}
        rowKey="id"
        loading={loading}
        pagination={{
          defaultPageSize: 10,
          showSizeChanger: true,
          showTotal: (total) => `총 ${total}개`,
        }}
      />
    </div>
  );
};

export default VideoList;