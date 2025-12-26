// API Configuration
const API_BASE = '';
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let currentTripId = null; // Store current trip ID for navigation
let navMap = null; // Store navigation map instance
let routingControl = null; // Store routing control instance

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    initEventListeners();
    initMap(); // Initialize map
    if (authToken) {
        loadUserData();
    }
    
    // Add new event listeners
    const speakBtn = document.getElementById('speakStoryBtn');
    if (speakBtn) speakBtn.addEventListener('click', speakStory);
    
    const navBtn = document.getElementById('startNavBtn');
    if (navBtn) navBtn.addEventListener('click', startNavigation);
});

let map;
let startMarker;
let endMarker;

function initMap() {
    // Default to a central location (e.g., London or User's location if available)
    map = L.map('map').setView([51.505, -0.09], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', function(e) {
        // Check if create trip modal is open by checking visibility of map container parent
        const modal = document.getElementById('createTripModal');
        if (!modal.classList.contains('active')) return;

        const mode = document.querySelector('input[name="mapMode"]:checked').value;
        const lat = e.latlng.lat.toFixed(4);
        const lng = e.latlng.lng.toFixed(4);

        if (mode === 'start') {
            document.getElementById('startLat').value = lat;
            document.getElementById('startLon').value = lng;
            
            if (startMarker) map.removeLayer(startMarker);
            startMarker = L.marker([lat, lng], {title: "Start"}).addTo(map);
        } else {
            document.getElementById('endLat').value = lat;
            document.getElementById('endLon').value = lng;
            
            if (endMarker) map.removeLayer(endMarker);
            endMarker = L.marker([lat, lng], {title: "End"}).addTo(map);
        }
    });
}

function initEventListeners() {
    // Navigation Links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                const sectionId = link.getAttribute('href').substring(1);
                showSection(sectionId);
            }
        });
    });

    // Modals
    document.querySelectorAll('[data-modal]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-modal');
            hideModal(modalId);
        });
    });

    document.getElementById('showLoginBtn').addEventListener('click', () => showModal('loginModal'));
    document.getElementById('showRegisterBtn').addEventListener('click', () => showModal('registerModal'));
    document.getElementById('createTripBtn').addEventListener('click', () => {
        showModal('createTripModal');
        setTimeout(() => map.invalidateSize(), 100); // Fix map render
    });
    document.getElementById('createZoneBtn').addEventListener('click', () => showModal('createZoneModal'));
    
    document.getElementById('switchToRegister').addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('loginModal');
        showModal('registerModal');
    });
    
    document.getElementById('switchToLogin').addEventListener('click', (e) => {
        e.preventDefault();
        hideModal('registerModal');
        showModal('loginModal');
    });

    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('getStartedBtn').addEventListener('click', () => {
        if (authToken) {
            showSection('trips');
        } else {
            showModal('registerModal');
        }
    });

    // Forms
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);
    document.getElementById('createTripForm').addEventListener('submit', handleCreateTrip);
    document.getElementById('createZoneForm').addEventListener('submit', handleCreateZone);
}

// Authentication
function initAuth() {
    const navUser = document.getElementById('navUser');
    const navAuth = document.getElementById('navAuth');
    
    if (authToken) {
        navUser.style.display = 'flex';
        navAuth.style.display = 'none';
        showSection('trips');
    } else {
        navUser.style.display = 'none';
        navAuth.style.display = 'flex';
        showSection('home');
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    const errorDiv = document.getElementById('loginError');

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/auth/token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            hideModal('loginModal');
            document.getElementById('loginForm').reset();
            loadUserData();
            initAuth();
            showToast('Login successful!');
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Login failed';
            errorDiv.classList.add('active');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error occurred';
        errorDiv.classList.add('active');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const role = document.getElementById('regRole').value;
    const errorDiv = document.getElementById('registerError');

    try {
        const response = await fetch('/auth/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password, role })
        });

        if (response.ok) {
            // Auto login after register
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const loginResponse = await fetch('/auth/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (loginResponse.ok) {
                const data = await loginResponse.json();
                authToken = data.access_token;
                localStorage.setItem('authToken', authToken);
                hideModal('registerModal');
                document.getElementById('registerForm').reset();
                loadUserData();
                initAuth();
                showToast('Registration successful!');
            }
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Registration failed';
            errorDiv.classList.add('active');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error occurred';
        errorDiv.classList.add('active');
    }
}

function handleLogout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    initAuth();
    showToast('Logged out successfully');
}

