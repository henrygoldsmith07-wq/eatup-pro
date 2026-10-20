const { app, BrowserWindow, ipcMain, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
let pythonProcess = null;

// Python backend process
function startPythonBackend() {
    const port = process.env.PORT || 5000;
    pythonProcess = spawn('python', ['api_server.py'], {
        cwd: __dirname,
        env: { ...process.env, PORT: port }
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python Error: ${data}`);
    });
}

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        icon: path.join(__dirname, 'assets', 'icon.png'),
        show: false,
        backgroundColor: '#fbfbfd'
    });

    // Load the web app
    mainWindow.loadFile('../index.html');

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
                    click: () => mainWindow.webContents.send('scan-start')
                },
                {
                    label: 'Smart Cleanup',
                    accelerator: 'CmdOrCtrl+C',
                    click: () => mainWindow.webContents.send('cleanup-run', { type: 'smart' })
                },
                {
                    label: 'Scheduled Tasks',
                    click: () => {
                        const scheduleWindow = new BrowserWindow({
                            width: 600,
                            height: 500,
                            parent: mainWindow
                        });
                        scheduleWindow.loadFile('../scheduler.html');
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

function setupTray(parentWindow) {
    const tray = require('electron'). Tray;
    const iconPath = path.join(__dirname, 'assets', 'icon.ico');

    const trayIcon = new tray(iconPath);
    
    tray.setToolTip('EatUp Pro - Disk Cleanup Tool');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Quick Scan',
            click: () => parentWindow.webContents.send('scan-start')
        },
        {
            label: 'Smart Cleanup',
            click: () => parentWindow.webContents.send('cleanup-run', { type: 'smart' })
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
    ipcMain.handle('start-scan', async () => {
        return fetch('http://localhost:5000/api/v1/scan/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ drive: 'C:' })
        }).then(res => res.json());
    });

    ipcMain.handle('run-cleanup', async (event, { type }) => {
        return fetch('http://localhost:5000/api/v1/cleanup/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type })
        }).then(res => res.json());
    });

    ipcMain.handle('get-usage-stats', async () => {
        return fetch('http://localhost:5000/api/v1/usage/stats')
            .then(res => res.json());
    });

    ipcMain.handle('health-check', async () => {
        return fetch('http://localhost:5000/api/v1/health')
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
