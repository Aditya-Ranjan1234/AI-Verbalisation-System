// API Configuration
const API_BASE = '';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initEventListeners();
    if (authToken) {
        loadUserData();
    }
});

// Event Listeners
function initEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            if (!e.target.hasAttribute('target')) {
                e.preventDefault();
                const target = e.target.getAttribute('href').substring(1);
                showSection(target);
            }
        });
    });

    // Auth buttons
    document.getElementById('showLoginBtn')?.addEventListener('click', () => showModal('loginModal'));
    document.getElementById('showRegisterBtn')?.addEventListener('click', () => showModal('registerModal'));
    document.getElementById('logoutBtn')?.addEventListener('click', logout);
    document.getElementById('getStartedBtn')?.addEventListener('click', () => {
        if (authToken) {
            showSection('trips');
        } else {
            showModal('loginModal');
        }
    });

    // Modal switches
    document.getElementById('switchToRegister')?.addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('loginModal');
        showModal('registerModal');
    });
    document.getElementById('switchToLogin')?.addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('registerModal');
        showModal('loginModal');
    });

    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modalId = e.target.getAttribute('data-modal');
            hideModal(modalId);
        });
    });

    // Forms
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.getElementById('createTripBtn')?.addEventListener('click', () => showModal('createTripModal'));
    document.getElementById('createTripForm')?.addEventListener('submit', handleCreateTrip);
    document.getElementById('createZoneBtn')?.addEventListener('click', () => showModal('createZoneModal'));
    document.getElementById('createZoneForm')?.addEventListener('submit', handleCreateZone);

    // Close modals on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// Authentication
function initAuth() {
    if (authToken) {
        document.getElementById('navAuth').style.display = 'none';
        document.getElementById('navUser').style.display = 'flex';
    } else {
        document.getElementById('navAuth').style.display = 'flex';
        document.getElementById('navUser').style.display = 'none';
    }
}

async function loadUserData() {
    try {
        const response = await fetch('/auth/me', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('userName').textContent = currentUser.username;
            loadDashboardData();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Error loading user data:', error);
        logout();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            hideModal('loginModal');
            showToast('Login successful!', 'success');
            initAuth();
            loadUserData();
            showSection('trips');
        } else {
            const error = await response.json();
            showError('loginError', error.detail || 'Login failed');
        }
    } catch (error) {
        showError('loginError', 'Network error. Please try again.');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const role = document.getElementById('regRole').value;

    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password, role })
        });

        if (response.ok) {
            showToast('Registration successful! Please login.', 'success');
            hideModal('registerModal');
            showModal('loginModal');
            document.getElementById('loginUsername').value = username;
        } else {
            const error = await response.json();
            showError('registerError', error.detail || 'Registration failed');
        }
    } catch (error) {
        showError('registerError', 'Network error. Please try again.');
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    initAuth();
    showSection('home');
    showToast('Logged out successfully', 'success');
}

// Trip Management
async function handleCreateTrip(e) {
    e.preventDefault();

    const tripData = {
        start_lat: parseFloat(document.getElementById('startLat').value),
        start_lon: parseFloat(document.getElementById('startLon').value),
        end_lat: parseFloat(document.getElementById('endLat').value),
        end_lon: parseFloat(document.getElementById('endLon').value),
        start_time: document.getElementById('startTime').value,
        end_time: document.getElementById('endTime').value,
        route_points: []
    };

    try {
        const response = await fetch('/trips/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(tripData)
        });

        if (response.ok) {
            showToast('Trip created successfully!', 'success');
            hideModal('createTripModal');
            document.getElementById('createTripForm').reset();
            loadTrips();
        } else {
            const error = await response.json();
            showError('createTripError', error.detail?.[0]?.msg || 'Failed to create trip');
        }
    } catch (error) {
        showError('createTripError', 'Network error. Please try again.');
    }
}

async function loadTrips() {
    try {
        const response = await fetch('/trips/', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const trips = await response.json();
            displayTrips(trips);
        }
    } catch (error) {
        console.error('Error loading trips:', error);
    }
}

function displayTrips(trips) {
    const grid = document.getElementById('tripsGrid');
    
    if (trips.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                    <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <p>No trips yet. Create your first trip!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = trips.map(trip => `
        <div class="trip-card">
            <div class="trip-header">
                <div class="trip-id">Trip #${trip.trip_id}</div>
                <div class="trip-badge">Active</div>
            </div>
            <div class="trip-info">
                <div class="info-row">
                    <span class="info-label">Start Time</span>
                    <span class="info-value">${new Date(trip.start_time).toLocaleDateString()}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">End Time</span>
                    <span class="info-value">${new Date(trip.end_time).toLocaleDateString()}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Duration</span>
                    <span class="info-value">${calculateDuration(trip.start_time, trip.end_time)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Zone Management
async function handleCreateZone(e) {
    e.preventDefault();

    const name = document.getElementById('zoneName').value;
    const description = document.getElementById('zoneDescription').value;
    const boundaryText = document.getElementById('zoneBoundary').value;

    try {
        const boundary = JSON.parse(boundaryText);
        
        const response = await fetch('/config/zones', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ name, description, boundary })
        });

        if (response.ok) {
            showToast('Zone created successfully!', 'success');
            hideModal('createZoneModal');
            document.getElementById('createZoneForm').reset();
            loadZones();
        } else {
            const error = await response.json();
            showError('createZoneError', error.detail || 'Failed to create zone');
        }
    } catch (error) {
        showError('createZoneError', 'Invalid JSON format for boundary coordinates');
    }
}

async function loadZones() {
    try {
        const response = await fetch('/config/zones', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const zones = await response.json();
            displayZones(zones);
        }
    } catch (error) {
        console.error('Error loading zones:', error);
    }
}

function displayZones(zones) {
    const grid = document.getElementById('zonesGrid');
    
    if (zones.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                </svg>
                <p>No zones configured. Create your first zone!</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = zones.map(zone => `
        <div class="zone-card">
            <div class="zone-header">
                <div class="zone-name">${zone.name}</div>
            </div>
            <div class="zone-info">
                ${zone.description ? `<p style="margin-top: 1rem; color: var(--gray);">${zone.description}</p>` : ''}
                <div class="info-row" style="margin-top: 1rem;">
                    <span class="info-label">Created</span>
                    <span class="info-value">${new Date(zone.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Dashboard Data
async function loadDashboardData() {
    try {
        const [tripsResponse, zonesResponse] = await Promise.all([
            fetch('/trips/', { headers: { 'Authorization': `Bearer ${authToken}` } }),
            fetch('/config/zones', { headers: { 'Authorization': `Bearer ${authToken}` } })
        ]);

        if (tripsResponse.ok) {
            const trips = await tripsResponse.json();
            document.getElementById('totalTrips').textContent = trips.length;
        }

        if (zonesResponse.ok) {
            const zones = await zonesResponse.json();
            document.getElementById('totalZones').textContent = zones.length;
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// UI Helpers
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.style.display = 'none';
    });
    
    document.querySelector('.hero').style.display = sectionId === 'home' ? 'block' : 'none';
    
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
        
        if (sectionId === 'trips') loadTrips();
        if (sectionId === 'zones') loadZones();
    }

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${sectionId}`) {
            link.classList.add('active');
        }
    });
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function showError(errorId, message) {
    const errorDiv = document.getElementById(errorId);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.add('active');
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} active`;
    
    setTimeout(() => {
        toast.classList.remove('active');
    }, 3000);
}

function calculateDuration(start, end) {
    const diff = new Date(end) - new Date(start);
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
}
