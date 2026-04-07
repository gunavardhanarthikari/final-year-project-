/**
 * TrueFace AI - Admin Page Logic
 * Handles system analytics, user management, and face database.
 */

const API_BASE = window.location.origin;
let deleteTarget = null;
let deleteType = null; // 'user' or 'face'

document.addEventListener('DOMContentLoaded', () => {
    // Auth Check
    if (typeof auth !== 'undefined') {
        auth.checkAuth();
        if (!auth.hasRole('ADMIN')) {
            window.location.href = 'index.html';
            return;
        }
        const user = auth.getUser();
        if (user) document.getElementById('user-display').textContent = user.readable_id;
    }

    loadDashboard();
    loadUsers();
    loadFaces();
    setupForms();
    setupModal();
    setupAdminTabs();
});

/**
 * Tab Switching Logic
 */
function setupAdminTabs() {
    const tabUsersBtn = document.getElementById('tab-users-btn');
    const tabDbBtn = document.getElementById('tab-db-btn');
    const secUsers = document.getElementById('sec-users');
    const secDatabase = document.getElementById('sec-database');

    tabUsersBtn.onclick = () => {
        tabUsersBtn.classList.add('active');
        tabDbBtn.classList.remove('active');
        secUsers.classList.remove('hidden');
        secDatabase.classList.add('hidden');
    };

    tabDbBtn.onclick = () => {
        tabDbBtn.classList.add('active');
        tabUsersBtn.classList.remove('active');
        secDatabase.classList.remove('hidden');
        secUsers.classList.add('hidden');
    };
}

/**
 * Load System Dashboard Statistics
 */
async function loadDashboard() {
    try {
        const res = await fetch(API_BASE + '/api/admin/dashboard');
        const data = await res.json();
        if (data.success) {
            document.getElementById('dash-total-detections').textContent = data.stats.total_detections;
            document.getElementById('dash-match-rate').textContent = data.stats.match_rate + '%';
            document.getElementById('dash-active-users').textContent = data.stats.user_counts.ADMIN + data.stats.user_counts.MANAGER + data.stats.user_counts.VIEWER;
        }
    } catch (e) {
        console.error('Stats error:', e);
    }
}

/**
 * Load and List Users
 */
