/**
 * TrueFace AI - History Page Logic
 * Handles activity logs, filtering, and report downloads.
 */

const API_BASE = window.location.origin;
let historyData = [];
let currentFilter = 'all';

document.addEventListener('DOMContentLoaded', () => {
    // Auth Check
    if (typeof auth !== 'undefined') {
        auth.checkAuth();
        const user = auth.getUser();
        if (user) {
            document.getElementById('user-display').textContent = user.readable_id;
            
            // Hide Admin link if not admin
            if (!auth.hasRole('ADMIN')) {
                document.querySelectorAll('[data-role="ADMIN"]').forEach(el => el.classList.add('hidden'));
            }
        }
    }

    loadHistory();
    setupFilters();
    setupDownload();
});

/**
 * Load history from API
 */
async function loadHistory() {
    try {
        const response = await fetch(API_BASE + '/api/history?limit=100');
        const data = await response.json();

        if (data.success) {
            historyData = data.history || [];
            displayHistory();
        } else {
            document.getElementById('no-history').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading history:', error);
        document.getElementById('no-history').style.display = 'block';
    }
}

/**
 * Display history items
 */
function displayHistory() {
    const container = document.getElementById('history-list');
    const noHistory = document.getElementById('no-history');
    
    const filtered = currentFilter === 'all' 
        ? historyData 
        : historyData.filter(h => h.file_type === currentFilter);

    container.innerHTML = '';
    
    if (filtered.length === 0) {
        noHistory.style.display = 'block';
        return;
    }

    noHistory.style.display = 'none';
    filtered.forEach(item => {
        const div = document.createElement('div');
        div.className = 'history-item';
        
        const date = new Date(item.upload_time).toLocaleString();
        const matches = (item.detections || []).filter(d => d.is_match).length;
        
        div.innerHTML = `
            <div style="font-size: 0.8rem; font-weight: 700; width: 80px;">${item.file_type.toUpperCase()}</div>
            <div>
                <div style="font-weight: 700;">${item.filename}</div>
                <div class="text-muted" style="font-size: 0.75rem;">${date} | ${item.processing_time?.toFixed(2)}s processing</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.85rem; font-weight: 700;">${matches} / ${(item.detections || []).length} Matches</div>
                <div class="text-muted" style="font-size: 0.7rem;">${(item.file_size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
        `;
        container.appendChild(div);
    });
}

/**
 * Filter Logic
 */
function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.getAttribute('data-filter');
            displayHistory();
        }
    });
}

/**
 * CSV Download Logic
 */
function setupDownload() {
    document.getElementById('btn-download-report').onclick = () => {
        if (historyData.length === 0) return alert('No data to download.');

        // Simple CSV construction
        let csv = 'Filename,Type,Date,Detections,Matches,ProcessingTime(s)\n';
        historyData.forEach(h => {
            const matches = (h.detections || []).filter(d => d.is_match).length;
            csv += `"${h.filename}",${h.file_type},"${new Date(h.upload_time).toLocaleString()}",${(h.detections || []).length},${matches},${h.processing_time?.toFixed(2)}\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.setAttribute('hidden', '');
        a.setAttribute('href', url);
        a.setAttribute('download', `TrueFace_Report_${new Date().toLocaleDateString()}.csv`);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };
}
