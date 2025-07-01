// --- GLOBAL NOTIFICATION LOGIC ---

let userSettings = null;
let audioEnabled = false;
let isSoundPlaying = false;
let currentNotification = null;
let audioMessageShown = false;
let currentReferralId = null;
let referralCountdownInterval = null;
let referralCountdownRemaining = null;
let referralCountdownStartTimestamp = null;
let referralCountdownReferralId = null;

// Fetch user settings
function loadUserSettings() {
	return fetch('/user/api/settings')
		.then((response) => response.json())
		.then((data) => {
			if (data.success) {
				userSettings = data.settings;
				setTimeout(() => {
					const audio = document.getElementById('notificationSound');
					if (audio) {
						audio.volume = userSettings.audio_volume;
						if (
							userSettings.audio_enabled &&
							userSettings.audio_notifications
						) {
							testAudioPlayability();
						}
					}
				}, 100);
			} else {
				userSettings = {
					audio_notifications: true,
					visual_notifications: true,
					browser_notifications: false,
					audio_volume: 0.7,
					audio_enabled: false,
					referral_notifications: true,
					bed_status_notifications: true,
					system_notifications: true,
					notification_duration: 120,
					auto_escalate: true,
				};
			}
		})
		.catch(() => {
			userSettings = {
				audio_notifications: true,
				visual_notifications: true,
				browser_notifications: false,
				audio_volume: 0.7,
				audio_enabled: false,
				referral_notifications: true,
				bed_status_notifications: true,
				system_notifications: true,
				notification_duration: 120,
				auto_escalate: true,
			};
		});
}

function testAudioPlayability() {
	const audio = document.getElementById('notificationSound');
	if (!audio) return;
	const originalVolume = audio.volume;
	audio.volume = 0;
	audio
		.play()
		.then(() => {
			audio.pause();
			audio.currentTime = 0;
			audio.volume = originalVolume;
			audioEnabled = true;
			audioMessageShown = false;
		})
		.catch(() => {
			audio.volume = originalVolume;
			audioEnabled = false;
		});
}

function saveAudioEnabledStatus(enabled) {
	fetch('/user/api/settings', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ audio_enabled: enabled }),
	});
}

function startReferralCountdown(referral) {
	// Stop any existing countdown
	if (referralCountdownInterval) {
		clearInterval(referralCountdownInterval);
		referralCountdownInterval = null;
	}
	referralCountdownRemaining = referral.time_remaining || 120;
	referralCountdownStartTimestamp = Date.now();
	referralCountdownReferralId = referral.id;
	updateReferralCountdownDisplay();
	referralCountdownInterval = setInterval(() => {
		// Calculate elapsed time
		const elapsed = Math.floor(
			(Date.now() - referralCountdownStartTimestamp) / 1000
		);
		let remaining = (referral.time_remaining || 120) - elapsed;
		if (remaining < 0) remaining = 0;
		referralCountdownRemaining = remaining;
		updateReferralCountdownDisplay();
		if (remaining <= 0) {
			clearInterval(referralCountdownInterval);
			referralCountdownInterval = null;
		}
	}, 1000);
}

function updateReferralCountdownDisplay() {
	const timeElement = document.getElementById('timeRemaining');
	if (timeElement && referralCountdownRemaining !== null) {
		timeElement.textContent = `${Math.floor(
			referralCountdownRemaining / 60
		)}:${(referralCountdownRemaining % 60).toString().padStart(2, '0')}`;
	}
}

function showReferralModal(referral) {
	const detailsDiv = document.getElementById('referralDetails');
	if (!detailsDiv) return;

	currentReferralId = referral.id;
	detailsDiv.innerHTML = `
		<div class="row">
			<div class="col-md-6">
				<h6>Patient Information</h6>
				<p><strong>Age:</strong> ${referral.patient_age}</p>
				<p><strong>Gender:</strong> ${referral.patient_gender}</p>
				${
					referral.primary_diagnosis
						? `<p><strong>Primary Diagnosis:</strong> ${referral.primary_diagnosis}</p>`
						: ''
				}
			</div>
			<div class="col-md-6">
				<h6>Referral Details</h6>
				<p><strong>From:</strong> ${referral.requesting_hospital}</p>
				<p><strong>Urgency:</strong> ${referral.urgency}</p>
				<p><strong>Reason:</strong> ${referral.reason || ''}</p>
				${
					referral.current_treatment
						? `<p><strong>Current Treatment:</strong> ${referral.current_treatment}</p>`
						: ''
				}
			</div>
		</div>
		${
			referral.special_requirements
				? `<p><strong>Special Requirements:</strong> ${referral.special_requirements}</p>`
				: ''
		}
	`;

	// Show the modal
	const modal = new bootstrap.Modal(
		document.getElementById('referralResponseModal')
	);
	modal.show();
	// Update the countdown display immediately
	updateReferralCountdownDisplay();
}

