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
  const backendDir = path.join(process.resourcesPath, 'backend');
  const backendExe =
    process.platform === 'win32'
      ? path.join(backendDir, 'aive-api.exe')
      : path.join(backendDir, 'aive-api');
  const frontendDist = path.join(backendDir, 'frontend-dist');
  const args = ['--host', '127.0.0.1', '--port', String(API_PORT)];
  if (require('fs').existsSync(frontendDist)) {
    args.push('--frontend-dist', frontendDist);
  }
  return {
    cmd: backendExe,
    args,
    cwd: backendDir,
    env: { ...process.env, AIVE_FRONTEND_DIST: frontendDist },
  };
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const { cmd, args, cwd, env } = getBackendCommand();

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
