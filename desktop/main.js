const { app, BrowserWindow, Menu, dialog, ipcMain, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const API_PORT = parseInt(process.env.AIVE_API_PORT || '9450', 10);
const DEV_UI_PORT = parseInt(process.env.AIVE_FRONTEND_PORT || '9451', 10);
const isDev = !app.isPackaged;

let backendProcess = null;
let mainWindow = null;

app.setName('Chakshu Forensics');
if (process.platform === 'win32') {
  app.setAppUserModelId('com.chakshu.forensics');
}

const singleInstanceLock = app.requestSingleInstanceLock();
if (!singleInstanceLock) {
  app.quit();
}

function getBackendPaths() {
  const backendDir = path.join(process.resourcesPath, 'backend');
  const backendExe =
    process.platform === 'win32'
      ? path.join(backendDir, 'aive-api.exe')
      : path.join(backendDir, 'aive-api');
  const frontendDist = path.join(backendDir, 'frontend-dist');
  return { backendDir, backendExe, frontendDist };
}

function getBackendCommand() {
  if (isDev) {
    return {
      cmd: process.platform === 'win32' ? 'python' : 'python3',
      args: ['-m', 'aive.api.server'],
      cwd: path.join(__dirname, '..'),
      env: { ...process.env, PYTHONPATH: path.join(__dirname, '..', 'src') },
    };
  }
  const fs = require('fs');
  const { backendDir, backendExe, frontendDist } = getBackendPaths();
  if (!fs.existsSync(backendExe)) {
    throw new Error(`Backend missing: ${backendExe}`);
  }
  // UI is bundled inside aive-api.exe - do not override with external paths
  const args = ['--host', '127.0.0.1', '--port', String(API_PORT)];
  return {
    cmd: backendExe,
    args,
    cwd: backendDir,
    env: process.env,
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
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1180,
    minHeight: 760,
    show: false,
    backgroundColor: '#06100f',
    title: 'Chakshu Forensics',
    icon: path.join(__dirname, 'build', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      nativeWindowOpen: true,
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) mainWindow.focus();
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    const allowed = isDev
      ? url.startsWith(`http://localhost:${DEV_UI_PORT}`)
      : url.startsWith(`http://127.0.0.1:${API_PORT}`);
    if (!allowed && /^https?:\/\//i.test(url)) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  if (isDev) {
    mainWindow.loadURL(`http://localhost:${DEV_UI_PORT}`);
    return;
  }

  const url = `http://127.0.0.1:${API_PORT}/`;
  mainWindow.loadURL(url);
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.webContents
      .executeJavaScript('document.body && document.body.innerText')
      .then((text) => {
        if (text && String(text).includes('"detail"') && String(text).includes('Not Found')) {
          dialog.showErrorBox(
            'Chakshu UI not loaded',
            'The app window could not load the interface.\n\n' +
              'Please download a fresh build from GitHub Actions (Chakshu-Native),\n' +
              'or rebuild with Build-Native.bat after the latest update.'
          );
        }
      })
      .catch(() => {});
  });
}

function createApplicationMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Evidence...',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            if (!mainWindow) return;
            const filePath = await openEvidenceFile();
            if (filePath) mainWindow.webContents.send('desktop-open-file', filePath);
          },
        },
        { type: 'separator' },
        { role: process.platform === 'darwin' ? 'close' : 'quit' },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'togglefullscreen' },
        ...(isDev ? [{ role: 'toggleDevTools' }] : []),
      ],
    },
    {
      label: 'Window',
      submenu: [{ role: 'minimize' }, { role: 'zoom' }, { role: 'front' }],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Chakshu Diagnostics',
          click: () => mainWindow?.loadURL(isDev ? `http://localhost:${DEV_UI_PORT}` : `http://127.0.0.1:${API_PORT}/`),
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.whenReady().then(async () => {
  try {
    createApplicationMenu();
    if (!isDev) {
      await startBackend();
    }
    createWindow();
  } catch (e) {
    console.error(e);
    app.quit();
  }
});

app.on('second-instance', () => {
  if (!mainWindow) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.focus();
});

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});

async function openEvidenceFile() {
  const { canceled, filePaths } = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      {
        name: 'Media',
        extensions: [
          'mp4', 'mov', 'avi', 'mkv', 'mxf', 'wmv', 'webm', 'ts', 'm4v', 'mpg', 'mpeg',
          'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp', 'gif', 'heic', 'heif',
          'dng', 'cr2', 'nef', 'arw', 'orf', 'rw2', 'raf', 'pef',
        ],
      },
    ],
  });
  if (canceled || !filePaths.length) return null;
  return filePaths[0];
}

ipcMain.handle('open-file', async () => {
  return openEvidenceFile();
});
