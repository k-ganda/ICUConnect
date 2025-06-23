// Referral System JavaScript
class ReferralSystem {
    constructor() {
        this.map = null;
        this.currentReferralId = null;
        this.timeoutInterval = null;
        this.notificationSound = document.getElementById('notificationSound');
        this.activeReferrals = new Map();
        
        this.init();
    }

    init() {
        this.initMap();
        this.initEventListeners();
        this.startPolling();
        this.loadPendingReferrals();
    }

    initMap() {
        // Initialize map with fallback view
        this.map = L.map('map').setView([-0.1022, 34.7617], 10);

        // Add base tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
        }).addTo(this.map);

        // Load Kisumu boundary
        fetch("/user/kisumu-geojson")
            .then((response) => response.json())
            .then((data) => {
                console.log('GeoJSON loaded:', data);

                // Handle GeometryCollection format
                if (data.type === 'GeometryCollection') {
                    const multiPolygon = data.geometries.find(
                        (g) => g.type === 'MultiPolygon'
                    );

                    if (multiPolygon) {
                        const feature = {
                            type: 'Feature',
                            properties: {},
                            geometry: multiPolygon,
                        };

                        const countyLayer = L.geoJSON(feature, {
                            style: {
                                color: '#3388ff',
                                weight: 3,
                                opacity: 1,
                                fillOpacity: 0.2,
                                fillColor: '#3388ff',
                            },
                        }).addTo(this.map);

                        this.map.fitBounds(countyLayer.getBounds());
                        this.map.setMaxBounds(countyLayer.getBounds().pad(0.5));
                    }
                }

                // Load hospitals data
                this.loadHospitalsOnMap();
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    }

    loadHospitalsOnMap() {
        // Get hospitals data from the page
        const hospitals = window.hospitalsData || [];
        
        // Color coding based on availability percentage
        function getMarkerColor(hospital) {
            if (hospital.beds <= 0) return 'gray';
            const percentage = (hospital.available / hospital.beds) * 100;
            if (percentage >= 30) return 'green';
            if (percentage >= 10) return 'orange';
            return 'red';
        }

        // Custom icon creation
        function createCustomIcon(color, available) {
            return L.divIcon({
                className: 'custom-marker',
                html: `
                    <div class="marker-pin" style="background-color:${color}">
                        <span>${available}</span>
                    </div>
                `,
                iconSize: [30, 42],
                iconAnchor: [15, 42],
            });
        }

        // Add hospitals with enhanced markers
        hospitals.forEach((hospital) => {
            if (!hospital.lat || !hospital.lng) return;

            const color = getMarkerColor(hospital);
            const icon = createCustomIcon(color, hospital.available);

            const marker = L.marker([hospital.lat, hospital.lng], { icon }).addTo(this.map)
                .bindPopup(`
                    <div class="hospital-popup">
                        <h6><strong>${hospital.name}</strong></h6>
                        ${hospital.level ? `<p>Level: <strong>${hospital.level}</strong></p>` : ''}
                        <p>Total Beds: <strong>${hospital.beds}</strong></p>
                        <p>Available: <strong>${hospital.available}</strong></p>
                        <button class="btn btn-sm btn-primary mt-2 w-100 select-hospital-btn"
                                data-hospital-id="${hospital.id}"
                                data-hospital-name="${hospital.name}">
                            Select for Referral
                        </button>
                    </div>
                `);

            // Handle hospital selection
            marker.on('popupopen', function () {
                document.querySelectorAll('.select-hospital-btn').forEach((btn) => {
                    btn.addEventListener('click', function () {
                        const hospitalId = this.dataset.hospitalId;
                        const hospitalName = this.dataset.hospitalName;
                        
                        // Update the form
                        document.getElementById('targetHospitalSelect').value = hospitalId;
                        
                        // Show success message
                        showAlert(`Selected ${hospitalName} for referral`, 'success');
                        
                        // Close popup
                        marker.closePopup();
                    });
                });
            });
        });
    }

    initEventListeners() {
        // Referral form submission
        const referralForm = document.getElementById('referralForm');
        if (referralForm) {
            referralForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitReferral();
            });
        }

        // Accept referral button
        const acceptBtn = document.getElementById('acceptReferralBtn');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', () => {
                this.respondToReferral('accept');
            });
        }

        // Reject referral button
        const rejectBtn = document.getElementById('rejectReferralBtn');
        if (rejectBtn) {
            rejectBtn.addEventListener('click', () => {
                this.respondToReferral('reject');
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadPendingReferrals();
                this.updateStatistics();
            });
        }
    }

    submitReferral() {
        const formData = {
            target_hospital_id: document.getElementById('targetHospitalSelect').value,
            patient_id: document.getElementById('patientSelect').value,
            primary_diagnosis: document.getElementById('primaryDiagnosis').value,
            current_treatment: document.getElementById('currentTreatment').value,
            urgency: document.getElementById('urgencyLevel').value,
            reason: document.getElementById('reasonForReferral').value,
            special_requirements: document.getElementById('specialRequirements').value
        };

        // Validate form
        if (!formData.target_hospital_id || !formData.patient_id || !formData.reason) {
            showAlert('Please fill in all required fields', 'error');
            return;
        }

        // Disable submit button
        const submitBtn = document.getElementById('submitReferralBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        fetch('/referrals/api/initiate-referral', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                this.startReferralTracking(data.referral_id, data.timeout_seconds);
                this.resetForm();
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while sending the referral', 'error');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send Referral Request';
        });
    }

    startReferralTracking(referralId, timeoutSeconds) {
        this.currentReferralId = referralId;
        let timeRemaining = timeoutSeconds;

        // Start countdown
        this.timeoutInterval = setInterval(() => {
            timeRemaining--;
            
            // Update UI
            this.updateReferralStatus(referralId, timeRemaining);
            
            if (timeRemaining <= 0) {
                clearInterval(this.timeoutInterval);
                this.handleTimeout(referralId);
            }
        }, 1000);

        // Store active referral
        this.activeReferrals.set(referralId, {
            startTime: Date.now(),
            timeout: timeoutSeconds,
            status: 'pending'
        });

        this.updateActiveReferralsList();
    }

    updateReferralStatus(referralId, timeRemaining) {
        // Update the active referrals list
        const referral = this.activeReferrals.get(referralId);
        if (referral) {
            referral.timeRemaining = timeRemaining;
            this.updateActiveReferralsList();
        }
    }

    handleTimeout(referralId) {
        // Check if referral was responded to
        fetch(`/referrals/api/check-referral-status/${referralId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.status === 'Pending') {
                    // Auto-escalate to next hospital
                    this.escalateReferral(referralId);
                }
            })
            .catch(error => {
                console.error('Error checking referral status:', error);
            });
    }

    escalateReferral(referralId) {
        fetch(`/referrals/api/escalate-referral/${referralId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(`Referral escalated to ${data.target_hospital}`, 'info');
                this.startReferralTracking(data.new_referral_id, 120);
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error escalating referral:', error);
            showAlert('Error escalating referral', 'error');
        });
    }

    respondToReferral(responseType) {
        if (!this.currentReferralId) {
            showAlert('No active referral to respond to', 'error');
            return;
        }

        const responseMessage = prompt(`Please provide a reason for ${responseType}ing this referral:`);
        
        fetch('/referrals/api/respond-to-referral', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                referral_id: this.currentReferralId,
                response_type: responseType,
                response_message: responseMessage || ''
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                this.stopNotification();
                this.closeReferralModal();
                this.loadPendingReferrals();
            } else {
                showAlert(data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while responding to the referral', 'error');
        });
    }

    loadPendingReferrals() {
        fetch('/referrals/api/pending-referrals')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayPendingReferrals(data.referrals);
                }
            })
            .catch(error => {
                console.error('Error loading pending referrals:', error);
            });
    }

    displayPendingReferrals(referrals) {
        if (referrals.length > 0) {
            // Show notification for new referrals
            this.playNotificationSound();
            this.showReferralModal(referrals[0]);
        }
    }

    showReferralModal(referral) {
        const modal = document.getElementById('referralResponseModal');
        const detailsDiv = document.getElementById('referralDetails');
        
        detailsDiv.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Patient Information</h6>
                    
                    <p><strong>Age:</strong> ${referral.patient_age || 'N/A'}</p>
                    <p><strong>Gender:</strong> ${referral.patient_gender || 'N/A'}</p>
                    ${referral.primary_diagnosis ? `<p><strong>Primary Diagnosis:</strong> ${referral.primary_diagnosis}</p>` : ''}
                </div>
                <div class="col-md-6">
                    <h6>Referral Details</h6>
                    <p><strong>From:</strong> ${referral.requesting_hospital}</p>
                    <p><strong>Urgency:</strong> <span class="badge bg-${this.getUrgencyColor(referral.urgency)}">${referral.urgency}</span></p>
                    <p><strong>Reason:</strong> ${referral.reason}</p>
                    ${referral.current_treatment ? `<p><strong>Current Treatment:</strong> ${referral.current_treatment}</p>` : ''}
                    ${referral.special_requirements ? `<p><strong>Special Requirements:</strong> ${referral.special_requirements}</p>` : ''}
                </div>
            </div>
        `;

        this.currentReferralId = referral.id;
        this.startCountdown(referral.time_remaining);
        
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }

    startCountdown(timeRemaining) {
        const timeElement = document.getElementById('timeRemaining');
        let timeLeft = timeRemaining;

        const countdown = setInterval(() => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timeElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

            if (timeLeft <= 0) {
                clearInterval(countdown);
                this.stopNotification();
                this.closeReferralModal();
            }
            timeLeft--;
        }, 1000);
    }

    playNotificationSound() {
        if (this.notificationSound) {
            this.notificationSound.play().catch(e => {
                console.log('Could not play notification sound:', e);
            });
        }
    }

    stopNotification() {
        if (this.notificationSound) {
            this.notificationSound.pause();
            this.notificationSound.currentTime = 0;
        }
    }

    closeReferralModal() {
        const modal = document.getElementById('referralResponseModal');
        const modalInstance = bootstrap.Modal.getInstance(modal);
        if (modalInstance) {
            modalInstance.hide();
        }
    }

    resetForm() {
        document.getElementById('referralForm').reset();
        document.getElementById('targetHospitalSelect').innerHTML = '<option value="">Select hospital from map...</option>';
    }

    updateActiveReferralsList() {
        const listElement = document.getElementById('activeReferralsList');
        if (!listElement) return;

        listElement.innerHTML = '';
        
        this.activeReferrals.forEach((referral, id) => {
            const timeRemaining = referral.timeRemaining || 0;
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                <div>
                    <strong>Referral #${id}</strong>
                    <br>
                    <small class="text-muted">Status: ${referral.status}</small>
                </div>
                <span class="badge bg-warning">${minutes}:${seconds.toString().padStart(2, '0')}</span>
            `;
            listElement.appendChild(item);
        });
    }

    updateStatistics() {
        // This would be implemented to update the statistics cards
        // For now, we'll just update the pending count
        document.getElementById('pendingCount').textContent = this.activeReferrals.size;
    }

    getUrgencyColor(urgency) {
        switch (urgency.toLowerCase()) {
            case 'high': return 'danger';
            case 'medium': return 'warning';
            case 'low': return 'info';
            default: return 'secondary';
        }
    }

    startPolling() {
        // Poll for new referrals every 10 seconds
        setInterval(() => {
            this.loadPendingReferrals();
        }, 10000);
    }
}

// Utility function to show alerts
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Initialize referral system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set hospitals data for the map
    window.hospitalsData = {{ available_hospitals|tojson|safe }};
    
    // Initialize the referral system
    window.referralSystem = new ReferralSystem();
}); 