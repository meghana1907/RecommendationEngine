import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 300000, // 5 minutes timeout for long-running processes
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Request interceptor for debugging
    this.api.interceptors.request.use(
      (config) => {
        console.log('🚀 API Request:', {
          method: config.method?.toUpperCase(),
          url: config.url,
          data: config.data ? 'Data attached' : 'No data',
          timestamp: new Date().toISOString()
        });
        return config;
      },
      (error) => {
        console.error('❌ API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for debugging
    this.api.interceptors.response.use(
      (response) => {
        console.log('✅ API Response:', {
          status: response.status,
          url: response.config.url,
          dataSize: response.data ? Object.keys(response.data).length : 0,
          timestamp: new Date().toISOString()
        });
        return response;
      },
      (error) => {
        console.error('❌ API Response Error:', {
          status: error.response?.status,
          message: error.response?.data?.message || error.message,
          url: error.config?.url,
          timestamp: new Date().toISOString()
        });
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials) {
    const response = await this.api.post('/auth/login', credentials);
    return response.data;
  }

  async register(userData) {
    const response = await this.api.post('/auth/register', userData);
    return response.data;
  }

  async validateToken(token) {
    try {
      const response = await this.api.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    } catch (error) {
      return null;
    }
  }

  // Jira Integration
  async testJiraConnection(credentials) {
    const response = await this.api.post('/jira/test-connection', credentials);
    return response.data;
  }

  async getJiraProjects(credentials) {
    const response = await this.api.post('/jira/projects', credentials);
    return response.data;
  }

  async importFromJira(importRequest) {
    const response = await this.api.post('/jira/import', importRequest);
    return response.data;
  }

  async getJiraIssues(credentials, projectKey, issueType = null) {
    const response = await this.api.post('/jira/issues', {
      ...credentials,
      project_key: projectKey,
      issue_type: issueType
    });
    return response.data;
  }

  // Document operations with new clustering pipeline
  async uploadFile(file, onProgress = null) {
    console.log('📤 Uploading file:', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    };

    if (onProgress) {
      config.onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      };
    }

    const response = await this.api.post('/documents/upload', formData, config);
    console.log('✅ File uploaded successfully:', response.data);
    return response.data;
  }

  async uploadText(textContent) {
    console.log('📝 Uploading text content');
    
    const response = await this.api.post('/documents/upload-text', {
      content: textContent
    });
    console.log('✅ Text content uploaded successfully:', response.data);
    return response.data;
  }

  async generateTests(brdDocumentId, userStoriesDocumentId) {
    console.log('🧪 Generating test recommendations from both documents:', {
      brdDocumentId,
      userStoriesDocumentId
    });
    
    const response = await this.api.post('/tests/generate', {
      brd_document_id: brdDocumentId,
      user_stories_document_id: userStoriesDocumentId
    });
    console.log('🎉 Test generation completed:', response.data);
    return response.data;
  }

  async generateIntelligentTests(brdDocumentId, userStoriesDocumentId) {
    console.log('🧠 Generating INTELLIGENT test recommendations using domain-aware + universal analysis:', {
      brdDocumentId,
      userStoriesDocumentId
    });
    
    const response = await this.api.post('/tests/generate-intelligent', {
      brd_document_id: brdDocumentId,
      user_stories_document_id: userStoriesDocumentId
    });
    console.log('🎉 Intelligent test generation completed:', response.data);
    return response.data;
  }

  async processDocument(documentId, userStoriesId = null) {
    console.log('🔄 Processing document through clustering pipeline:', documentId);
    
    const params = userStoriesId ? { user_stories_id: userStoriesId } : {};
    const response = await this.api.post(`/documents/process/${documentId}`, {}, { params });
    console.log('🎉 Document processing completed:', response.data);
    return response.data;
  }

  async uploadAndProcess(file, userStoriesId = null, onProgress = null) {
    console.log('🚀 Starting upload and process pipeline for:', file.name);
    
    try {
      // Step 1: Upload file
      if (onProgress) onProgress(10, 'Uploading file...');
      const uploadResult = await this.uploadFile(file, (progress) => {
        if (onProgress) onProgress(progress * 0.2, 'Uploading file...');
      });

      const documentId = uploadResult.document_id;
      console.log('📁 File uploaded, document ID:', documentId);

      // Step 2: Process through pipeline
      if (onProgress) onProgress(25, 'Starting AI processing...');
      
      const processResult = await this.processDocument(documentId, userStoriesId);
      
      if (onProgress) onProgress(100, 'Processing completed!');
      
      return {
        ...processResult,
        document_id: documentId,
        filename: uploadResult.filename
      };
      
    } catch (error) {
      console.error('❌ Upload and process pipeline failed:', error);
      if (onProgress) onProgress(-1, `Processing failed: ${error.message}`);
      throw error;
    }
  }

  async listDocuments() {
    const response = await this.api.get('/documents/');
    return response.data;
  }

  async getDocumentResults(documentId) {
    const response = await this.api.get(`/documents/${documentId}/results`);
    return response.data;
  }

  // User Stories operations
  async uploadUserStories(file) {
    console.log('📋 Uploading user stories file:', file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    };

    const response = await this.api.post('/user-stories/upload', formData, config);
    console.log('✅ User stories uploaded successfully:', response.data);
    return response.data;
  }

  async listUserStories() {
    const response = await this.api.get('/user-stories');
    return response.data;
  }

  async getUserStories(userStoriesId) {
    const response = await this.api.get(`/user-stories/${userStoriesId}`);
    return response.data;
  }

  async getProcessingLog(documentId) {
    const response = await this.api.get(`/debug/processing-log/${documentId}`);
    return response.data;
  }

  // Test recommendation operations
  async getTestRecommendations(documentId) {
    const response = await this.api.get(`/tests/recommendations/${documentId}`);
    return response.data;
  }

  async regenerateClusterTests(documentId, clusterId) {
    const response = await this.api.post(`/tests/regenerate/${documentId}/${clusterId}`);
    return response.data;
  }

  async getAggregatedTests(documentId) {
    const response = await this.api.get(`/tests/aggregated/${documentId}`);
    return response.data;
  }

  async getTestsByCategory(documentId) {
    const response = await this.api.get(`/tests/by-category/${documentId}`);
    return response.data;
  }

  async exportTests(documentId, format = 'json') {
    const response = await this.api.get(`/tests/export/${documentId}/${format}`, {
      responseType: 'blob'
    });
    return response;
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('Backend service is not available');
    }
  }

  // Polling helper for document processing status
  async pollDocumentStatus(documentId, onUpdate = null, maxAttempts = 60) {
    let attempts = 0;
    const pollInterval = 2000; // 2 seconds

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          attempts++;
          const status = await this.getDocumentStatus(documentId);
          
          if (onUpdate) {
            onUpdate(status);
          }

          if (status.status === 'completed') {
            resolve(status);
          } else if (status.status === 'failed') {
            reject(new Error('Document processing failed'));
          } else if (attempts >= maxAttempts) {
            reject(new Error('Processing timeout - maximum attempts reached'));
          } else {
            setTimeout(poll, pollInterval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }

  // Batch operations
  async batchDeleteDocuments(documentIds) {
    const deletePromises = documentIds.map(id => this.deleteDocument(id));
    return Promise.allSettled(deletePromises);
  }

  // Export helper
  async downloadExportFile(documentId, format, filename) {
    try {
      const response = await this.exportTests(documentId, format);
      
      // Create blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Export download failed:', error);
      throw error;
    }
  }
}

export default new ApiService();