const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
let pythonProcess = null;
let tray = null;

const PORT = process.env.PORT || 5000;
const PYTHON = process.env.PYTHON || 'python';
const BACKEND_URL = `http://127.0.0.1:${PORT}`;
const PROJECT_ROOT = path.join(__dirname, '..');

// Python backend process
function startPythonBackend() {
    pythonProcess = spawn(PYTHON, ['api_server.py'], {
        cwd: PROJECT_ROOT,
        env: { ...process.env, PORT: PORT }
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });
}

async function waitForBackend(timeoutMs = 15000) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        try {
            const res = await fetch(`${BACKEND_URL}/api/v1/health`);
            if (res.ok) return true;
        } catch (e) {
            // Not listening yet
        }
        await new Promise(resolve => setTimeout(resolve, 300));
    }
    return false;
}

async function postApi(endpoint, body) {
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!response.ok) {
        throw new Error(`Backend returned ${response.status} for ${endpoint}`);
    }
    return response.json();
}

function startScan() {
    return postApi('/api/v1/scan/start', { drive: 'C:' });
}

function runCleanup(type = 'smart') {
    return postApi('/api/v1/cleanup/run', { type });
}

function logActionFailure(error) {
    console.error('EatUp action failed:', error);
}

async function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            // The UI loads third-party CDN scripts, so it must not get Node access
            nodeIntegration: false,
            contextIsolation: true
        },
        icon: path.join(__dirname, 'assets', 'icon.png'),
        show: false,
        backgroundColor: '#fbfbfd'
    });

    // Serve the UI from the backend so its relative /api/v1 calls resolve
    if (await waitForBackend()) {
        mainWindow.loadURL(`${BACKEND_URL}/app.html`);
    } else {
        mainWindow.loadFile(path.join(PROJECT_ROOT, 'app.html'));  // Demo mode
    }

    // Show when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // System tray integration
    setupTray(mainWindow);

    // Create menu
    const template = [
        {
            label: 'App',
            submenu: [
                { role: 'quit' }
            ]
        },
        { role: 'editMenu' },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { role: 'resetZoom' }
            ]
        },
        {
            label: 'Features',
            submenu: [
                {
                    label: 'Scan Drive',
                    accelerator: 'CmdOrCtrl+S',
                    click: () => startScan().catch(logActionFailure)
                },
                {
                    label: 'Smart Cleanup',
                    click: () => runCleanup('smart').catch(logActionFailure)
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

function setupTray(parentWindow) {
    const { Tray } = require('electron');
    const iconPath = path.join(__dirname, 'assets', 'icon.ico');
    if (!fs.existsSync(iconPath)) return;

    tray = new Tray(iconPath);  // Module-level so it isn't garbage collected

    tray.setToolTip('EatUp Pro - Disk Cleanup Tool');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Quick Scan',
            click: () => startScan().catch(logActionFailure)
        },
        {
            label: 'Smart Cleanup',
            click: () => runCleanup('smart').catch(logActionFailure)
        },
        { type: 'separator' },
        {
            label: 'Open App',
            click: () => parentWindow.show()
        },
        {
            label: 'Quit',
            click: () => app.quit()
        }
    ]);

    tray.setContextMenu(contextMenu);
}

app.whenReady().then(() => {
    startPythonBackend();

    // Expose Python API to JavaScript
    ipcMain.handle('start-scan', () => startScan());

    ipcMain.handle('run-cleanup', (event, { type }) => runCleanup(type));

    ipcMain.handle('get-usage-stats', async () => {
        return fetch(`${BACKEND_URL}/api/v1/usage/stats`)
            .then(res => res.json());
    });

    ipcMain.handle('health-check', async () => {
        return fetch(`${BACKEND_URL}/api/v1/health`)
            .then(res => res.json());
    });

    createWindow();
});

app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
