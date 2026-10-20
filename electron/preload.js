// Preload script for better security with context isolation
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to render process
contextBridge.exposeInMainWorld('eatupAPI', {
    // API Request
    apiRequest: (endpoint, options) => ipcRenderer.invoke('api-request', endpoint, options),
    
    // Scan operations
    startScan: (drive) => ipcRenderer.invoke('start-scan', drive),
    
    // Cleanup operations
    runCleanup: (type) => ipcRenderer.invoke('run-cleanup', { type }),
    
    // Statistics and analytics
    getUsageStats: () => ipcRenderer.invoke('get-usage-stats'),
    getHealthCheck: () => ipcRenderer.invoke('health-check'),
    getRecentScans: (limit) => ipcRenderer.invoke('get-recent-scans', limit),
    getCleanupHistory: (limit) => ipcRenderer.invoke('get-cleanup-history', limit),
    getTrends: (days) => ipcRenderer.invoke('get-trends', days),
    getStatistics: () => ipcRenderer.invoke('get-statistics')
});

console.log('EatUp Pro preload script loaded');
