// API Configuration
        const API_BASE = '/api/v1';

        (function () {
            const stored = localStorage.getItem('theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (stored === 'dark' || (!stored && prefersDark)) {
                document.documentElement.classList.add('dark');
            }
            window.addEventListener('load', () => {
                const button = document.getElementById('themeToggleAnalytics');
                if (!button) return;
                button.addEventListener('click', () => {
                    const dark = document.documentElement.classList.toggle('dark');
                    localStorage.setItem('theme', dark ? 'dark' : 'light');
                });
            });
        })();

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
                    if (typeof fetchData === 'function') fetchData();
                });
            });
        })();

        let usageChart, pieChart;
        let hasScan = false;

        // Chart.js draws on canvas, so Tailwind's dark classes cannot colour it.
        const darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (typeof Chart !== 'undefined' && darkMode) {
            Chart.defaults.color = '#d1d5db';
            Chart.defaults.borderColor = '#4b5563';
        }

        function escapeHtml(value) {
            return String(value ?? '').replace(/[&<>"']/g, ch => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            })[ch]);
        }

        function fmtMb(mb) {
            const value = Number(mb) || 0;
            return value >= 1024 ? `${(value / 1024).toFixed(2)} GB` : `${value.toFixed(1)} MB`;
        }

        async function getJson(path, options) {
            const response = await fetch(`${API_BASE}${path}`, options);
            if (!response.ok) throw new Error(`${response.status} from ${path}`);
            return response.json();
        }

        function showDataError(message) {
            const banner = document.getElementById('dataError');
            if (!banner) return;
            banner.textContent = `Some analytics could not be loaded: ${message}. Existing values were left unchanged.`;
            banner.classList.remove('hidden');
        }

        async function fetchData() {
            const refresh = document.getElementById('refreshButton');
            const failed = [];
            if (refresh) { refresh.disabled = true; refresh.textContent = 'Refreshing…'; }

            // Each section stands alone: one failing endpoint must not blank
            // the whole dashboard.
            async function section(path, fallback) {
                try { return await getJson(path); }
                catch (error) { console.error(path, error); failed.push(path); return fallback; }
            }

            const [stats, appStats, trends, scans, history, prediction, latest] = await Promise.all([
                section('/usage/stats', {}),
                section('/analytics/statistics', {}),
                section('/analytics/trends?days=90', { data_points: 0 }),
                section('/analytics/scans?limit=30', { scans: [] }),
                section('/analytics/cleanup-history?limit=20', { cleanups: [] }),
                section('/ai/prediction', { available: false, message: 'Prediction data is unavailable.' }),
                section('/scan/latest', null)
            ]);

            document.getElementById('totalUsed').textContent = stats.used_gb != null
                ? `${Number(stats.used_gb).toFixed(1)} GB` : '-- GB';
            document.getElementById('spaceFreed').textContent = fmtMb(
                appStats.total_space_saved_last_30_days_mb || appStats.total_space_freed_mb || 0);
            document.getElementById('filesAnalyzed').textContent = latest
                ? (latest.files_scanned ?? 0).toLocaleString() : (appStats.total_scans || 0).toLocaleString();
            const growth = trends.data_points >= 2 ? trends.daily_growth_mb : null;
            document.getElementById('growthRate').textContent = growth == null
                ? 'Not enough data' : `${Number(growth).toFixed(1)} MB/day`;

            hasScan = Boolean(latest);
            updateCharts(scans.scans || [], latest);
            updateCleanupTable(history.cleanups || []);
            updatePrediction(prediction);
            updateRecommendations(latest, prediction, trends);

            const banner = document.getElementById('dataError');
            if (failed.length) {
                banner.textContent = `Some sections could not be loaded: ${failed.join(', ')}. Other data is up to date.`;
                banner.classList.remove('hidden');
            } else {
                banner.classList.add('hidden');
            }
            if (refresh) { refresh.disabled = false; refresh.textContent = 'Refresh Data'; }
        }

        function ensureCanvas(id) {
            const existing = document.getElementById(id);
            if (existing && existing.tagName === 'CANVAS') return existing;
            const canvas = document.createElement('canvas');
            canvas.id = id;
            if (existing) existing.parentNode.replaceChild(canvas, existing);
            return canvas;
        }

        function updateCharts(scans, latest) {
            const usageCanvas = ensureCanvas('usageTrendChart');
            const pieCanvas = ensureCanvas('categoryPieChart');

            if (usageChart) { usageChart.destroy(); usageChart = null; }
            if (pieChart) { pieChart.destroy(); pieChart = null; }

            if (scans.length >= 2) {
                usageChart = new Chart(usageCanvas.getContext('2d'), {
                    type: 'line',
                    data: {
                        labels: scans.map(s => new Date(s.timestamp).toLocaleDateString()),
                        datasets: [{
                            label: 'Used Space (GB)',
                            data: scans.map(s => Number(s.total_used_gb) || 0),
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { display: false } } }
                });
            } else {
                usageCanvas.replaceWith(emptyCanvasNote(usageCanvas, 'At least two scans are needed to draw a trend.'));
            }

            const categories = latest && latest.categories
                ? Object.entries(latest.categories).filter(([, size]) => size > 0)
                : [];
            if (categories.length) {
                pieChart = new Chart(pieCanvas.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: categories.map(([name]) => name),
                        datasets: [{
                            data: categories.map(([, size]) => Number(size) || 0),
                            backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#6b7280', '#0ea5e9', '#ec4899']
                        }]
                    },
                    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
                });
            } else {
                pieCanvas.replaceWith(emptyCanvasNote(pieCanvas, 'Run a scan to see the category breakdown.'));
            }
        }

        function emptyCanvasNote(canvas, message) {
            const note = document.createElement('p');
            note.className = 'text-sm text-gray-500 dark:text-gray-400 text-center py-10';
            note.textContent = message;
            note.id = canvas.id;
            canvas.parentNode.replaceChild(note, canvas);
            return note;
        }

        function updateCleanupTable(cleanups) {
            const tbody = document.getElementById('cleanupTableBody');
            if (!cleanups.length) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-6 text-center text-sm text-gray-500">No cleanups recorded yet.</td></tr>';
                return;
            }
            tbody.innerHTML = cleanups.map(clean => `
                <tr class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${escapeHtml(new Date(clean.timestamp).toLocaleString())}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">${escapeHtml(clean.type)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${escapeHtml(clean.files_deleted)}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-700 dark:text-green-400">${escapeHtml(fmtMb(clean.space_freed_mb))}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${clean.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${clean.success ? 'completed' : 'partial'}
                        </span>
                    </td>
                </tr>
            `).join('');
        }

        function updatePrediction(prediction) {
            const card = document.getElementById('predictionCard');
            if (!prediction.available) {
                card.innerHTML = `<p class="text-sm text-gray-600 dark:text-gray-400 text-center py-8">${escapeHtml(prediction.message || 'Not enough scan history to project growth.')}</p>`;
                return;
            }
            const date = prediction.predicted_full_date
                ? `Around ${escapeHtml(prediction.predicted_full_date)}`
                : `Growth ${Number(prediction.average_daily_growth_mb || 0).toFixed(1)} MB/day; no full-date estimate`;
            card.innerHTML = `
                <div class="text-center py-6">
                    <p class="text-3xl font-bold text-gray-900 dark:text-white">${date}</p>
                    <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                        Based on ${escapeHtml(prediction.data_points)} recorded scans · ${escapeHtml(prediction.trend_direction)} trend
                    </p>
                </div>`;
        }

        function updateRecommendations(latest, prediction, trends) {
            const list = document.getElementById('recommendationsList');
            const items = [];
            if (latest && latest.cleanable_gb > 0) {
                items.push({ text: `${fmtMb(latest.cleanable_gb * 1024)} is marked cleanable from the latest scan.`, priority: 'high' });
            }
            if (latest && latest.duplicate_groups > 0) {
                items.push({ text: `${latest.duplicate_groups} duplicate groups found; review before removing.`, priority: 'medium' });
            }
            if (prediction.available && prediction.trend_direction === 'increasing') {
                items.push({ text: `Storage is growing at ${Number(prediction.average_daily_growth_mb).toFixed(1)} MB/day.`, priority: 'medium' });
            }
            if (!items.length) {
                items.push({ text: hasScan ? 'No cleanup suggestions from the latest scan.' : 'Run a scan to receive suggestions.', priority: 'low' });
            }
            list.innerHTML = items.map(item => `
                <li class="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <div class="flex-1">
                        <p class="text-sm text-gray-900 dark:text-white">${escapeHtml(item.text)}</p>
                        <span class="text-xs text-gray-500 dark:text-gray-400 capitalize">${escapeHtml(item.priority)} priority</span>
                    </div>
                </li>
            `).join('');
        }

        function refreshData() { fetchData(); }

        // Initialize
        fetchData();
        setInterval(fetchData, 60000);

        document.addEventListener('click', event => {
            const target = event.target.closest('[data-action="refreshData"]');
            if (target) refreshData();
        });