function acceptReferral() {
	if (!currentReferralId) return;
	fetch('/referrals/api/respond-to-referral', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			referral_id: currentReferralId,
			response_type: 'accept',
			response_message: 'Referral accepted',
		}),
	})
		.then((response) => response.json())
		.then((data) => {
			if (data.success) {
				stopNotificationSound();
				if (currentNotification) {
					currentNotification.remove();
					currentNotification = null;
				}

				// Add notification to notification center for the accepting hospital
				if (window.addNotification) {
					window.addNotification(
						'referral',
						'Referral Accepted',
						`ICU referral request has been accepted successfully.`,
						{ referral_id: currentReferralId }
					);
				}

				showAlert('Referral accepted successfully!', 'success');
				closeReferralModal();
			} else {
				showAlert(data.message, 'error');
			}
		})
		.catch((error) => {
			console.error('Error:', error);
			showAlert('Error accepting referral', 'error');
		});
}

function rejectReferral(reason) {
	console.log('rejectReferral called with reason:', reason);
	if (!currentReferralId) {
		console.warn('No currentReferralId available');
		return;
	}
	console.log('Current referral ID:', currentReferralId);

	fetch('/referrals/api/respond-to-referral', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({
			referral_id: currentReferralId,
			response_type: 'reject',
			response_message: reason,
		}),
	})
		.then((response) => response.json())
		.then((data) => {
			console.log('Reject referral response:', data);
			if (data.success) {
				stopNotificationSound();

				// Add notification to notification center for the rejecting hospital
				if (window.addNotification) {
					console.log('Adding rejection notification to notification center');
					window.addNotification(
						'referral',
						'Referral Rejected',
						`ICU referral request was rejected. Reason: ${reason}`,
						{ referral_id: currentReferralId, reason: reason }
					);
				} else {
					console.warn(
						'addNotification function not available in rejectReferral'
					);
				}

				showAlert('Referral rejected', 'info');
				closeReferralModal();
				closeRejectionModal();
			} else {
				showAlert(data.message, 'error');
			}
		})
		.catch((error) => {
			console.error('Error rejecting referral:', error);
			showAlert('Error rejecting referral', 'error');
		});
}

function closeReferralModal() {
	const modal = bootstrap.Modal.getInstance(
		document.getElementById('referralResponseModal')
	);
	if (modal) {
		modal.hide();
	}
}

function closeRejectionModal() {
	document.getElementById('rejectionReason').value = '';
	const modal = bootstrap.Modal.getInstance(
		document.getElementById('rejectionReasonModal')
	);
	if (modal) {
		modal.hide();
	}
}

// Set up global event listeners for modal buttons
function setupGlobalReferralModalListeners() {
	const acceptBtn = document.getElementById('acceptReferralBtn');
	const rejectBtn = document.getElementById('rejectReferralBtn');
	const confirmRejectBtn = document.getElementById('confirmRejectBtn');

	if (acceptBtn) {
		acceptBtn.addEventListener('click', acceptReferral);
	}
	if (rejectBtn) {
		rejectBtn.addEventListener('click', function () {
			const rejectionModal = new bootstrap.Modal(
				document.getElementById('rejectionReasonModal')
			);
			rejectionModal.show();
		});
	}
	if (confirmRejectBtn) {
		confirmRejectBtn.addEventListener('click', function () {
			const reason = document.getElementById('rejectionReason').value;
			if (reason.trim()) {
				rejectReferral(reason);
			} else {
				showAlert('Please provide a reason for rejection.', 'error');
			}
		});
	}
}

