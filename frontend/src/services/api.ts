// src/services/api.ts
import axios from 'axios';
import { ReviewRequest, ReviewResponse, BatchResponse, ModelInfo } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds timeout
});

// Request interceptor - log outgoing requests
api.interceptors.request.use(
  (config) => {
    console.log('[API] Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors and log responses
api.interceptors.response.use(
  (response) => {
    console.log('[API] Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('[API] Request timeout:', error.message);
    } else if (error.response) {
      console.error('[API] Error Response:', {
        status: error.response.status,
        data: error.response.data,
      });
      
      const errorMessage = error.response.data?.detail || 
                          error.response.data?.message || 
                          error.message;
      error.message = errorMessage;
    } else if (error.request) {
      console.error('[API] No response from server:', error.request);
      error.message = 'Cannot connect to server. Please check if the backend is running.';
    } else {
      console.error('[API] Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

export const absaApi = {
  // Health check
  health: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('[API] Health check failed:', error);
      throw error;
    }
  },

  // Model info
  getModelInfo: async (): Promise<ModelInfo> => {
    try {
      const response = await api.get('/model/info');
      return response.data;
    } catch (error) {
      console.error('[API] Failed to get model info:', error);
      throw error;
    }
  },

  // Predict single review
  predict: async (request: ReviewRequest): Promise<ReviewResponse> => {
    try {
      console.log('[API] Sending prediction request:', request);
      const response = await api.post('/predict', request);
      console.log('[API] Prediction response received');
      return response.data;
    } catch (error) {
      console.error('[API] Prediction failed:', error);
      throw error;
    }
  },

  // Predict batch
  predictBatch: async (reviews: ReviewRequest[], threshold?: number): Promise<BatchResponse> => {
    try {
      const response = await api.post('/predict/batch', {
        reviews,
        threshold
      });
      return response.data;
    } catch (error) {
      console.error('[API] Batch prediction failed:', error);
      throw error;
    }
  },

  // Upload file
  uploadFile: async (file: File, threshold: number = 0.6): Promise<any> => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('threshold', threshold.toString());
      
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('[API] File upload failed:', error);
      throw error;
    }
  },

  // Translate
  translate: async (text: string): Promise<{ original: string; translated: string }> => {
    try {
      const response = await api.post('/translate', { text });
      return response.data;
    } catch (error) {
      console.error('[API] Translation failed:', error);
      throw error;
    }
  },

  // Load model
  loadModel: async (modelPath: string): Promise<any> => {
    try {
      const response = await api.post('/load_model', null, {
        params: { model_path: modelPath }
      });
      return response.data;
    } catch (error) {
      console.error('[API] Model loading failed:', error);
      throw error;
    }
  }
};

export default absaApi;