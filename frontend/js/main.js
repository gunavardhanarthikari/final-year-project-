/**
 * TrueFace AI - Main JavaScript
 * Handles file uploads, API communication, and UI interactions
 */

// API Configuration
const API_BASE = window.location.origin;

// State Management
const state = {
    imageFile: null,
    videoFile: null,
    dbFile: null,
    processing: false
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initializeUploadZones();
    loadSystemStats();
});

/**
 * Initialize drag-and-drop upload zones
 */
function initializeUploadZones() {
    // Image upload zone
    setupUploadZone('drop-zone-image', 'file-input-image', 'image');

    // Video upload zone
    setupUploadZone('drop-zone-video', 'file-input-video', 'video');

    // Database upload zone
    setupDatabaseZone();
}

/**
 * Setup individual upload zone for Processing
 */
function setupUploadZone(zoneId, inputId, type) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const btnId = type === 'image' ? 'btn-process-image' : 'btn-process-video';
    const btn = document.getElementById(btnId);

    if (!zone || !input) return;

    // Click to upload
    zone.addEventListener('click', (e) => {
        if (e.target !== btn && e.target.tagName !== 'BUTTON') {
            input.click();
        }
    });

    // File selection
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileSelect(file, zone, type);
    });

    // Drag and drop
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file, zone, type);
    });

    // Process Button
    if (btn) {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            processFile(type);
        });
    }
}

/**
 * Setup Database Upload Zone
 */
function setupDatabaseZone() {
    const zone = document.getElementById('drop-zone-database');
    const input = document.getElementById('file-input-database');
    const inputsContainer = document.getElementById('database-inputs');
    const previewImg = document.getElementById('db-preview-img');
    const saveBtn = document.getElementById('btn-add-database');

    if (!zone || !input) return;

    // Click to upload (only if not clicking inputs)
    zone.addEventListener('click', (e) => {
        if (!inputsContainer.contains(e.target)) {
            input.click();
        }
    });

    // Handle File
    const handleDbFile = (file) => {
        if (!file.type.startsWith('image/')) {
            showNotification('Please upload an image file', 'error');
            return;
        }

        state.dbFile = file;

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            inputsContainer.style.display = 'block';
            zone.querySelector('.upload-area').style.display = 'none';
        };
        reader.readAsDataURL(file);
    };

    input.addEventListener('change', (e) => {
        if (e.target.files[0]) handleDbFile(e.target.files[0]);
    });

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files[0]) handleDbFile(e.dataTransfer.files[0]);
    });

    // Save Button
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const name = document.getElementById('db-person-name').value.trim();
            const msg = document.getElementById('db-status-msg');

            if (!name || !state.dbFile) {
                showNotification('Please fill all fields', 'warning');
                return;
            }

            // Disable button
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<ion-icon name="hourglass-outline"></ion-icon> Saving...';
            msg.textContent = 'Training model... This takes a moment.';

            try {
                const formData = new FormData();
                formData.append('file', state.dbFile);
                formData.append('person_name', name);

                const response = await fetch(API_BASE + '/api/face/add', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    showNotification('Face added successfully!', 'success');
                    msg.textContent = `Success! Added ID: ${data.person_id}`;
                    msg.style.color = 'var(--success)';

                    // Reset after 2 seconds
                    setTimeout(() => {
                        resetDatabaseZone();
                        loadSystemStats(); // Refresh stats
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Failed to add face');
                }
            } catch (error) {
                console.error(error);
                showNotification(error.message, 'error');
                msg.textContent = 'Error: ' + error.message;
                msg.style.color = 'var(--error)';
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<ion-icon name="save-outline"></ion-icon> Save Face';
            }
        });
    }

    function resetDatabaseZone() {
        state.dbFile = null;
        document.getElementById('db-person-name').value = '';
        inputsContainer.style.display = 'none';
        zone.querySelector('.upload-area').style.display = 'block';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<ion-icon name="save-outline"></ion-icon> Save Face';
        msg.textContent = '';
    }
}

/**
 * Handle file selection for processing
 */
function handleFileSelect(file, zone, type) {
    // Validate file type
    const validTypes = type === 'image'
        ? ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/webp']
        : ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];

    if (!validTypes.includes(file.type)) {
        showNotification(`Invalid ${type} format`, 'error');
        return;
    }

    // Update state
    if (type === 'image') {
        state.imageFile = file;
    } else {
        state.videoFile = file;
    }

    // Show Preview
    const container = document.getElementById(`preview-container-${type}`);
    const filename = document.getElementById(`filename-${type}`);
    const uploadArea = zone.querySelector('.upload-area');

    if (container && filename) {
        uploadArea.style.display = 'none';
        container.style.display = 'block';
        filename.textContent = file.name;
    }
}

/**
 * Upload and process file
 */
async function processFile(type) {
    if (state.processing) return;

    const file = type === 'image' ? state.imageFile : state.videoFile;
    if (!file) return;

    state.processing = true;
    showProcessingOverlay(true);

    try {
        const formData = new FormData();
        formData.append('file', file);

        const endpoint = type === 'image' ? '/api/upload/image' : '/api/upload/video';

        const response = await fetch(API_BASE + endpoint, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Processing failed');
        }

        // Store results and redirect
        sessionStorage.setItem('detectionResults', JSON.stringify(data));
        window.location.href = 'results.html';

    } catch (error) {
        console.error('Upload error:', error);
        showProcessingOverlay(false);
        showNotification(error.message || 'Processing failed', 'error');

        // Reset UI
        const zone = document.getElementById(`drop-zone-${type}`);
        const container = document.getElementById(`preview-container-${type}`);
        zone.querySelector('.upload-area').style.display = 'block';
        container.style.display = 'none';
    } finally {
        state.processing = false;
    }
}

/**
 * Show/Hide Overlay
 */
function showProcessingOverlay(show) {
    const overlay = document.getElementById('processing-overlay');
    if (overlay) overlay.style.display = show ? 'flex' : 'none';
}

/**
 * Load system statistics
 */
async function loadSystemStats() {
    try {
        const response = await fetch(API_BASE + '/api/stats');
        const data = await response.json();

        if (data.success) {
            const stats = data.stats;
            updateElement('stat-faces', stats.total_stored_faces);
            updateElement('stat-detections', stats.total_detections);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

function updateElement(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `glass-panel`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'error' ? 'rgba(239, 68, 68, 0.9)' : type === 'success' ? 'rgba(16, 185, 129, 0.9)' : 'rgba(59, 130, 246, 0.9)'};
        color: white;
        border-radius: 0.5rem;
        z-index: 3000;
        animation: fadeIn 0.3s ease-out;
        border: 1px solid rgba(255,255,255,0.2);
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
