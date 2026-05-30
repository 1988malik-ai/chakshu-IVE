const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const API_PORT = parseInt(process.env.AIVE_API_PORT || '9450', 10);
const DEV_UI_PORT = parseInt(process.env.AIVE_FRONTEND_PORT || '9451', 10);
const isDev = !app.isPackaged;

let backendProcess = null;

function getBackendCommand() {
  if (isDev) {
    return {
      cmd: process.platform === 'win32' ? 'python' : 'python3',
      args: ['-m', 'aive.api.server'],
      cwd: path.join(__dirname, '..'),
      env: { ...process.env, PYTHONPATH: path.join(__dirname, '..', 'src') },
    };
  }
  const backendExe =
    process.platform === 'win32'
      ? path.join(process.resourcesPath, 'backend', 'aive-api.exe')
      : path.join(process.resourcesPath, 'backend', 'aive-api');
  return { cmd: backendExe, args: [], cwd: path.dirname(backendExe), env: process.env };
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const { cmd, args, cwd, env } = getBackendCommand();
    const dist = isDev ? null : path.join(process.resourcesPath, 'frontend', 'dist');
    if (dist) {
      env.AIVE_FRONTEND_DIST = dist;
    }

    backendProcess = spawn(cmd, args, { cwd, env, stdio: 'inherit' });

    const check = () => {
      http
        .get(`http://127.0.0.1:${API_PORT}/api/health`, (res) => {
          if (res.statusCode === 200) resolve();
          else setTimeout(check, 300);
        })
        .on('error', () => setTimeout(check, 300));
    };
    setTimeout(check, 500);
    setTimeout(() => reject(new Error('Backend startup timeout')), 30000);
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
    },
  });

  if (isDev) {
    win.loadURL(`http://localhost:${DEV_UI_PORT}`);
  } else {
    win.loadURL(`http://127.0.0.1:${API_PORT}`);
  }
}

app.whenReady().then(async () => {
  try {
    if (!isDev) {
      await startBackend();
    }
    createWindow();
  } catch (e) {
    console.error(e);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('open-file', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: 'Media', extensions: ['mp4', 'mov', 'avi', 'mkv', 'jpg', 'jpeg', 'png', 'tiff', 'bmp'] },
    ],
  });
  if (canceled || !filePaths.length) return null;
  return filePaths[0];
});
