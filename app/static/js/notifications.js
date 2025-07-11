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
	console.log('startReferralCountdown called with referral:', referral);
	// Stop any existing countdown
	if (referralCountdownInterval) {
		clearInterval(referralCountdownInterval);
		referralCountdownInterval = null;
	}
	// Use the referral's time_remaining (set by backend based on hospital settings)
	const notificationDuration = referral.time_remaining || 120;
	referralCountdownRemaining = notificationDuration;
	referralCountdownStartTimestamp = Date.now();
	referralCountdownReferralId = referral.id;
	console.log(
		'Starting countdown for referral ID:',
		referralCountdownReferralId,
		'with time remaining:',
		referralCountdownRemaining,
		'(referral.time_remaining:',
		referral.time_remaining,
		')'
	);
	updateReferralCountdownDisplay();
	referralCountdownInterval = setInterval(() => {
		// Calculate elapsed time
		const elapsed = Math.floor(
			(Date.now() - referralCountdownStartTimestamp) / 1000
		);
		let remaining = notificationDuration - elapsed;
		if (remaining < 0) remaining = 0;
		referralCountdownRemaining = remaining;
		updateReferralCountdownDisplay();
		if (remaining <= 0) {
			console.log(
				'startReferralCountdown: Countdown reached 0, handling timeout...'
			);
			console.log('referralCountdownReferralId:', referralCountdownReferralId);
			console.log('window.referralSystem:', window.referralSystem);

			clearInterval(referralCountdownInterval);
			referralCountdownInterval = null;
			// Handle timeout - stop notification and close modal
			stopNotificationSound();
			closeReferralModal();

			// Escalation logic: call backend to escalate referral
			if (referralCountdownReferralId) {
				console.log(
					'startReferralCountdown: Escalating referral with ID:',
					referralCountdownReferralId
				);
				console.log('About to call check-referral-status API...');
				fetch(
					`/referrals/api/check-referral-status/${referralCountdownReferralId}`
				)
					.then((response) => response.json())
					.then((data) => {
						console.log('Referral status check response:', data);
						if (data.success && data.status === 'Pending') {
							console.log('Referral is still pending, escalating...');
							console.log('About to call escalate-referral API...');
							fetch(
								`/referrals/api/escalate-referral/${referralCountdownReferralId}`,
								{
									method: 'POST',
									headers: {
										'Content-Type': 'application/json',
									},
								}
							)
								.then((response) => response.json())
								.then((escalateData) => {
									console.log('Escalation response:', escalateData);
									if (escalateData.success) {
										showAlert(
											`Referral escalated to ${escalateData.target_hospital}`,
											'info'
										);
									} else {
										showAlert(escalateData.message, 'error');
									}
								})
								.catch((error) => {
									console.error('Error escalating referral:', error);
									showAlert('Error escalating referral', 'error');
								});
						} else {
							console.log('Referral is not pending, status:', data.status);
						}
					})
					.catch((error) => {
						console.error('Error checking referral status:', error);
					});
			} else {
				console.log(
					'startReferralCountdown: referralCountdownReferralId not available'
				);
			}
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
	const urgency = referral.urgency || referral.urgency_level || 'Medium';
	const urgencyColor =
		urgency.toLowerCase() === 'high'
			? 'danger'
			: urgency.toLowerCase() === 'medium'
			? 'warning text-dark'
			: 'info text-dark';
	detailsDiv.innerHTML = `
		<div class="row">
			<div class="col-md-6 mb-3">
				<h6 class="fw-bold text-primary mb-3">Patient Information</h6>
				<div class="mb-2"><span class="fw-bold">Age:</span> ${
					referral.patient_age
				}</div>
				<div class="mb-2"><span class="fw-bold">Gender:</span> ${
					referral.patient_gender
				}</div>
				${
					referral.primary_diagnosis
						? `<div class="mb-2"><span class="fw-bold">Primary Diagnosis:</span> ${referral.primary_diagnosis}</div>`
						: ''
				}
			</div>
			<div class="col-md-6 mb-3">
				<h6 class="fw-bold text-primary mb-3">Referral Details</h6>
				<div class="mb-2"><span class="fw-bold">From:</span> ${
					referral.requesting_hospital
				}</div>
				<div class="mb-2">
					<span class="fw-bold">Urgency:</span>
					<span class="badge bg-${urgencyColor} ms-1">${urgency}</span>
				</div>
				<div class="mb-2"><span class="fw-bold">Reason:</span> ${
					referral.reason || ''
				}</div>
				${
					referral.current_treatment
						? `<div class="mb-2"><span class="fw-bold">Current Treatment:</span> ${referral.current_treatment}</div>`
						: ''
				}
			</div>
		</div>
		${
			referral.special_requirements
				? `<div class="mt-3"><span class="fw-bold">Special Requirements:</span> ${referral.special_requirements}</div>`
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
			// Check if this is an escalation hospital (id=11) and show different message
			let title, message;
			if (window.currentHospitalId == 11) {
				title = 'Referral Escalation Received';
				message = 'You have received a referral escalation';
			} else {
				title = 'New ICU Referral Request';
				message = `New referral request received from ${referral.requesting_hospital}`;
			}

			window.addNotification('referral', title, message, {
				referral_id: referral.id,
				requesting_hospital: referral.requesting_hospital,
			});
		}
	}
});

// Listen for transfer status updates
socket.on('transfer_status_update', function (transfer) {
	console.log(
		'Transfer status update received:',
		transfer,
		'Current hospital:',
		window.currentHospitalId
	);

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
					// Different message for sending vs receiving hospital
					if (window.currentHospitalId == transfer.from_hospital_id) {
						message = 'Your patient transfer is now en route';
					} else {
						message = `Patient transfer from ${transfer.from_hospital} is now en route`;
					}
					break;
				case 'Arrived':
					title = 'Patient Transfer Arrived';
					message = `Patient transfer from ${transfer.from_hospital} has arrived`;
					break;
				case 'Admitted':
					if (window.currentHospitalId == transfer.from_hospital_id) {
						title = 'Patient Admitted';
						message = `Your patient referral at ${transfer.to_hospital} has been admitted.`;

						// Add popup notification for sending hospital
						showAlert(message, 'success');

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

	// Also update dashboard if function is available
	if (typeof window.loadActiveTransfers === 'function') {
		if (transfer.status === 'Admitted') {
			// Immediately refresh the transfers list to remove the admitted transfer
			window.loadActiveTransfers();

			// Also refresh the page after a short delay to ensure all updates are visible
			setTimeout(() => {
				window.location.reload();
			}, 1000);
		} else {
			window.loadActiveTransfers();
		}
	} else if (transfer.status === 'Admitted') {
		// Fallback: force reload if admitted and function not available
		setTimeout(() => window.location.reload(), 1000);
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
		// This is for the sending hospital
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

// Listen for referral accepted by us (for the accepting hospital)
socket.on('referral_accepted_by_us', function (data) {
	console.log('Referral accepted by us received:', data);
	if (window.addNotification) {
		// This is for the accepting hospital
		if (window.currentHospitalId == data.hospital_id) {
			const title = 'Referral Accepted';
			const message = 'You have accepted this referral request';

			console.log('Adding notification for accepting hospital:', {
				title,
				message,
			});
			window.addNotification('referral', title, message, {
				referral_id: data.referral_id,
				response_type: 'accepted_by_us',
				target_hospital: data.hospital_name,
			});
		}
	} else {
		console.warn('addNotification function not available for accepted_by_us');
	}
});

// Listen for referral escalations
socket.on('referral_escalated', function (escalation) {
	console.log('Referral escalation received:', escalation);
	if (window.addNotification) {
		// Show to the requesting hospital (the one that sent the original referral)
		if (window.currentHospitalId) {
			const title = 'Referral Escalated';
			const message = escalation.message;

			console.log('Adding notification for referral escalation:', {
				title,
				message,
			});
			window.addNotification('referral', title, message, {
				referral_id: escalation.referral_id,
				escalated_to: escalation.escalated_to,
			});
		}
	} else {
		console.warn('addNotification function not available for escalation');
	}
});

socket.on('bed_stats_update', function (data) {
	console.log('bed_stats_update received:', data);
	// Only update cards if this is the current hospital
	if (
		typeof window.updateBedStatsCards === 'function' &&
		window.currentHospitalId &&
		data.hospital_stats &&
		data.hospital_stats.hospital_id == window.currentHospitalId
	) {
		window.updateBedStatsCards(data.hospital_stats);
	}
	if (typeof window.updateMapPins === 'function') {
		window.updateMapPins(data.hospitals);
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