async function loadUserData() {
    try {
        const response = await fetch('/users/me', {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (response.ok) {
            currentUser = await response.json();
            document.getElementById('userName').textContent = currentUser.username;
            loadTrips();
            loadDashboardData();
        } else {
            handleLogout(); // Token invalid
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}

// Trip Management
async function handleCreateTrip(e) {
    e.preventDefault();
    
    const startLat = parseFloat(document.getElementById('startLat').value);
    const startLon = parseFloat(document.getElementById('startLon').value);
    const endLat = parseFloat(document.getElementById('endLat').value);
    const endLon = parseFloat(document.getElementById('endLon').value);
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;

    try {
        const response = await fetch('/trips/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                start_lat: startLat,
                start_lon: startLon,
                end_lat: endLat,
                end_lon: endLon,
                start_time: startTime,
                end_time: endTime
            })
        });

        if (response.ok) {
            showToast('Trip created successfully!');
            hideModal('createTripModal');
            document.getElementById('createTripForm').reset();
            loadTrips();
            loadDashboardData();
        } else {
            const error = await response.json();
            showError('createTripError', error.detail || 'Failed to create trip');
        }
    } catch (error) {
        showError('createTripError', 'Network error occurred');
    }
}

async function loadTrips() {
    try {
        const response = await fetch('/trips/', {
            headers: { 'Authorization': `Bearer ${authToken}` }
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
                <button onclick="verbalizeTrip(${trip.trip_id})" class="btn btn-outline btn-block" style="margin-top: 1rem; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    Verbalize Trip
                </button>
            </div>
        </div>
    `).join('');
}

// Verbalization
async function verbalizeTrip(tripId) {
    currentTripId = tripId; // Store for navigation
    showModal('storyModal');
    document.getElementById('storyLoader').style.display = 'block';
    document.getElementById('storyText').innerHTML = '';
    document.getElementById('storyLocations').innerHTML = '';
    
    // Reset Navigation UI
    document.getElementById('navContainer').style.display = 'none';
    if (navMap) {
        navMap.remove();
        navMap = null;
    }
    document.getElementById('navMap').innerHTML = '';

    try {
        const response = await fetch(`/trips/${tripId}/verbalize`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('storyText').innerHTML = `<p>${data.story}</p>`;
            document.getElementById('storyLocations').innerHTML = `
                <strong>Start:</strong> ${data.start_address}<br>
                <strong>End:</strong> ${data.end_address}
            `;
        } else {
            const error = await response.json();
            document.getElementById('storyText').innerHTML = `<p style="color: var(--danger)">${error.detail || 'Failed to generate story'}</p>`;
        }
    } catch (error) {
        document.getElementById('storyText').innerHTML = `<p style="color: var(--danger)">Network error. Please try again.</p>`;
    } finally {
        document.getElementById('storyLoader').style.display = 'none';
    }
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

// Text-to-Speech
function speakStory() {
    const text = document.getElementById('storyText').innerText;
    if (!text) return;

    // Cancel any current speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    
    // Try to select a good English voice
    const voices = window.speechSynthesis.getVoices();
    const englishVoice = voices.find(v => v.lang.includes('en-') && v.name.includes('Google')) || voices.find(v => v.lang.includes('en'));
    if (englishVoice) {
        utterance.voice = englishVoice;
    }

    window.speechSynthesis.speak(utterance);
}

// Live Navigation
async function startNavigation() {
    if (!currentTripId) return;
    
    const navContainer = document.getElementById('navContainer');
    navContainer.style.display = 'block';
    
    // fetch trip details to get destination coordinates
    try {
        const response = await fetch(`/trips/${currentTripId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch trip details');
        
        const trip = await response.json();
        const destLat = trip.end_lat;
        const destLon = trip.end_lon;
        
        if (navMap) {
            navMap.remove();
        }
        
        // Initialize Map
        navMap = L.map('navMap').setView([destLat, destLon], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(navMap);
        
        // Get Current Location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLat = position.coords.latitude;
                    const userLon = position.coords.longitude;
                    
                    // Start Routing
                    routingControl = L.Routing.control({
                        waypoints: [
                            L.latLng(userLat, userLon),
                            L.latLng(destLat, destLon)
                        ],
                        routeWhileDragging: false,
                        showAlternatives: true,
                        fitSelectedRoutes: true,
                        lineOptions: {
                            styles: [{color: '#6366f1', opacity: 0.8, weight: 6}]
                        }
                    }).addTo(navMap);
                    
                    document.getElementById('navStatus').innerText = "Navigation Started. Follow the route.";
                    
                    // Speak Instructions
                    routingControl.on('routesfound', function(e) {
                        const routes = e.routes;
                        const summary = routes[0].summary;
                        const firstInstruction = routes[0].instructions[0];
                        
                        // Speak summary
                        const speech = `Navigation started. Distance is ${(summary.totalDistance / 1000).toFixed(1)} kilometers. ${firstInstruction.text}`;
                        
                        // Speak
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance(speech);
                        window.speechSynthesis.speak(utterance);
                    });
                },
                (error) => {
                    showError('navStatus', "Error getting location: " + error.message);
                }
            );
        } else {
            showError('navStatus', "Geolocation is not supported by this browser.");
        }
        
    } catch (error) {
        console.error(error);
        document.getElementById('navStatus').innerText = "Error initializing navigation.";
    }
}
