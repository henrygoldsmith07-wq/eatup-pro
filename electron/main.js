const { app, BrowserWindow, ipcMain, Menu, Tray, nativeImage } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
let pythonProcess = null;
let mainWindow = null;

// Python backend process
function startPythonBackend() {
    const port = process.env.PORT || 5000;
    
    // Set environment variables
    const env = { ...process.env };
    
    pythonProcess = spawn('python', ['api_server.py'], {
        cwd: __dirname + '/../',
        env: env
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`[Python Backend]: ${data}`);
        
        // Check if server is ready
        if (data.toString().includes('Starting EatUp Pro API Server')) {
            console.log('✅ Python backend started successfully');
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`[Python Error]: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python backend exited with code ${code}`);
    });
}

// Helper function to make HTTP requests
function apiRequest(endpoint, options = {}) {
    return new Promise((resolve, reject) => {
        const url = `http://localhost:5000${endpoint}`;
        const reqOptions = {
            hostname: 'localhost',
            port: 5000,
            path: endpoint,
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        };

        const req = http.request(reqOptions, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    resolve(data);
                }
            });
        });

        req.on('error', (e) => {
            reject(e);
        });

        if (options.body) {
            req.write(JSON.stringify(options.body));
        }

        req.end();
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        title: 'EatUp Pro - Disk Cleanup Tool',
        show: false,
        backgroundColor: '#fbfbfd',
        icon: path.join(__dirname, 'assets', 'icon.png')
    });

    // Load the web app
    mainWindow.loadFile('../app.html');

    // Show when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // System tray integration
    setupTray(mainWindow);
}

function createSystemIcon() {
    // Create a simple blue square icon using nativeImage
    const canvas = require('canvas');
    const img = canvas.createCanvas(64, 64);
    const ctx = img.getContext('2d');
    
    // Draw background
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(0, 0, 64, 64);
    
    // Draw disk symbol
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(32, 32, 20, 0, Math.PI * 2);
    ctx.stroke();
    
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(28, 40, 8, 6);
    
    return nativeImage.createFromDataURL(img.toDataURL());
}

function setupTray(parentWindow) {
    let trayIcon;
    try {
        const iconPath = path.join(__dirname, 'assets', 'icon.ico');
        if (require('fs').existsSync(iconPath)) {
            trayIcon = new Tray(iconPath);
        }
    } catch (e) {
        console.log('Using default system tray');
        trayIcon = new Tray(nativeImage.createEmpty());
    }
    
    if (!trayIcon) return;
    
    trayIcon.setToolTip('EatUp Pro - Disk Cleanup Tool');

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Quick Scan',
            icon: nativeImage.createFromPath(path.join(__dirname, 'assets', 'scan.png')),
            click: () => parentWindow.webContents.send('quick-action', { action: 'scan' })
        },
        {
            label: 'Smart Cleanup',
            icon: nativeImage.createFromPath(path.join(__dirname, 'assets', 'cleanup.png')),
            click: () => parentWindow.webContents.send('quick-action', { action: 'cleanup', type: 'smart' })
        },
        { type: 'separator' },
        {
            label: 'View Storage Overview',
            click: () => parentWindow.show()
        },
        { type: 'separator' },
        {
            label: 'Analytics Dashboard',
            click: () => {
                const dashboardWindow = new BrowserWindow({
                    width: 1000,
                    height: 700,
                    parent: parentWindow,
                    webPreferences: {
                        nodeIntegration: false,
                        contextIsolation: true
                    }
                });
                dashboardWindow.loadFile('../analytics_dashboard.html');
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => app.quit()
        }
    ]);

    trayIcon.setContextMenu(contextMenu);
    
    // Double-click to show main window
    trayIcon.on('double-click', () => {
        parentWindow.show();
    });
}

// Setup IPC handlers for renderer process
function setupIPCHandlers() {
    ipcMain.handle('api-request', async (event, endpoint, options = {}) => {
        try {
            const result = await apiRequest(endpoint, options);
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('start-scan', async (event, drive = 'C:') => {
        try {
            const result = await apiRequest('/api/v1/scan/start', {
                method: 'POST',
                body: { drive }
            });
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('run-cleanup', async (event, { type }) => {
        try {
            const result = await apiRequest('/api/v1/cleanup/run', {
                method: 'POST',
                body: { type }
            });
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('get-usage-stats', async () => {
        try {
            const result = await apiRequest('/api/v1/usage/stats');
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('health-check', async () => {
        try {
            const result = await apiRequest('/api/v1/health');
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('get-recent-scans', async (event, limit = 10) => {
        try {
            const result = await apiRequest(`/api/v1/analytics/scans?limit=${limit}`);
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('get-cleanup-history', async (event, limit = 20) => {
        try {
            const result = await apiRequest(`/api/v1/analytics/cleanup-history?limit=${limit}`);
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('get-trends', async (event, days = 90) => {
        try {
            const result = await apiRequest(`/api/v1/analytics/trends?days=${days}`);
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });

    ipcMain.handle('get-statistics', async () => {
        try {
            const result = await apiRequest('/api/v1/analytics/statistics');
            return { success: true, data: result };
        } catch (error) {
            return { success: false, error: error.message };
        }
    });
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