function showVisualNotification(referral) {
	if (!userSettings || !userSettings.visual_notifications) return;
	if (currentNotification) currentNotification.remove();
	const notification = document.createElement('div');
	notification.className = 'position-fixed notification-alert';
	notification.style.cssText = `
        top: 20px; right: 20px; z-index: 9999;
        background: #dc3545; color: white; padding: 15px 25px;
        border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer; animation: fadeIn 0.3s;
    `;
	notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-bell me-2"></i>
            <div>
                <strong>NEW ICU TRANSFER REQUEST!</strong><br>
                <small>Click to view details</small>
            </div>
        </div>
    `;
	notification.addEventListener('click', () => {
		showReferralModal(referral);
		notification.remove();
		currentNotification = null;
	});
	document.body.appendChild(notification);
	currentNotification = notification;
}

function playNotificationSound() {
	if (!userSettings || !userSettings.audio_notifications) return;
	const audio = document.getElementById('notificationSound');
	if (!audio) return;
	if (isSoundPlaying) return;
	if (!audioEnabled) {
		audio
			.play()
			.then(() => {
				audio.pause();
				audio.currentTime = 0;
				audioEnabled = true;
				saveAudioEnabledStatus(true);
				playNotificationSound();
			})
			.catch(() => {
				if (!audioMessageShown) {
					showAlert(
						'Click anywhere on the page to enable notification sounds',
						'info'
					);
					audioMessageShown = true;
				}
			});
		return;
	}
	isSoundPlaying = true;
	audio.volume = userSettings.audio_volume || 0.7;
	const restartSound = () => {
		if (isSoundPlaying) {
			audio.currentTime = 0;
			audio.play().catch(() => {
				isSoundPlaying = false;
			});
		}
	};
	audio.restartSound = restartSound;
	audio.addEventListener('ended', restartSound);
	audio.currentTime = 0;
	audio.play().catch(() => {
		isSoundPlaying = false;
	});
}

function stopNotificationSound() {
	const audio = document.getElementById('notificationSound');
	if (audio) {
		isSoundPlaying = false;
		audio.pause();
		audio.currentTime = 0;
		if (audio.restartSound) {
			audio.removeEventListener('ended', audio.restartSound);
			audio.restartSound = null;
		}
	}
}

function showAlert(message, type) {
	const alertDiv = document.createElement('div');
	alertDiv.className = `alert alert-${
		type === 'error' ? 'danger' : type
	} alert-dismissible fade show position-fixed`;
	alertDiv.style.cssText =
		'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
	alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
	document.body.appendChild(alertDiv);
	setTimeout(() => {
		if (alertDiv.parentNode) {
			alertDiv.remove();
		}
	}, 5000);
}

// --- SOCKET.IO REAL-TIME REFERRALS ---
window.socket = io();
const socket = window.socket;
socket.on('connect', function () {
	console.log('Connected to WebSocket server');
});
socket.on('new_referral', function (referral) {
	if (
		window.currentHospitalId &&
		referral.target_hospital_id == window.currentHospitalId
	) {
		showVisualNotification(referral);
		playNotificationSound();
		startReferralCountdown(referral); // Start countdown immediately

		// Add notification to notification center
		if (window.addNotification) {
			window.addNotification(
				'referral',
				'New ICU Referral Request',
				`New referral request received from ${referral.requesting_hospital}`,
				{
					referral_id: referral.id,
					requesting_hospital: referral.requesting_hospital,
				}
			);
		}
	}
});

// Listen for transfer status updates
socket.on('transfer_status_update', function (transfer) {
	console.log('Transfer status update received:', transfer);

	// Only show notifications to the sending or receiving hospital
	if (
		window.currentHospitalId &&
		(window.currentHospitalId == transfer.from_hospital_id ||
			window.currentHospitalId == transfer.to_hospital_id)
	) {
		if (window.addNotification) {
			let title, message;

			switch (transfer.status) {
				case 'En Route':
					title = 'Patient Transfer Started';
					message = `Patient transfer from ${transfer.from_hospital} is now en route`;
					break;
				case 'Arrived':
					title = 'Patient Transfer Arrived';
					message = `Patient transfer from ${transfer.from_hospital} has arrived`;
					break;
				case 'Admitted':
					if (window.currentHospitalId == transfer.from_hospital_id) {
						title = 'Patient Admitted';
						message = `Your patient referral at ${transfer.to_hospital} has been admitted.`;
						window.addNotification('transfer', title, message, {
							transfer_id: transfer.id,
							status: transfer.status,
							from_hospital: transfer.from_hospital,
							to_hospital: transfer.to_hospital,
						});
					}
					// Do not notify the receiving hospital on admission
					return;
				case 'Cancelled':
					title = 'Transfer Cancelled';
					message = `Patient transfer from ${transfer.from_hospital} was cancelled`;
					break;
				default:
					title = 'Transfer Status Update';
					message = `Transfer status changed to: ${transfer.status}`;
			}

			// For all other statuses, notify both hospitals as before
			if (transfer.status !== 'Admitted') {
				console.log('Adding transfer notification:', { title, message });
				window.addNotification('transfer', title, message, {
					transfer_id: transfer.id,
					status: transfer.status,
					from_hospital: transfer.from_hospital,
					to_hospital: transfer.to_hospital,
				});
			}
		} else {
			console.warn(
				'addNotification function not available for transfer update'
			);
		}
	} else {
		console.log('Transfer update not relevant for current hospital');
	}
});

// Listen for referral responses (for the sending hospital)
socket.on('referral_response', function (response) {
	console.log('Referral response received:', response);
	console.log(
		'Current hospital ID:',
		window.currentHospitalId,
		'Requesting hospital ID:',
		response.requesting_hospital_id
	);
	if (window.addNotification) {
		// Only show to the sending hospital
		if (
			window.currentHospitalId &&
			window.currentHospitalId == response.requesting_hospital_id
		) {
			const title =
				response.response_type === 'accept'
					? 'Referral Accepted'
					: 'Referral Rejected';
			const message =
				response.response_type === 'accept'
					? `Your referral to ${response.target_hospital} was accepted`
					: `Your referral to ${response.target_hospital} was rejected. Reason: ${response.response_message}`;

			console.log('Adding notification for referral response:', {
				title,
				message,
			});
			window.addNotification('referral', title, message, {
				referral_id: response.referral_id,
				response_type: response.response_type,
				target_hospital: response.target_hospital,
			});
		}
	} else {
		console.warn('addNotification function not available');
	}
});

document.addEventListener('DOMContentLoaded', function () {
	loadUserSettings();
	setupGlobalReferralModalListeners();
	// Enable audio on first user interaction if settings allow
	document.addEventListener(
		'click',
		function enableAudio() {
			if (!audioEnabled && userSettings && userSettings.audio_notifications) {
				const audio = document.getElementById('notificationSound');
				if (audio) {
					audio.play().then(() => {
						audio.pause();
						audio.currentTime = 0;
						audioEnabled = true;
						audioMessageShown = false;
						saveAudioEnabledStatus(true);
					});
				}
			}
			document.removeEventListener('click', enableAudio);
		},
		{ once: true }
	);
});

// --- GLOBAL TOAST AND SOUND NOTIFICATION ---
window.showGlobalNotification = function (title, message) {
	// Play global notification sound if enabled
	const audio = document.getElementById('globalNotificationSound');
	if (audio) {
		audio.currentTime = 0;
		audio.play().catch(() => {});
	}
	// Show toast
	const container = document.getElementById('globalToastContainer');
	if (!container) return;
	// Create toast element
	const toast = document.createElement('div');
	toast.className = 'global-toast shadow';
	toast.style.cssText = `
        min-width: 280px;
        max-width: 350px;
        background: #222;
        color: #fff;
        border-radius: 8px;
        margin-top: 10px;
        padding: 16px 24px;
        font-size: 1rem;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.18);
        cursor: pointer;
        opacity: 0.97;
        animation: fadeIn 0.3s;
    `;
	toast.innerHTML = `
        <div style="flex:1;">
            <strong style="font-size:1.1em;">${title}</strong><br>
            <span style="font-size:0.97em;">${message}</span>
        </div>
        <span style="margin-left:16px; font-size:1.3em; opacity:0.7;">🔔</span>
    `;
	// Remove toast on click
	toast.onclick = () => toast.remove();
	// Auto-dismiss after 5 seconds
	setTimeout(() => toast.remove(), 5000);
	container.appendChild(toast);
};

// Patch addNotification to also show a global toast and sound
const originalAddNotification = window.addNotification;
window.addNotification = function (type, title, message, meta) {
	// Call the original notification logic
	if (originalAddNotification) {
		originalAddNotification(type, title, message, meta);
	}
	// Show global toast and sound
	window.showGlobalNotification(title, message);
};
