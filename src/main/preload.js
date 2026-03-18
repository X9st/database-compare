const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API 给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // 测试 Python 后端连接
  testPythonConnection: () => ipcRenderer.invoke('test-python-connection'),
  
  // 数据库连接相关 API
  testDatabaseConnection: (config) => ipcRenderer.invoke('test-database-connection', config),
  getDatabaseTables: (config) => ipcRenderer.invoke('get-database-tables', config),
  
  // 比对任务相关 API
  startComparison: (taskConfig) => ipcRenderer.invoke('start-comparison', taskConfig),
  getComparisonProgress: (taskId) => ipcRenderer.invoke('get-comparison-progress', taskId),
  getComparisonResult: (taskId) => ipcRenderer.invoke('get-comparison-result', taskId),
  
  // 连接管理 API
  saveConnection: (connection) => ipcRenderer.invoke('save-connection', connection),
  getConnections: () => ipcRenderer.invoke('get-connections'),
  deleteConnection: (id) => ipcRenderer.invoke('delete-connection', id),
  getConnectionFull: (id) => ipcRenderer.invoke('get-connection-full', id),
  
  // 报告导出 API
  exportReport: (taskId, format) => ipcRenderer.invoke('export-report', taskId, format),
  
  // 监听事件
  onComparisonProgress: (callback) => {
    ipcRenderer.on('comparison-progress', (event, data) => callback(data));
  },
  
  // 移除监听
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});
