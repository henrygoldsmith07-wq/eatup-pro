// Helper: Sleep utility for async operations
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        // Display actual scan results from API
        async function displayScanResults(results, scanId) {
            lastScanResults = results;
            const map = document.getElementById('storageMap');
            const categories = ['Applications', 'Videos', 'Documents', 'Images', 'Music', 'Downloads', 'System', 'Other'];
            const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500', 'bg-red-500', 'bg-teal-500', 'bg-indigo-500', 'bg-pink-500'];
            
            // Update storage totals
            document.getElementById('totalUsed').textContent = `${results.total_used_gb ? results.total_used_gb.toFixed(1) : '--'} GB used`;
            const ofTotal = document.querySelector('#storageResults .glass-nav p.text-sm');
            if (ofTotal && results.total_space_gb) {
                ofTotal.textContent = `of ${results.total_space_gb.toFixed(1)} GB total`;
            }
            const freeUp = document.querySelector('#storageResults .bg-gradient-to-br p strong');
            if (freeUp) {
                freeUp.textContent = formatSize(results.cleanable_gb);
            }
            
            // Clear and rebuild storage map with real data
            map.innerHTML = '';
            
            if (results.categories) {
                const catKeys = Object.keys(results.categories);
                const catValues = Object.values(results.categories);
                
                const largest = Math.max(...catValues, 1);
                catKeys.forEach((cat, i) => {
                    const size = catValues[i] || 0;
                    // Scale spans to the grid so a large category cannot create
                    // implicit columns and break the fixed-height treemap.
                    const colSpan = Math.max(1, Math.min(8, Math.ceil(size / largest * 8)));
                    const rowSpan = Math.max(1, Math.min(4, Math.ceil(size / largest * 4)));
                    
                    const div = document.createElement('div');
                    div.className = `${colors[i % colors.length]} rounded-lg treemap-item relative group cursor-pointer hover:opacity-90 transition-opacity`;
                    div.style.gridColumn = `span ${colSpan}`;
                    div.style.gridRow = `span ${rowSpan}`;
                    div.title = `${cat}: ${formatSize(size)}`;
                    div.innerHTML = `
                        <div class="absolute inset-0 flex items-center justify-center text-white font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                            ${categories[i] || cat}
                        </div>
                        <div class="absolute bottom-2 left-2 right-2 text-xs opacity-90 truncate">
                            ${formatSize(size)}
                        </div>
                    `;
                    
                    div.onclick = () => showCategoryDetails(cat, size);
                    map.appendChild(div);
                });
            }
            
            // Populate category bars with real data
            renderCategoryBars(results.categories);
            
            // Show results section
            document.getElementById('storageResults').classList.remove('hidden');
            showSection('storage');
            
            // Prepare cleanup categories based on results
            prepareCleanupCategories();
        }
        
        // Render category distribution bars
        function renderCategoryBars(categories) {
            const container = document.getElementById('categoryBars');
            container.innerHTML = '';
            
            const total = Object.values(categories).reduce((a, b) => a + b, 0);
            if (total === 0) return;
            
            const catNames = ['Applications', 'Videos', 'Documents', 'Images', 'Music', 'Downloads', 'System', 'Other'];
            const icons = ['💿', '🎬', '📄', '🖼️', '🎵', '📥', '⚙️', '📦'];
            const colors = ['text-blue-500', 'text-green-500', 'text-purple-500', 'text-orange-500', 'text-red-500', 'text-teal-500', 'text-indigo-500', 'text-pink-500'];
            
            Object.entries(categories).forEach(([name, size], index) => {
                const percentage = ((size / total) * 100).toFixed(1);
                const icon = icons[index % icons.length];
                const colorClass = colors[index % colors.length];
                
                const barContainer = document.createElement('div');
                barContainer.className = 'mb-6';
                barContainer.innerHTML = `
                    <div class="flex justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <span class="text-lg">${icon}</span>
                            <span class="font-semibold text-neutral-700 dark:text-neutral-300">${name}</span>
                        </div>
                        <span class="text-sm text-neutral-500">${percentage}% (${formatSize(size)})</span>
                    </div>
                    <div class="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-3 overflow-hidden">
                        <div class="bg-brand-500 h-full rounded-full progress-bar"></div>
                    </div>
                `;
                barContainer.querySelector('.progress-bar').style.width = `${percentage}%`;
                container.appendChild(barContainer);
            });
        }
        
        // Show category details tooltip
        function showCategoryDetails(category, size) {
            alert(`${category} files:\nSize: ${formatSize(size)}\nThis category could be cleaned up.`);
        }
        
        // Prepare cleanup categories based on scan results
        function prepareCleanupCategories() {
            const cleanupSection = document.getElementById('cleanup-section');
            cleanupSection.classList.remove('hidden');

            const results = lastScanResults || {};
            const gb = value => formatSize(value);
            const categories = [
                { id: 'temp', name: 'Temporary Files', icon: '🗑️',
                  count: `${results.temp_files_count ?? 0} files`, size: gb(results.temp_gb) },
                { id: 'duplicates', name: 'Duplicate Files', icon: '🔄',
                  count: `${results.duplicate_groups ?? 0} groups`, size: gb(results.duplicate_gb) },
                { id: 'large', name: 'Large Files (>1GB)', icon: '💾',
                  count: `${results.large_files_count ?? 0} files`, size: 'See results' },
                { id: 'downloads', name: 'Old Downloads', icon: '📥', count: 'Not scanned', size: '-' },
                { id: 'cache', name: 'System Cache', icon: '💰', count: 'Not scanned', size: '-' }
            ];

            renderCleanupCategoriesWithRealData(categories);
        }
        
        // Render cleanup categories with real data from API
        function renderCleanupCategoriesWithRealData(categories) {
            const container = document.getElementById('cleanupCategories');
            container.innerHTML = '';
            
            categories.forEach(cat => {
                const available = !String(cat.count).includes('Not scanned');
                const card = document.createElement('div');
                card.className = 'bg-white dark:bg-neutral-800 rounded-xl p-6 file-card border-2 border-transparent hover:border-brand-500';
                card.id = cat.id + '-card';
                card.innerHTML = `
                    <div class="flex items-start gap-4">
                        <input type="checkbox" aria-label="Select ${cat.name} for cleanup"
                               data-cleanup-checkbox
                               class="mt-1 w-5 h-5 rounded border-gray-300 text-brand-500 focus:ring-brand-500"
                               ${available ? '' : 'disabled'}>
                        <div class="flex-1">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <span class="text-2xl" aria-hidden="true">${cat.icon}</span>
                                    <h3 class="font-bold text-lg">${cat.name}</h3>
                                </div>
                                <span class="text-sm text-neutral-500">${cat.count} • ${cat.size}</span>
                            </div>
                            <p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">${available ? 'Moved to Recycle Bin after confirmation' : 'Not included in the current scan'}</p>
                        </div>
                    </div>
                `;
                if (available) card.addEventListener('click', event => {
                    if (event.target.tagName === 'INPUT') return;
                    toggleSelection(cat.id);
                });
                container.appendChild(card);
            });
        }

        // Theme Toggle
        function toggleTheme() {
            const html = document.documentElement;
            const isDark = html.classList.toggle('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
        }

        // Mobile Menu
        function toggleMobileMenu() {
            const menu = document.getElementById('mobileMenu');
            const button = document.getElementById('mobileMenuBtn');
            const open = menu.classList.toggle('hidden') === false;
            if (button) {
                button.setAttribute('aria-expanded', String(open));
                button.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
            }
        }

        // Show Section
        function showSection(section) {
            document.querySelectorAll('main > section').forEach(s => s.classList.add('hidden'));
            if (section === 'storage') {
                document.getElementById('storage-section').classList.remove('hidden');
            } else if (section === 'cleanup') {
                document.getElementById('cleanup-section').classList.remove('hidden');
            }
        }

        // API Configuration. Sample data is only acceptable when the page is
        // opened directly from disk, and must be labelled as such.
        const API_BASE_URL = '/api/v1';
        const DEMO_MODE = location.protocol === 'file:';

        // When API_KEY is enabled the UI needs to send it. Keep the key in
        // session storage so it is never written to a file or shared elsewhere.
        (function () {
            const keyName = 'eatup_api_key';
            const nativeFetch = window.fetch.bind(window);
            window.fetch = function (input, init) {
                const url = typeof input === 'string' ? input : (input && input.url) || '';
                const key = sessionStorage.getItem(keyName);
                if (url.indexOf('/api/v1/') !== -1 && key) {
                    init = init || {};
                    const headers = new Headers(init.headers || {});
                    headers.set('X-API-Key', key);
                    init.headers = headers;
                }
                return nativeFetch(input, init);
            };
            window.addEventListener('load', () => {
                const button = document.getElementById('apiKeyButton');
                if (!button) return;
                button.addEventListener('click', () => {
                    const current = sessionStorage.getItem(keyName) || '';
                    const entered = window.prompt('Local EatUp API key (blank to clear):', current);
                    if (entered === null) return;
                    if (entered.trim()) sessionStorage.setItem(keyName, entered.trim());
                    else sessionStorage.removeItem(keyName);
                    button.title = sessionStorage.getItem(keyName) ? 'API key set' : 'Set API key';
                });
            });
        })();

        let lastScanResults = null;

        function openScanModal() {
            const modal = document.getElementById('scanModal');
            modal.classList.remove('hidden');
            modal.focus();
        }

        function closeScanModal() {
            document.getElementById('scanModal').classList.add('hidden');
        }

        document.addEventListener('keydown', event => {
            if (event.key !== 'Escape') return;
            const modal = document.getElementById('scanModal');
            if (modal && !modal.classList.contains('hidden')) closeScanModal();
            document.querySelectorAll('[role="alertdialog"]').forEach(dialog => dialog.remove());
        });

        function setProgress(value) {
            const bar = document.getElementById('scanProgress');
            bar.style.width = value;
            const numeric = parseInt(String(value), 10);
            if (Number.isFinite(numeric)) bar.setAttribute('aria-valuenow', String(numeric));
        }

        function formatSize(gb) {
            const bytes = (gb || 0) * 1024 ** 3;
            if (bytes === 0) return '0 B';
            if (bytes < 1024) return `${bytes.toFixed(0)} B`;
            if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(0)} KB`;
            if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
            return `${gb.toFixed(2)} GB`;
        }

        function escapeHtml(value) {
            return String(value).replace(/[&<>"']/g, ch => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            })[ch]);
        }
        
        function apiUnavailable(message) {
            const dialog = document.createElement('div');
            dialog.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6';
            dialog.setAttribute('role', 'alertdialog');
            dialog.setAttribute('aria-modal', 'true');
            dialog.innerHTML = `
                <div class="bg-white dark:bg-neutral-800 rounded-2xl p-8 max-w-md w-full shadow-2xl">
                    <h3 class="font-bold text-lg mb-2">Unable to reach the API</h3>
                    <p class="text-neutral-600 dark:text-neutral-400 mb-4">${escapeHtml(message)}</p>
                    <p class="text-sm text-neutral-500 mb-4">Run <code>python api_server.py</code> and reload this page. No files were changed.</p>
                    <button type="button" data-action="dismissDialog" class="px-6 py-3 bg-brand-500 text-white rounded-lg font-semibold hover:bg-brand-600">Dismiss</button>
                </div>
            `;
            document.body.appendChild(dialog);
            dialog.querySelector('button').focus();
        }

        function showDemoBanner() {
            if (document.getElementById('demoBanner')) return;
            const banner = document.createElement('div');
            banner.id = 'demoBanner';
            banner.className = 'bg-amber-100 text-amber-900 px-6 py-3 text-center font-semibold';
            banner.textContent = 'Sample data only — no disk was scanned and no files were changed.';
            document.querySelector('main').prepend(banner);
        }

        function showApiError(message) {
            if (DEMO_MODE) {
                alert('Demo mode: ' + message);
            } else {
                apiUnavailable(message);
            }
        }

        async function scanDrive(drive = 'C:') {
            const modal = document.getElementById('scanModal');
            const progressBar = document.getElementById('scanProgress');
            const statusText = document.getElementById('scanStatus');
            
            openScanModal();
            setProgress('5%');
            statusText.textContent = 'Initializing scan...';
            
            try {
                // Start scan via API
                const response = await fetch(`${API_BASE_URL}/scan/start`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({drive: drive})
                });
                
                if (!response.ok) {
                    throw new Error(`Scan failed: ${response.statusText}`);
                }
                
                const data = await response.json();
                const scanId = data.scan_id;
                
                statusText.textContent = `Scan started (${drive}). Waiting for results...`;
                setProgress('20%');
                
                // Poll for scan completion
                let attempts = 0;
                const maxAttempts = 600; // 10 minutes: duplicate detection hashes file contents
                
                while (attempts < maxAttempts) {
                    await sleep(1000); // Wait 1 second between polls
                    attempts++;
                    
                    const statusResponse = await fetch(`${API_BASE_URL}/scan/status/${scanId}`);
                    const statusData = await statusResponse.json();
                    
                    if (statusData.status === 'failed') {
                        throw new Error(statusData.message);
                    }
                    
                    if (statusData.status === 'complete') {
                        setProgress('100%');
                        statusText.textContent = 'Scan complete! Loading results...';
                        
                        // Get detailed results
                        const resultsResponse = await fetch(`${API_BASE_URL}/scan/results/${scanId}`);
                        if (!resultsResponse.ok) {
                            throw new Error('Scan finished but its results are no longer available. Run a new scan.');
                        }
                        displayScanResults(await resultsResponse.json(), scanId);

                        setTimeout(() => {
                            closeScanModal();
                        }, 500);
                        break;
                    } else if (statusData.status === 'running') {
                        // Update progress based on scan phase
                        const progress = statusData.progress || Math.min(80, (attempts / maxAttempts) * 80);
                        setProgress(`${progress}%`);
                        
                        // Dynamic status messages based on progress
                        if (attempts < 30) {
                            statusText.textContent = 'Analyzing file system structure...';
                        } else if (attempts < 90) {
                            statusText.textContent = 'Computing file hashes and finding duplicates...';
                        } else if (attempts < 150) {
                            statusText.textContent = 'Calculating statistics and categorizing files...';
                        }
                    }
                }
                
                if (attempts >= maxAttempts) {
                    throw new Error('Scan timed out');
                }

            } catch (error) {
                console.error('Scan error:', error);
                closeScanModal();
                showApiError(error.message || 'The scan could not be completed.');
                // Never present sample numbers as a real scan result. Only the
                // file:// demo is allowed to show sample data, clearly labelled.
                if (DEMO_MODE) showDemoBanner();
            }
        }

        // Populate Storage Data
        function populateStorageData() {
            const map = document.getElementById('storageMap');
            const categories = ['Applications', 'Videos', 'Documents', 'Images', 'Music', 'Downloads', 'System', 'Other'];
            const colors = ['bg-blue-500', 'bg-green-500', 'bg-purple-500', 'bg-orange-500', 'bg-red-500', 'bg-teal-500', 'bg-indigo-500', 'bg-pink-500'];
            const sizes = [45, 24, 18, 8, 3, 1, 1, 0];
            
            map.innerHTML = '';
            const totalSize = sizes.reduce((a, b) => a + b, 0);
            
            categories.forEach((cat, i) => {
                const size = sizes[i];
                const colSpan = Math.max(1, Math.floor(size / 5));
                const rowSpan = Math.max(1, Math.floor(size / 10));
                
                const div = document.createElement('div');
                div.className = `${colors[i]} rounded-lg treemap-item relative`;
                div.style.gridColumn = `span ${colSpan}`;
                div.style.gridRow = `span ${rowSpan}`;
                div.innerHTML = `<div class="absolute inset-0 flex items-center justify-center text-white font-bold text-sm opacity-0 group-hover:opacity-100 transition-opacity">${cat}</div>`;
                map.appendChild(div);
            });
            
            document.getElementById('totalUsed').textContent = '197 GB used';
        }

        // Render Cleanup Categories
        function renderCleanupCategories() {
            const categories = [
                { id: 'temp', name: 'Temporary Files', icon: '🗑️', count: 1247, size: '2.3 GB', selected: true },
                { id: 'duplicates', name: 'Duplicate Files', icon: '🔄', count: 89, size: '4.8 GB', selected: true },
                { id: 'large', name: 'Large Files (>1GB)', icon: '💾', count: 23, size: '12.1 GB', selected: false },
                { id: 'downloads', name: 'Old Downloads', icon: '📥', count: 156, size: '1.2 GB', selected: false },
                { id: 'cache', name: 'System Cache', icon: '💰', count: 2341, size: '890 MB', selected: false }
            ];
            
            const container = document.getElementById('cleanupCategories');
            container.innerHTML = '';
            
            categories.forEach(cat => {
                const card = document.createElement('div');
                card.className = 'bg-white dark:bg-neutral-800 rounded-xl p-6 file-card cursor-pointer border-2 border-transparent hover:border-brand-500';
                card.onclick = () => toggleSelection(cat.id);
                card.id = cat.id + '-card';
                
                const isChecked = cat.selected ? 'checked' : '';
                
                card.innerHTML = `
                    <div class="flex items-start gap-4">
                        <input type="checkbox" data-cleanup-checkbox class="mt-1 w-5 h-5 rounded border-gray-300 text-brand-500 focus:ring-brand-500" ${isChecked}>
                        <div class="flex-1">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-3">
                                    <span class="text-2xl">${cat.icon}</span>
                                    <h3 class="font-bold text-lg">${cat.name}</h3>
                                </div>
                                <span class="text-sm text-neutral-500">${cat.count} files • ${cat.size}</span>
                            </div>
                            <p class="text-sm text-neutral-600 dark:text-neutral-400 mt-1">Safe to remove • Goes to Recycle Bin</p>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        // Update Selection
        function updateSelection() {
            const selected = [...document.querySelectorAll('#cleanupCategories input:checked')];
            const preview = document.getElementById('cleanupPreview');
            if (selected.length) {
                preview.classList.remove('hidden');
                renderFilesList(selected);
            } else {
                preview.classList.add('hidden');
            }
        }

        // Toggle Selection
        function toggleSelection(id) {
            const checkbox = document.querySelector(`#${id}-card input`);
            if (checkbox && !checkbox.disabled) {
                checkbox.checked = !checkbox.checked;
                updateSelection();
            }
        }

        // Render Files List
        function renderFilesList(selected = []) {
            const list = document.getElementById('filesList');
            list.innerHTML = '';

            const large = (lastScanResults && lastScanResults.large_files) || [];
            if (!large.length) {
                const empty = document.createElement('p');
                empty.className = 'text-sm text-neutral-500';
                empty.textContent = 'File-level details are not included in the scan API response. Export a report from the CLI for the full list.';
                list.appendChild(empty);
            } else {
                large.forEach(file => {
                    const item = document.createElement('div');
                    item.className = 'flex justify-between items-center gap-3 p-4 bg-neutral-50 dark:bg-neutral-900 rounded-lg';
                    // Paths come from the API, so treat them as untrusted text.
                    const path = escapeHtml(file.path);
                    const name = escapeHtml(String(file.path).split(/[\\/]/).pop());
                    item.innerHTML = `
                        <div class="min-w-0">
                            <p class="font-semibold truncate" title="${path}">${name}</p>
                            <p class="text-sm text-neutral-500 truncate">${path}</p>
                        </div>
                        <p class="font-bold text-brand-500 whitespace-nowrap">${(file.size_gb || 0).toFixed(2)} GB</p>
                    `;
                    list.appendChild(item);
                });
            }

            const cleanable = selected.reduce((sum, checkbox) => {
                const id = checkbox.closest('[id]')?.id || '';
                if (id.startsWith('temp')) return sum + (lastScanResults?.temp_gb || 0);
                if (id.startsWith('duplicates')) return sum + (lastScanResults?.duplicate_gb || 0);
                return sum;
            }, 0);
            document.getElementById('totalSpace').textContent = `${formatSize(cleanable)} estimated`;
        }

        // Execute Cleanup via API
        async function performCleanup(cleanupType = 'smart', options = {}) {
            const modal = document.getElementById('scanModal');
            const progressBar = document.getElementById('scanProgress');
            const statusText = document.getElementById('scanStatus');
            
            openScanModal();
            setProgress('5%');
            statusText.textContent = `Starting ${cleanupType} cleanup...`;
            
            try {
                const response = await fetch(`${API_BASE_URL}/cleanup/run`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: cleanupType})
                });
                
                if (!response.ok) {
                    throw new Error(`Cleanup failed: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Update progress
                setProgress('40%');
                statusText.textContent = 'Processing files...';
                
                // Wait a moment then show results
                await sleep(1500);
                
                if (!options.deferDisplay) {
                    closeScanModal();
                    displayCleanupResults(data.space_freed_mb || 0, cleanupType);
                }
                return data.space_freed_mb || 0;

            } catch (error) {
                console.error('Cleanup error:', error);
                closeScanModal();
                showApiError(error.message || 'Cleanup could not be completed. No files were changed.');
                return 0;
            }
        }
        
        // Display cleanup results
        function displayCleanupResults(spaceFreedMB, type) {
            const spaceFreedGB = spaceFreedMB / 1024;
            
            document.querySelectorAll('main > section').forEach(s => s.classList.add('hidden'));
            document.getElementById('results-section').classList.remove('hidden');
            
            // Update result display
            const resultElement = document.querySelector('#results-section p.text-6xl.font-bold.mb-4');
            if (resultElement) {
                resultElement.textContent = `${spaceFreedGB.toFixed(1)} GB`;
            }
        }
        
        // Quick Clean Functions - Updated to use API
        async function quickClean(type) {
            if (!lastScanResults) {
                showSection('storage');
                showApiError('Run a scan first so cleanup knows what is safe to remove. No files were changed.');
                return;
            }
            showSection('cleanup');
            // The API calls the combined operation 'smart'; the quick action says 'all'.
            await performCleanup(type === 'all' ? 'smart' : type);
        }
        
        // Cleanup operations
        async function confirmCleanup() {
            document.getElementById('confirmDialog').showModal();
        }
        
        function closeDialog() {
            document.getElementById('confirmDialog').close();
        }
        
        async function executeCleanup() {
            closeDialog();
            const selected = [...document.querySelectorAll('#cleanupCategories input:checked')]
                .map(cb => (cb.closest('[id]')?.id || '').replace('-card', ''))
                .filter(id => ['temp', 'duplicates', 'large'].includes(id));
            if (!selected.length) {
                showApiError('Select at least one cleanup category first. No files were changed.');
                return;
            }
            const types = (selected.includes('temp') && selected.includes('duplicates'))
                ? ['smart', ...selected.filter(id => id === 'large')]
                : selected;
            let freed = 0;
            for (const type of types) {
                freed += await performCleanup(type, { deferDisplay: true });
            }
            document.getElementById('scanModal').classList.add('hidden');
            displayCleanupResults(freed, types.join('+'));
        }

        // Deselect All
        function deselectAll() {
            document.querySelectorAll('#cleanupCategories input[type="checkbox"]').forEach(cb => cb.checked = false);
            document.getElementById('cleanupPreview').classList.add('hidden');
        }

        // Initialize
        window.addEventListener('load', () => {
            if (!lastScanResults) {
                document.getElementById('cleanupCategories').innerHTML =
                    '<p class="text-sm text-neutral-500 rounded-xl border border-dashed border-neutral-300 dark:border-neutral-700 p-8 text-center">Run a scan from Storage Overview to review cleanup candidates.</p>';
            }
            const storedTheme = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (storedTheme === 'dark' || (!storedTheme && prefersDark)) {
                document.documentElement.classList.add('dark');
            }
            
            // Setup theme toggle
            const themeToggle = document.getElementById('themeToggle');
            if (themeToggle) {
                themeToggle.addEventListener('click', toggleTheme);
            }
            
            // Setup mobile menu button
            const mobileMenuBtn = document.getElementById('mobileMenuBtn');
            if (mobileMenuBtn) {
                mobileMenuBtn.addEventListener('click', toggleMobileMenu);
            }
            
            // Dynamic category cards are also keyboard and screen-reader accessible
            document.getElementById('cleanupPreview').setAttribute('aria-live', 'polite');
        });

        // Event delegation replaces inline onclick/onchange handlers so a strict
        // Content-Security-Policy can be used without unsafe-inline.
        const actionHandlers = {
            scanDrive: () => scanDrive(),
            'show-storage': () => showSection('storage'),
            'show-cleanup': () => showSection('cleanup'),
            'toggle-menu': () => toggleMobileMenu(),
            'scan-menu': () => { scanDrive(); toggleMobileMenu(); },
            'storage-menu': () => { showSection('storage'); toggleMobileMenu(); },
            'cleanup-menu': () => { showSection('cleanup'); toggleMobileMenu(); },
            'quick-temp': () => quickClean('temp'),
            'quick-duplicates': () => quickClean('duplicates'),
            'quick-large': () => quickClean('large'),
            'quick-all': () => quickClean('all'),
            performCleanup: () => performCleanup(),
            deselectAll: () => deselectAll(),
            confirmCleanup: () => confirmCleanup(),
            reload: () => location.reload(),
            closeDialog: () => closeDialog(),
            executeCleanup: () => executeCleanup(),
            dismissDialog: (element) => element.closest('.fixed')?.remove(),
        };

        document.addEventListener('click', event => {
            const target = event.target.closest('[data-action]');
            if (!target) return;
            const handler = actionHandlers[target.dataset.action];
            if (handler) handler(target);
        });

        document.addEventListener('change', event => {
            if (event.target.matches('[data-cleanup-checkbox]')) updateSelection();
        });
