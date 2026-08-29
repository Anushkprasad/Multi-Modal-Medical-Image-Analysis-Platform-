import api from './api';

export const uploadXray = async (file, clinicalNotes, onProgress) => {
  const formData = new FormData();
  formData.append('image', file);
  if (clinicalNotes) {
    formData.append('clinical_notes', clinicalNotes);
  }

  const response = await api.post('/api/v1/predict', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
  });

  return response.data;
};
