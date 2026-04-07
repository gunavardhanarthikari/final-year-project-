/**
 * TrueFace AI - Main JavaScript
 * Handles file uploads, API communication, and UI-RBAC integration.
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
    // 1. Mandatory Auth Check
    if (typeof auth !== 'undefined') {
        auth.checkAuth();
        updateUIForRole();
    }

    initializeUploadZones();
    loadSystemStats();
});

/**
 * Update UI elements based on user role using data-role attributes
 */
function updateUIForRole() {
    const user = auth.getUser();
    if (!user) return;

    // Display user ID
    const display = document.getElementById('user-display');
    if (display) display.textContent = user.readable_id;

    // Hide/Show based on roles
    document.querySelectorAll('[data-role]').forEach(el => {
        const requiredRole = el.getAttribute('data-role');
        if (!auth.hasRole(requiredRole)) {
            el.classList.add('hidden');
        }
    });
}

/**
 * Initialize drag-and-drop upload zones
 */
function initializeUploadZones() {
    setupUploadZone('drop-zone-image', 'file-input-image', 'image');
    setupUploadZone('drop-zone-video', 'file-input-video', 'video');
    setupDatabaseZone();
}

/**
 * Setup individual upload zone for Processing
 */
function setupUploadZone(zoneId, inputId, type) {
    const zone = document.getElementById(zoneId);
    if (!zone) return;

    const input = document.getElementById(inputId);
    const btnId = type === 'image' ? 'btn-process-image' : 'btn-process-video';
    const btn = document.getElementById(btnId);

    if (!input) return;

    zone.addEventListener('click', (e) => {
        if (e.target !== btn && e.target.tagName !== 'BUTTON') {
            input.click();
        }
    });

    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileSelect(file, zone, type);
    });

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.style.borderColor = 'black';
    });

    zone.addEventListener('dragleave', () => {
        zone.style.borderColor = 'var(--border)';
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.style.borderColor = 'var(--border)';
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file, zone, type);
    });

    if (btn) {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            processFile(type);
        });
    }
}

/**
 * Setup Database Upload Zone (Role-restricted already by HTML/CSS)
 */
function setupDatabaseZone() {
    const zone = document.getElementById('drop-zone-database');
    const input = document.getElementById('file-input-database');
    const inputsContainer = document.getElementById('database-inputs');
    const previewImg = document.getElementById('db-preview-img');
    const saveBtn = document.getElementById('btn-add-database');

    if (!zone || !input) return;

    zone.addEventListener('click', (e) => {
        if (!inputsContainer.contains(e.target)) {
            input.click();
        }
    });

    const handleDbFile = (file) => {
        if (!file.type.startsWith('image/')) {
            showNotification('Please upload an image file', 'error');
            return;
        }

        state.dbFile = file;
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

    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            const name = document.getElementById('db-person-name').value.trim();
            const msg = document.getElementById('db-status-msg');

            if (!name || !state.dbFile) {
                showNotification('Please fill all fields', 'warning');
                return;
            }

            saveBtn.disabled = true;
            saveBtn.textContent = 'Saving...';
            msg.textContent = 'Processing biometric data...';

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
                    msg.textContent = `Success: ${data.person_id}`;
                    setTimeout(() => {
                        resetDatabaseZone();
                        loadSystemStats();
                    }, 2000);
                } else {
                    throw new Error(data.error || 'Failed to add face');
                }
            } catch (error) {
                showNotification(error.message, 'error');
                msg.textContent = 'Error: ' + error.message;
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save Face';
            }
        });
    }

    function resetDatabaseZone() {
        state.dbFile = null;
        document.getElementById('db-person-name').value = '';
        inputsContainer.style.display = 'none';
        zone.querySelector('.upload-area').style.display = 'block';
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save Face';
        msg.textContent = '';
    }
}

function handleFileSelect(file, zone, type) {
    const validTypes = type === 'image'
        ? ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/webp']
        : ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/webm'];

    if (!validTypes.includes(file.type)) {
        showNotification(`Invalid ${type} format`, 'error');
        return;
    }

    if (type === 'image') state.imageFile = file;
    else state.videoFile = file;

    const container = document.getElementById(`preview-container-${type}`);
    const filename = document.getElementById(`filename-${type}`);
    const uploadArea = zone.querySelector('.upload-area');

    if (container && filename) {
        uploadArea.style.display = 'none';
        container.style.display = 'block';
        filename.textContent = file.name;
    }
}

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
        if (!response.ok) throw new Error(data.error || 'Processing failed');

        sessionStorage.setItem('detectionResults', JSON.stringify(data));
        window.location.href = 'results.html';

    } catch (error) {
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

function showProcessingOverlay(show) {
    const overlay = document.getElementById('processing-overlay');
    if (overlay) overlay.style.display = show ? 'flex' : 'none';
}

async function loadSystemStats() {
    try {
        // Need to be logged in for stats
        if (!auth.isAuthenticated()) return;
        
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

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = 'stark-box';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: black;
        color: white;
        z-index: 3000;
        font-weight: 500;
        font-size: 0.9rem;
        border: none;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    `;

    document.body.appendChild(notification);
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}
