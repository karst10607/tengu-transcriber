const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  selectInputFolder: () => ipcRenderer.invoke('select-input-folder'),
  selectOutputFolder: () => ipcRenderer.invoke('select-output-folder'),
  processVideos: (data) => ipcRenderer.invoke('process-videos', data),
  stopProcessing: () => ipcRenderer.invoke('stop-processing'),
  verifyModel: (model) => ipcRenderer.invoke('verify-model', model),
  downloadModel: (model) => ipcRenderer.invoke('download-model', model),
  searchTranscripts: (data) => ipcRenderer.invoke('search-transcripts', data),
  onProcessingUpdate: (callback) => ipcRenderer.on('processing-update', (event, message) => callback(message)),
  onProcessingError: (callback) => ipcRenderer.on('processing-error', (event, error) => callback(error)),
  loadSettings: () => ipcRenderer.invoke('load-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings)
});
