import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Video APIs
export const videoAPI = {
  uploadVideo: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/videos/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  getVideos: (params) => api.get('/videos/', { params }),
  
  getVideo: (videoId) => api.get(`/videos/${videoId}`),
  
  getVideoStatus: (videoId) => api.get(`/videos/${videoId}/status`),
};

// Hand APIs
export const handAPI = {
  getHands: (params) => api.get('/hands/', { params }),
  
  getHand: (handId) => api.get(`/hands/${handId}`),
  
  searchHands: (filters) => api.post('/hands/search', filters),
};

// Clip APIs
export const clipAPI = {
  generateClip: (handId, format = 'mp4') => 
    api.post('/clips/generate', { hand_id: handId, format }),
  
  getClipStatus: (taskId) => api.get(`/clips/status/${taskId}`),
  
  downloadClip: (filename) => `${API_BASE_URL}/clips/${filename}`,
};

// Statistics API
export const statsAPI = {
  getStats: () => api.get('/stats'),
};

export default api;