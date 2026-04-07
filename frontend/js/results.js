/**
 * TrueFace AI - Results Page Logic
 * Handles detection display and post-detection enrollment.
 */

const API_BASE = window.location.origin;
let currentEnrollmentId = null;

document.addEventListener('DOMContentLoaded', () => {
    // Auth Check
    if (typeof auth !== 'undefined') {
        auth.checkAuth();
        const user = auth.getUser();
        if (user) document.getElementById('user-display').textContent = user.readable_id;
    }

    loadResults();
    setupEnrollmentHandlers();
});

/**
 * Load and display results from sessionStorage
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
 * Display detections and visualization
 */
function displayResults(results) {
    const detections = results.detections || [];
    const totalFaces = results.total_faces || detections.length || 0;
    const matched = detections.filter(d => d.is_match).length || 0;
    const processingTime = results.processing_time?.toFixed(2) || 0;

    updateElement('totalFaces', totalFaces);
    updateElement('matchedFaces', matched);
    updateElement('processingTime', processingTime + 's');

    const img = document.getElementById('result-image');
    if (results.annotated_image && img) {
        img.src = API_BASE + results.annotated_image;
    }

    const container = document.getElementById('detections-list');
    const noResults = document.getElementById('noResults');

    if (detections.length > 0) {
        container.innerHTML = '';
        detections.forEach((det, idx) => {
            container.appendChild(createDetectionItem(det, idx));
        });
        noResults.style.display = 'none';
    } else {
        noResults.style.display = 'block';
    }
}

/**
 * Create a Premium Identification Card
 */
function createDetectionItem(det, idx) {
    const item = document.createElement('div');
    item.className = 'detection-item-premium';
    
    const isMatch = det.is_match;
    const canEnroll = !isMatch && auth.hasRole('MANAGER');
    
    // Path handling
    let faceImgUrl = 'img/placeholder-face.png';
    if (det.face_image_path) {
        faceImgUrl = det.face_image_path.startsWith('/api') 
            ? API_BASE + det.face_image_path 
            : API_BASE + '/api/file/temp/' + det.face_image_path;
    }

    item.innerHTML = `
        <img src="${faceImgUrl}" class="face-thumb-lg" onerror="this.src='https://via.placeholder.com/72?text=?'">
        <div style="flex: 1;">
            <span class="status-badge" style="background: ${isMatch ? '#000' : 'transparent'}; color: ${isMatch ? '#fff' : '#000'};">
                ${isMatch ? 'Match Verified' : 'Unknown Individual'}
            </span>
            <div style="margin-bottom: 0.25rem;">
                <span style="font-weight: 800; font-size: 1.1rem; display: block;">${det.person_name || 'System ID: Unknown'}</span>
            </div>
            <div class="text-muted" style="font-size: 0.8rem; font-family: monospace;">
                Confidence: ${(det.confidence * 100).toFixed(1)}% | 
                Ref: ${det.person_id || 'NULL'}
            </div>
        </div>
        ${canEnroll ? `
            <button class="btn btn-primary btn-enroll" data-id="${det.detection_id}" style="padding: 0.5rem 1rem;">
                Enroll Face
            </button>
        ` : ''}
    `;

    // Hook up Enroll button
    const enrollBtn = item.querySelector('.btn-enroll');
    if (enrollBtn) {
        enrollBtn.onclick = (e) => {
            e.stopPropagation();
            openEnrollModal(det.detection_id);
        };
    }

    return item;
}

/**
 * Modal Logic for Enrollment
 */
function setupEnrollmentHandlers() {
    const modal = document.getElementById('enrollment-modal');
    const cancelBtn = document.getElementById('btn-cancel-enroll');
    const confirmBtn = document.getElementById('btn-confirm-enroll');

    cancelBtn.onclick = () => {
        modal.style.display = 'none';
        currentEnrollmentId = null;
    };

    confirmBtn.onclick = async () => {
        const name = document.getElementById('modal-person-name').value.trim();
        if (!name) return alert('Please enter a name');

        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Enrolling...';

        try {
            const res = await fetch(API_BASE + '/api/face/add-from-upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    detection_id: currentEnrollmentId,
                    person_name: name
                })
            });

            const data = await res.json();
            if (res.ok) {
                alert('Success! Face enrolled as ' + data.face.person_id);
                window.location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        } catch (e) {
            alert('Server error occurred.');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Save to DB';
            modal.style.display = 'none';
        }
    };
}

function openEnrollModal(detectionId) {
    currentEnrollmentId = detectionId;
    document.getElementById('enrollment-modal').style.display = 'flex';
}

function showNoResults() {
    const noResults = document.getElementById('noResults');
    if (noResults) noResults.style.display = 'block';
}

function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}
