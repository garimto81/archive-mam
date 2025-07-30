import React, { useState } from 'react';
import { Upload, Button, message, Card, Progress, Alert } from 'antd';
import { InboxOutlined, UploadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { videoAPI } from '../services/api';

const { Dragger } = Upload;

const VideoUpload = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const navigate = useNavigate();

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: 'video/*',
    beforeUpload: (file) => {
      const isVideo = file.type.startsWith('video/');
      if (!isVideo) {
        message.error('비디오 파일만 업로드할 수 있습니다!');
        return false;
      }
      
      const isLt2G = file.size / 1024 / 1024 / 1024 < 2;
      if (!isLt2G) {
        message.error('파일 크기는 2GB 이하여야 합니다!');
        return false;
      }
      
      handleUpload(file);
      return false;
    },
  };

  const handleUpload = async (file) => {
    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await videoAPI.uploadVideo(file);
      
      message.success('영상 업로드가 완료되었습니다. 분석을 시작합니다.');
      
      // 잠시 후 영상 목록 페이지로 이동
      setTimeout(() => {
        navigate('/videos');
      }, 2000);
      
    } catch (error) {
      console.error('Upload error:', error);
      message.error('영상 업로드에 실패했습니다.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">영상 업로드</h1>
      </div>
      
      <Alert
        message="영상 업로드 안내"
        description="포커 영상을 업로드하면 자동으로 핸드를 감지하고 팟 사이즈, 참여 플레이어를 분석합니다. 분석에는 영상 길이에 따라 수 분에서 수십 분이 소요될 수 있습니다."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />
      
      <Card>
        <Dragger {...uploadProps} disabled={uploading}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            클릭하거나 파일을 드래그하여 업로드하세요
          </p>
          <p className="ant-upload-hint">
            MP4, AVI, MOV 등 일반적인 비디오 형식을 지원합니다
          </p>
        </Dragger>
        
        {uploading && (
          <div style={{ marginTop: 24 }}>
            <Progress percent={uploadProgress} />
            <p style={{ textAlign: 'center', marginTop: 8 }}>
              업로드 중... 잠시만 기다려주세요.
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default VideoUpload;