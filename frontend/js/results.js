/**
 * Results Page JavaScript
 * Display detection results with visualizations
 */

const API_BASE = window.location.origin;

document.addEventListener('DOMContentLoaded', () => {
    loadResults();
});

/**
 * Load and display results
 */
function loadResults() {
    const resultsData = sessionStorage.getItem('detectionResults');

    if (!resultsData) {
        showNoResults();
        return;
    }

    try {
        const results = JSON.parse(resultsData);
        displayResults(results);
    } catch (error) {
        console.error('Error parsing results:', error);
        showNoResults();
    }
}

/**
 * Display detection results
 */
function displayResults(results) {
    // Update stats
    const detections = results.detections || [];
    const totalFaces = results.total_faces || detections.length || 0;
    const matched = detections.filter(d => d.is_match).length || 0;
    const processingTime = results.processing_time?.toFixed(2) || 0;

    updateElement('totalFaces', totalFaces);
    updateElement('matchedFaces', matched);
    updateElement('processingTime', processingTime + 's');

    // Show annotated image if available
    const img = document.getElementById('result-image');
    if (results.annotated_image && img) {
        img.src = API_BASE + results.annotated_image;
    }

    // Display detections
    const container = document.getElementById('detections-list');
    const noResults = document.getElementById('noResults');

    if (detections.length > 0) {
        if (container) {
            container.innerHTML = '';
            detections.forEach((detection, index) => {
                const card = createDetectionCard(detection, index);
                container.appendChild(card);
            });
        }
        if (noResults) noResults.style.display = 'none';
        if (container) container.style.display = 'flex';
    } else {
        if (container) container.style.display = 'none';
        if (noResults) noResults.style.display = 'block';
    }
}

/**
 * Create detection card element
 */
function createDetectionCard(detection, index) {
    const card = document.createElement('div');
    card.className = 'detection-card fade-in';
    card.style.animationDelay = `${index * 0.1}s`;

    const personName = detection.person_name || 'Unknown';
    const personId = detection.person_id || 'N/A';
    const confidence = detection.confidence || 0;
    const isMatch = detection.is_match || false;
    const occlusion = detection.occlusion || 0;
    // Use our temp API for face image
    // If detection.face_image_path is null or empty, this will be ''
    let faceImgUrl = '';
    if (detection.face_image_path) {
        // If it starts with /api already (it shouldn't in current app.py but good for robustness)
        if (detection.face_image_path.startsWith('/api')) {
            faceImgUrl = API_BASE + detection.face_image_path;
        } else {
            // Path returned by app/video is folder/filename or just filename for image
            faceImgUrl = API_BASE + '/api/file/temp/' + detection.face_image_path;
        }
    }

    card.innerHTML = `
        <img src="${faceImgUrl}" class="face-thumbnail" alt="Face" onerror="this.src='https://via.placeholder.com/60?text=Face'">
        <div style="flex: 1; display: flex; flex-direction: column; gap: 0.25rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; font-size: 1.1rem; color: var(--text-main);">${personName}</span>
                <span style="font-size: 0.75rem; padding: 0.2rem 0.6rem; border-radius: 1rem; background: ${isMatch ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}; color: ${isMatch ? 'var(--success)' : 'var(--error)'};">
                    ${isMatch ? 'MATCH' : 'UNKNOWN'}
                </span>
            </div>
            
            <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: var(--text-muted);">
                <span>Similarity</span>
                <div style="flex: 1; height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; background: var(--gradient-main); width: ${confidence * 100}%;"></div>
                </div>
                <span style="color: var(--text-main); font-weight: 500;">${(confidence * 100).toFixed(1)}%</span>
            </div>

            ${occlusion > 0 ? `
            <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; background: rgba(255,255,255,0.03); padding: 0.4rem; border-radius: 0.4rem; margin-top: 0.2rem;">
                <ion-icon name="shield-half-outline" style="color: var(--secondary);"></ion-icon>
                <span>Occlusion: <strong>${(occlusion * 100).toFixed(0)}%</strong></span>
            </div>
            ` : ''}

            <div style="font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 0.75rem; margin-top: 0.2rem;">
                ${personId !== 'N/A' ? `<span>ID: ${personId}</span>` : ''}
                ${detection.timestamp !== undefined ? `<span>Time: ${formatTimestamp(detection.timestamp)}</span>` : ''}
            </div>
        </div>
    `;

    return card;
}

/**
 * Show no results message
 */
function showNoResults() {
    const grid = document.getElementById('detections-list');
    const noResults = document.getElementById('noResults');

    if (grid) grid.style.display = 'none';
    if (noResults) noResults.style.display = 'block';
}

/**
 * Utility: Update element text
 */
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

/**
 * Utility: Format timestamp
 */
function formatTimestamp(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}
