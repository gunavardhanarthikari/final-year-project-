/**
 * History Page JavaScript
 * Display and filter detection history
 */

const API_BASE = window.location.origin;
let currentFilter = 'all';
let historyData = [];

document.addEventListener('DOMContentLoaded', () => {
    setupFilters();
    loadHistory();
});

/**
 * Setup filter buttons
 */
function setupFilters() {
    const filterBtns = document.querySelectorAll('.filter-btn');

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Apply filter
            currentFilter = btn.dataset.filter;
            displayHistory(historyData);
        });
    });
}

/**
 * Load history from API
 */
async function loadHistory() {
    try {
        const response = await fetch(API_BASE + '/api/history?limit=100');
        const data = await response.json();

        if (data.success) {
            historyData = data.history || [];
            displayHistory(historyData);
        } else {
            showNoHistory();
        }
    } catch (error) {
        console.error('Error loading history:', error);
        showNoHistory();
    } finally {
        hideLoading();
    }
}

/**
 * Display history items
 */
function displayHistory(history) {
    const container = document.getElementById('historyList');

    if (!container) return;

    // Filter history
    const filtered = currentFilter === 'all'
        ? history
        : history.filter(item => item.file_type === currentFilter);

    if (filtered.length === 0) {
        showNoHistory();
        return;
    }

    container.innerHTML = '';

    filtered.forEach((item, index) => {
        const card = createHistoryCard(item, index);
        container.appendChild(card);
    });

    document.getElementById('noHistory').style.display = 'none';
}

/**
 * Create history card element
 */
function createHistoryCard(item, index) {
    const card = document.createElement('div');
    card.className = 'upload-card fade-in';
    card.style.animationDelay = `${index * 0.05}s`;
    card.style.marginBottom = '1.5rem';

    const uploadDate = new Date(item.upload_time);
    const formattedDate = uploadDate.toLocaleString();
    const fileSize = formatFileSize(item.file_size || 0);
    const processingTime = item.processing_time?.toFixed(2) || 'N/A';

    const detections = item.detections || [];
    const totalDetections = detections.length;
    const matchedDetections = detections.filter(d => d.is_match).length;

    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div>
                <h3 class="card-title" style="margin-bottom: 0.25rem;">${item.filename}</h3>
                <p class="text-muted" style="font-size: 0.875rem;">${formattedDate}</p>
            </div>
            <span class="badge ${item.file_type === 'image' ? 'badge-success' : 'badge-warning'}" style="text-transform: uppercase;">
                ${item.file_type}
            </span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
            <div>
                <div class="text-muted" style="font-size: 0.875rem;">File Size</div>
                <div style="font-weight: 600;">${fileSize}</div>
            </div>
            <div>
                <div class="text-muted" style="font-size: 0.875rem;">Processing Time</div>
                <div style="font-weight: 600;">${processingTime}s</div>
            </div>
            <div>
                <div class="text-muted" style="font-size: 0.875rem;">Detections</div>
                <div style="font-weight: 600;">${totalDetections}</div>
            </div>
            <div>
                <div class="text-muted" style="font-size: 0.875rem;">Matches</div>
                <div style="font-weight: 600; color: var(--success-color);">${matchedDetections}</div>
            </div>
        </div>
        
        ${totalDetections > 0 ? `
            <details style="margin-top: 1rem;">
                <summary style="cursor: pointer; font-weight: 600; color: var(--primary-color); user-select: none;">
                    View Detections (${totalDetections})
                </summary>
                <div style="margin-top: 1rem; padding: 1rem; background: var(--bg-secondary); border-radius: 0.5rem;">
                    ${createDetectionsList(detections)}
                </div>
            </details>
        ` : '<p class="text-muted" style="margin-top: 1rem;">No faces detected in this file</p>'}
    `;

    return card;
}

/**
 * Create detections list HTML
 */
function createDetectionsList(detections) {
    return detections.map((det, idx) => {
        const person = det.matched_person;
        const personName = person ? person.name : 'Unknown';
        const confidence = (det.confidence_score * 100).toFixed(1);

        return `
            <div style="padding: 0.75rem; background: var(--bg-primary); border-radius: 0.375rem; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600;">${personName}</div>
                        ${det.frame_number > 0 ? `<div class="text-muted" style="font-size: 0.875rem;">Frame ${det.frame_number}</div>` : ''}
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 600; color: var(--primary-color);">${confidence}%</div>
                        <span class="badge ${det.is_match ? 'badge-success' : 'badge-warning'}" style="font-size: 0.75rem;">
                            ${det.is_match ? 'Matched' : 'Unknown'}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Show no history message
 */
function showNoHistory() {
    const list = document.getElementById('historyList');
    const noHistory = document.getElementById('noHistory');

    if (list) list.innerHTML = '';
    if (noHistory) noHistory.style.display = 'block';
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) loading.style.display = 'none';
}

/**
 * Utility: Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
