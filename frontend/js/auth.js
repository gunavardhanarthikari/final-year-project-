/**
 * TrueFace AI Authentication Module
 * Handles login, session management, and role access.
 */

const auth = {
    // API Endpoints
    LOGIN_URL: '/api/login',
    LOGOUT_URL: '/api/logout',
    STATUS_URL: '/api/auth/status',

    /**
     * Login a user and store session
     */
    async login(username, password) {
        try {
            const response = await fetch(this.LOGIN_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                localStorage.setItem('tf_user', JSON.stringify(data.user));
                return true;
            }
            return false;
        } catch (error) {
            console.error('Login error:', error);
            return false;
        }
    },

    /**
     * Logout and clear session
     */
    async logout() {
        try {
            await fetch(this.LOGOUT_URL, { method: 'POST' });
        } catch (e) { }
        localStorage.removeItem('tf_user');
        window.location.href = 'login.html';
    },

    /**
     * Check if user is authenticated via localStorage
     */
    isAuthenticated() {
        return !!localStorage.getItem('tf_user');
    },

    /**
     * Get current user object
     */
    getUser() {
        const user = localStorage.getItem('tf_user');
        return user ? JSON.parse(user) : null;
    },

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        const user = this.getUser();
        if (!user) return false;
        
        if (role === 'ADMIN') return user.role === 'ADMIN';
        if (role === 'MANAGER') return ['ADMIN', 'MANAGER'].includes(user.role);
        return true; // VIEWER
    },

    /**
     * Redirect to login if not authenticated
     */
    checkAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = 'login.html';
        }
    }
};

// Initialize if on a page (but not the login page)
if (!window.location.pathname.endsWith('login.html')) {
    // We can't automatically redirect here because it might block main script loads,
    // but the individual pages will call auth.checkAuth()
}
