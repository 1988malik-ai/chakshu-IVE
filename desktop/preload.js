const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('aiveDesktop', {
  isElectron: true,
  openFile: () => ipcRenderer.invoke('open-file'),
  onOpenFile: (callback) => {
    if (typeof callback !== 'function') return () => {};
    const listener = (_event, filePath) => callback(filePath);
    ipcRenderer.on('desktop-open-file', listener);
    return () => ipcRenderer.removeListener('desktop-open-file', listener);
  },
});
