document.addEventListener('DOMContentLoaded', function () {
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
			admissionForm.classList.add('show');
			formOverlay.style.display = 'block';
			document.body.style.overflow = 'hidden';
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
	}

	// Form submission
	if (admissionFormData) {
		admissionFormData.addEventListener('submit', function (e) {
			e.preventDefault();

			const formData = {
				patient_name: this.patient_name.value,
				bed_number: parseInt(this.bed_number.value),
				doctor: this.doctor.value,
				reason: this.reason.value,
				age: parseInt(this.age.value),
				gender: this.gender.value,
				priority: this.querySelector('input[name="priority"]:checked')?.value,
			};

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

					if (response.ok && data.success) {
						closeForm();
						window.location.reload();
					} else {
						alert('Error: ' + (data.message || 'Unknown error occurred'));
					}
				})
				.catch((error) => {
					console.error('Fetch error:', error);
					alert('An error occurred: ' + (error.message || 'Unknown error'));
				});
		});
	}
});
