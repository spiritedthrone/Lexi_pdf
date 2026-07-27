import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes timeout for large PDF processing
});

// Automatic retry interceptor for transient network failures
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;

    // Handle 429 Too Many Requests / Quota Exceeded without retrying client-side indefinitely
    if (response && response.status === 429) {
      if (response.data && typeof response.data.detail === 'string') {
        error.message = response.data.detail;
      } else {
        error.message = 'Gemini API quota exceeded. Please wait until your quota resets or use a different API key.';
      }
      return Promise.reject(error);
    }

    // Retry only on network errors or 5xx server errors, up to 2 retries
    if (!config || config._retryCount >= 2) {
      if (error.code === 'ECONNABORTED') {
        error.message = 'Request timed out. The PDF may be large or API is busy.';
      }
      return Promise.reject(error);
    }

    if (!response || (response.status >= 500 && response.status <= 504)) {
      config._retryCount = (config._retryCount || 0) + 1;
      const backoffDelay = config._retryCount * 1500;
      await new Promise((resolve) => setTimeout(resolve, backoffDelay));
      return apiClient(config);
    }

    return Promise.reject(error);
  }
);

export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

export const uploadPdf = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/upload/', formData, {
    onUploadProgress: (progressEvent) => {

      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
};

export const simplifyPdf = async (fileId) => {
  const response = await apiClient.post(`/simplify/${fileId}`);
  return response.data;
};

export const downloadPdf = async (fileId, filename = 'simplified_document.pdf') => {
  const response = await apiClient.get(`/simplify/${fileId}/download`, {
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};
