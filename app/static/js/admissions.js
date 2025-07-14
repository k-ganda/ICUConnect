document.addEventListener('DOMContentLoaded', function () {
	console.log('[admissions.js] DOMContentLoaded');
	const newAdmissionBtn = document.getElementById('newAdmissionBtn');
	const closeFormBtn = document.getElementById('closeFormBtn');
	const admissionForm = document.getElementById('admissionForm');
	const formOverlay = document.getElementById('formOverlay');
	const admissionFormData = document.getElementById('admissionFormData');
	const statusFilter = document.getElementById('statusFilter');

	// Status filter functionality
	if (statusFilter) {
		statusFilter.addEventListener('change', function () {
			const selectedStatus = this.value;
			const currentUrl = new URL(window.location);
			currentUrl.searchParams.set('status', selectedStatus);
			currentUrl.searchParams.set('page', '1'); // Reset to first page when filtering
			window.location.href = currentUrl.toString();
		});
	}

	// Open form
	if (newAdmissionBtn && admissionForm && formOverlay) {
		newAdmissionBtn.addEventListener('click', function () {
			console.log('[admissions.js] New Admission button clicked');
			admissionForm.classList.add('show');
			formOverlay.style.display = 'block';
			document.body.style.overflow = 'hidden';
			console.log('[admissions.js] Slide-in form opened');
			updateAvailableBeds();
		});
	}

	// Close form
	if (closeFormBtn && formOverlay && admissionForm) {
		closeFormBtn.addEventListener('click', closeForm);
		formOverlay.addEventListener('click', closeForm);
	}

	function closeForm() {
		admissionForm.classList.remove('show');
		formOverlay.style.display = 'none';
		document.body.style.overflow = 'auto';
		console.log('[admissions.js] Slide-in form closed');
	}

	// Track reserved bed for transfer
	let reservedBedForTransfer = null;
	let reservedBedToSelect = null;

	window.setReservedBedToSelect = function (bedNumber) {
		console.log(
			'[admissions.js] setReservedBedToSelect called with',
			bedNumber
		);
		reservedBedToSelect = bedNumber;
		reservedBedForTransfer = bedNumber;
	};

	window.updateAvailableBeds = function (reservedBedNumber) {
		console.log(
			'[admissions.js] updateAvailableBeds called',
			reservedBedNumber
		);
		const bedSelect = document.getElementById('bedSelect');
		const countSpan = document.getElementById('availableBedsCount');
		if (!bedSelect || !countSpan) return;
		// Show loading state
		bedSelect.disabled = true;
		countSpan.textContent = 'loading...';
		let url = '/admissions/api/available-beds';
		if (reservedBedNumber) {
			url += `?reserved_bed_number=${reservedBedNumber}`;
		}
		fetch(url)
			.then((response) => {
				if (!response.ok) throw new Error('Network error');
				return response.json();
			})
			.then((data) => {
				// Clear existing options except the default
				bedSelect.innerHTML = '<option value="">Select available bed</option>';
				if (data.availableBeds.length === 0) {
					bedSelect.innerHTML =
						'<option value="" disabled>No beds available</option>';
					countSpan.textContent = '0';
					return;
				}
				// Add bed options
				data.availableBeds.forEach((bed) => {
					const option = new Option(`Bed ${bed.number}`, bed.number);
					bedSelect.add(option);
				});
				countSpan.textContent = data.count;
				bedSelect.disabled = false;
				// If a reserved bed is set, select it
				if (reservedBedToSelect) {
					console.log(
						'[admissions.js] Selecting reserved bed',
						reservedBedToSelect
					);
					bedSelect.value = reservedBedToSelect;
					reservedBedToSelect = null; // Reset after use
				}
			})
			.catch((error) => {
				console.error('Error fetching beds:', error);
				bedSelect.innerHTML =
					'<option value="" disabled>Error loading beds</option>';
				countSpan.textContent = 'error';
			});
	};

	// Form submission
	if (admissionFormData) {
		admissionFormData.addEventListener('submit', function (e) {
			e.preventDefault();

			const submitBtn = this.querySelector('button[type="submit"]');
			if (submitBtn) {
				submitBtn.disabled = true;
				submitBtn.innerHTML =
					'<span class="spinner-border spinner-border-sm"></span> Admitting...';
			}

			const formData = {
				patient_name: this.patient_name.value,
				bed_number: parseInt(this.bed_number.value),
				doctor: this.doctor.value,
				reason: this.reason.value,
				age: parseInt(this.age.value),
				gender: this.gender.value,
				priority: this.querySelector('input[name="priority"]:checked')?.value,
			};

			// If reservedBedForTransfer is set and matches the selected bed, include it
			if (
				reservedBedForTransfer &&
				parseInt(this.bed_number.value) === parseInt(reservedBedForTransfer)
			) {
				formData.reserved_bed_number = reservedBedForTransfer;
			}

			fetch('/admissions/api/admit', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(formData),
			})
				.then(async (response) => {
					const data = await response.json();
					console.log('API Response:', data);

					if (submitBtn) {
						submitBtn.disabled = false;
						submitBtn.innerHTML =
							'<i class="fas fa-bed me-2"></i>Admit Patient';
					}

					if (response.ok && data.success) {
						closeForm();
						// If this was a transfer admission, update the transfer status
						const url = new URL(window.location);
						const transferId = url.searchParams.get('transfer_id');
						if (transferId) {
							fetch('/transfers/api/update-transfer-status', {
								method: 'POST',
								headers: { 'Content-Type': 'application/json' },
								body: JSON.stringify({
									transfer_id: transferId,
									status: 'Admitted',
									arrival_notes: '',
								}),
							}).then(() => {
								refreshAdmissionsTable();
								if (window.showToast) {
									window.showToast(
										'Patient admitted and transfer updated!',
										'success'
									);
								}
							});
						} else {
							if (window.addNotification) {
								window.addNotification(
									'system',
									'Patient Admitted',
									'A new patient has been admitted to ICU',
									{
										patient_name: formData.patient_name,
										bed_number: formData.bed_number,
									}
								);
							}
							refreshAdmissionsTable();
							url.searchParams.delete('transfer_id');
						}
					} else {
						alert('Error: ' + (data.message || 'Unknown error occurred'));
					}
				})
				.catch((error) => {
					if (submitBtn) {
						submitBtn.disabled = false;
						submitBtn.innerHTML =
							'<i class="fas fa-bed me-2"></i>Admit Patient';
					}
					console.error('Fetch error:', error);
					alert('An error occurred: ' + (error.message || 'Unknown error'));
				});
		});
	}

	// Function to refresh the admissions table
	function refreshAdmissionsTable() {
		console.log('[admissions.js] Refreshing admissions table...');
		// Reload the page to show the updated admissions table
		window.location.reload();
	}

	window.openAdmissionForm = function () {
		console.log('[admissions.js] openAdmissionForm called');
		const admissionForm = document.getElementById('admissionForm');
		const formOverlay = document.getElementById('formOverlay');
		admissionForm.classList.add('show');
		formOverlay.style.display = 'block';
		document.body.style.overflow = 'hidden';
		console.log('[admissions.js] Slide-in form opened (openAdmissionForm)');
		if (typeof updateAvailableBeds === 'function') updateAvailableBeds();
	};
});