async function loadUsers() {
    try {
        const res = await fetch(API_BASE + '/api/admin/users');
        const data = await res.json();
        if (data.success) {
            const tbody = document.getElementById('users-table-body');
            tbody.innerHTML = '';
            data.users.forEach(user => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 700;">${user.readable_id}</td>
                    <td>${user.full_name}</td>
                    <td><span style="font-size: 0.7rem; background: #eee; padding: 2px 6px;">${user.role}</span></td>
                    <td>
                        <button class="btn btn-secondary" style="padding: 0.2rem 0.6rem; font-size: 0.7rem;" onclick="confirmDelete('${user.id}', 'user')">Deactivate</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error('Load users error:', e);
    }
}

/**
 * Load Registered Faces
 */
async function loadFaces() {
    try {
        const res = await fetch(API_BASE + '/api/face/list');
        const data = await res.json();
        const container = document.getElementById('faces-list');
        container.innerHTML = '';

        if (data.success && data.faces.length > 0) {
            data.faces.forEach(face => {
                const item = document.createElement('div');
                item.className = 'detection-item';
                item.style.padding = '0.5rem 0';
                item.innerHTML = `
                    <div style="flex: 1;">
                        <span style="font-weight: 700; font-size: 0.9rem;">${face.person_name}</span>
                        <div class="text-muted" style="font-size: 0.7rem;">${face.person_id}</div>
                    </div>
                    <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.65rem;" onclick="confirmDelete('${face.id}', 'face')">Remove</button>
                `;
                container.appendChild(item);
            });
        } else {
            container.innerHTML = '<p class="text-muted" style="font-size: 0.8rem;">No faces registered.</p>';
        }
    } catch (e) {
        console.error('Load faces error:', e);
    }
}

/**
 * Modal Handling
 */
function setupModal() {
    const modal = document.getElementById('confirm-modal');
    document.getElementById('modal-cancel').onclick = () => modal.style.display = 'none';

    document.getElementById('modal-confirm').onclick = async () => {
        const endpoint = deleteType === 'user' ? `/api/admin/user/${deleteTarget}` : `/api/face/${deleteTarget}`;
        try {
            const res = await fetch(API_BASE + endpoint, { method: 'DELETE' });
            if (res.ok) {
                modal.style.display = 'none';
                if (deleteType === 'user') loadUsers();
                else loadFaces();
            } else {
                const d = await res.json();
                alert(d.error || 'Operation failed');
            }
        } catch (e) {
            alert('Server error');
        }
    };
}

function confirmDelete(id, type) {
    deleteTarget = id;
    deleteType = type;
    document.getElementById('modal-title').textContent = type === 'user' ? 'Deactivate User' : 'Delete Face';
    document.getElementById('modal-text').textContent = type === 'user'
        ? 'This user will no longer be able to login.'
        : 'This will permanently remove the person from the AI database.';
    document.getElementById('confirm-modal').style.display = 'flex';
}

/**
 * Form Submission Handling
 */
/**
 * Combined Modal Form Handling
 */
function setupForms() {
    const formModal = document.getElementById('form-modal');
    const dynamicForm = document.getElementById('dynamic-form');
    const formTitle = document.getElementById('form-title');
    const formSubmit = document.getElementById('form-submit');
    const formCancel = document.getElementById('form-cancel');

    // Show Create User Modal
    document.getElementById('add-user-btn').onclick = () => {
        formTitle.innerText = "Initialize Personnel Account";
        dynamicForm.innerHTML = `
            <div class="form-group">
                <label>Full Legal Name</label>
                <input id="modal-user-name" class="form-input" placeholder="e.g. Sgt. Miller" required>
            </div>
            <div class="form-group">
                <label>Institutional Email</label>
                <input type="email" id="modal-user-email" class="form-input" placeholder="e.g. miller@trueface.ai" required>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" id="modal-user-password" class="form-input" placeholder="Minimum 8 characters" required>
            </div>
            <div class="form-group">
                <label>Security Authorization Role</label>
                <select id="modal-user-role" class="form-input">
                    <option value="VIEWER">VIEWER (Basic Access)</option>
                    <option value="MANAGER">MANAGER (Enrollment Privileges)</option>
                    <option value="ADMIN">ADMIN (Full System Control)</option>
                </select>
            </div>
        `;
        formModal.style.display = 'flex';
    };

    // Show Add Face Modal
    document.getElementById('add-face-btn').onclick = () => {
        formTitle.innerText = "Register Biometric Identity";
        dynamicForm.innerHTML = `
            <div class="form-group">
                <label>Subject Facial Capture</label>
                <input type="file" id="modal-face-image" accept="image/*" class="form-input" style="padding: 0.5rem;">
            </div>
            <div class="form-group">
                <label>Subject Full Name</label>
                <input id="modal-face-name" class="form-input" placeholder="Enter name for AI mapping">
            </div>
        `;
        formModal.style.display = 'flex';
    };

    // Close Modal
    formCancel.onclick = () => formModal.style.display = 'none';

    // Global Submit Logic
    formSubmit.onclick = async () => {
        const isUserForm = formTitle.innerText.includes("Personnel");
        formSubmit.disabled = true;
        formSubmit.innerText = "Processing...";

        try {
            if (isUserForm) {
                // User Creation Logic
                const name = document.getElementById('modal-user-name').value;
                const email = document.getElementById('modal-user-email').value;
                const password = document.getElementById('modal-user-password').value;
                const role = document.getElementById('modal-user-role').value;

                if (!name || !email || !password) throw new Error("Missing required fields");

                const res = await fetch(API_BASE + '/api/admin/user/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ full_name: name, email: email, password: password, role: role })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || "Creation failed");
                alert('Account generated successfully.');
            } else {
                // Face Addition Logic
                const name = document.getElementById('modal-face-name').value;
                const fileInput = document.getElementById('modal-face-image');
                if (!name || !fileInput.files[0]) throw new Error("Name and photo identification required");

                const formData = new FormData();
                formData.append('person_name', name);
                formData.append('file', fileInput.files[0]);

                const res = await fetch(API_BASE + '/api/face/add', { method: 'POST', body: formData });
                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.error || "Face upload failed");
                }
                alert('Subject identity registered in database.');
            }

            // Success Cleanup
            formModal.style.display = 'none';
            loadUsers();
            loadFaces();
            loadDashboard();
        } catch (err) {
            alert(err.message);
        } finally {
            formSubmit.disabled = false;
            formSubmit.innerText = "Submit";
        }
    };
}
