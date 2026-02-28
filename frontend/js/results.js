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
    const totalFaces = results.total_faces || results.total_detections || 0;
    const matched = results.detections?.filter(d => d.is_match).length || 0;
    const processingTime = results.processing_time?.toFixed(2) || 0;

    updateElement('totalFaces', totalFaces);
    updateElement('matchedFaces', matched);
    updateElement('processingTime', processingTime + 's');

    // Show annotated image if available
    if (results.annotated_image) {
        const container = document.getElementById('annotatedImageContainer');
        const img = document.getElementById('annotatedImage');

        if (container && img) {
            img.src = API_BASE + results.annotated_image;
            container.style.display = 'block';
        }
    }

    // Display detections
    if (results.detections && results.detections.length > 0) {
        displayDetections(results.detections);
    } else {
        showNoResults();
    }
}

/**
 * Display detection cards
 */
function displayDetections(detections) {
    const grid = document.getElementById('detectionGrid');

    if (!grid) return;

    grid.innerHTML = '';

    detections.forEach((detection, index) => {
        const card = createDetectionCard(detection, index);
        grid.appendChild(card);
    });
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

    // Determine badge
    const badge = isMatch
        ? '<span class="badge badge-success">Matched</span>'
        : '<span class="badge badge-warning">Unknown</span>';

    // Create card HTML
    card.innerHTML = `
        <div class="detection-info">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                <div class="detection-name">${personName}</div>
                ${badge}
            </div>
            
            ${personId !== 'N/A' ? `<div class="text-muted" style="font-size: 0.875rem; margin-bottom: 0.5rem;">ID: ${personId}</div>` : ''}
            
            <div class="detection-confidence">
                <span style="font-size: 0.875rem; color: var(--text-secondary);">Confidence</span>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: ${confidence * 100}%"></div>
                </div>
                <span style="font-size: 0.875rem; font-weight: 600;">${(confidence * 100).toFixed(1)}%</span>
            </div>
            
            ${occlusion > 0 ? `
                <div style="margin-top: 0.75rem; padding: 0.5rem; background: var(--bg-secondary); border-radius: 0.375rem;">
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">Estimated Occlusion</div>
                    <div style="font-weight: 600; color: var(--text-primary);">${(occlusion * 100).toFixed(0)}%</div>
                </div>
            ` : ''}
            
            ${detection.frame_number !== undefined ? `
                <div style="margin-top: 0.75rem; font-size: 0.875rem; color: var(--text-muted);">
                    Frame: ${detection.frame_number} | Time: ${formatTimestamp(detection.timestamp || 0)}
                </div>
            ` : ''}
            
            ${detection.bbox ? `
                <div style="margin-top: 0.75rem; font-size: 0.75rem; color: var(--text-muted);">
                    Position: (${detection.bbox.x}, ${detection.bbox.y})
                </div>
            ` : ''}
        </div>
    `;

    return card;
}

/**
 * Show no results message
 */
function showNoResults() {
    const grid = document.getElementById('detectionGrid');
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
