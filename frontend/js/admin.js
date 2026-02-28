/**
 * Admin Page JavaScript
 * Manage face database - add and delete faces
 */

const API_BASE = window.location.origin;
let faceToDelete = null;

document.addEventListener('DOMContentLoaded', () => {
    setupUploadZone();
    setupForm();
    setupDeleteModal();
    loadFaces();
});

/**
 * Setup face image upload zone
 */
function setupUploadZone() {
    const zone = document.getElementById('faceUploadZone');
    const input = document.getElementById('faceImageInput');

    if (!zone || !input) return;

    // Click to upload
    zone.addEventListener('click', () => input.click());

    // File selection
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            zone.classList.add('has-file');
            zone.querySelector('p').textContent = `Selected: ${file.name}`;
        }
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
        if (file && file.type.startsWith('image/')) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            input.files = dataTransfer.files;

            zone.classList.add('has-file');
            zone.querySelector('p').textContent = `Selected: ${file.name}`;
        }
    });
}

/**
 * Setup add face form
 */
function setupForm() {
    const form = document.getElementById('addFaceForm');

    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const personId = document.getElementById('personId').value.trim();
        const personName = document.getElementById('personName').value.trim();
        const fileInput = document.getElementById('faceImageInput');
        const file = fileInput.files[0];

        if (!personId || !personName || !file) {
            showNotification('Please fill all fields and select an image', 'error');
            return;
        }

        // Create form data
        const formData = new FormData();
        formData.append('person_id', personId);
        formData.append('person_name', personName);
        formData.append('file', file);

        try {
            showNotification('Adding face to database...', 'info');

            const response = await fetch(API_BASE + '/api/face/add', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to add face');
            }

            showNotification('Face added successfully!', 'success');

            // Reset form
            form.reset();
            const zone = document.getElementById('faceUploadZone');
            zone.classList.remove('has-file');
            zone.querySelector('p').textContent = 'Click or drag face image here';

            // Reload faces
            loadFaces();

        } catch (error) {
            console.error('Error adding face:', error);
            showNotification(error.message || 'Failed to add face', 'error');
        }
    });
}

/**
 * Setup delete confirmation modal
 */
function setupDeleteModal() {
    const modal = document.getElementById('deleteModal');
    const cancelBtn = document.getElementById('cancelDeleteBtn');
    const confirmBtn = document.getElementById('confirmDeleteBtn');

    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.classList.remove('active');
            faceToDelete = null;
        });
    }

    if (confirmBtn) {
        confirmBtn.addEventListener('click', async () => {
            if (faceToDelete) {
                await deleteFace(faceToDelete);
                modal.classList.remove('active');
                faceToDelete = null;
            }
        });
    }
}

/**
 * Load all faces from database
 */
async function loadFaces() {
    try {
        const response = await fetch(API_BASE + '/api/face/list');
        const data = await response.json();

        if (data.success) {
            displayFaces(data.faces || []);
            updateElement('totalStoredFaces', data.total || 0);
        } else {
            showNoFaces();
        }
    } catch (error) {
        console.error('Error loading faces:', error);
        showNoFaces();
    } finally {
        hideLoading();
    }
}

/**
 * Display face cards
 */
function displayFaces(faces) {
    const grid = document.getElementById('faceGrid');
    const noFaces = document.getElementById('noFaces');

    if (!grid) return;

    if (faces.length === 0) {
        showNoFaces();
        return;
    }

    grid.innerHTML = '';
    noFaces.style.display = 'none';

    faces.forEach((face, index) => {
        const card = createFaceCard(face, index);
        grid.appendChild(card);
    });
}

/**
 * Create face card element
 */
function createFaceCard(face, index) {
    const card = document.createElement('div');
    card.className = 'detection-card fade-in';
    card.style.animationDelay = `${index * 0.05}s`;

    const createdDate = new Date(face.created_at);
    const formattedDate = createdDate.toLocaleDateString();

    card.innerHTML = `
        <div class="detection-info">
            <div class="detection-name" style="margin-bottom: 0.5rem;">${face.person_name}</div>
            <div class="text-muted" style="font-size: 0.875rem; margin-bottom: 1rem;">ID: ${face.person_id}</div>
            
            <div style="padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.375rem; margin-bottom: 1rem;">
                <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">Added</div>
                <div style="font-weight: 600;">${formattedDate}</div>
            </div>
            
            <button class="btn btn-secondary delete-btn" data-id="${face.id}" style="background: var(--error-color); color: white; width: 100%;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3 6 5 6 21 6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>Delete</span>
            </button>
        </div>
    `;

    // Add delete button listener
    const deleteBtn = card.querySelector('.delete-btn');
    deleteBtn.addEventListener('click', () => {
        faceToDelete = face.id;
        document.getElementById('deleteModal').classList.add('active');
    });

    return card;
}

/**
 * Delete face from database
 */
async function deleteFace(faceId) {
    try {
        showNotification('Deleting face...', 'info');

        const response = await fetch(API_BASE + `/api/face/${faceId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to delete face');
        }

        showNotification('Face deleted successfully!', 'success');
        loadFaces();

    } catch (error) {
        console.error('Error deleting face:', error);
        showNotification(error.message || 'Failed to delete face', 'error');
    }
}

/**
 * Show no faces message
 */
function showNoFaces() {
    const grid = document.getElementById('faceGrid');
    const noFaces = document.getElementById('noFaces');

    if (grid) grid.innerHTML = '';
    if (noFaces) noFaces.style.display = 'block';
    updateElement('totalStoredFaces', 0);
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) loading.style.display = 'none';
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 3000;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
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
