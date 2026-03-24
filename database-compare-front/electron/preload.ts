import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  minimizeWindow: () => ipcRenderer.invoke('window:minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window:maximize'),
  closeWindow: () => ipcRenderer.invoke('window:close'),
  isMaximized: () => ipcRenderer.invoke('window:isMaximized'),
  
  onMaximizeChange: (callback: (isMaximized: boolean) => void) => {
    ipcRenderer.on('window:maximize-change', (_, isMaximized) => callback(isMaximized));
  },
  
  saveFile: (options: { defaultPath: string; content: string }) => 
    ipcRenderer.invoke('file:save', options),
  
  getPlatform: () => process.platform,
});
