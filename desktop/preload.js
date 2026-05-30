const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aiveDesktop', {
  isElectron: true,
  openFile: () => ipcRenderer.invoke('open-file'),
});
