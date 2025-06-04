document.addEventListener('DOMContentLoaded', function () {
	const newAdmissionBtn = document.getElementById('newAdmissionBtn');
	const closeFormBtn = document.getElementById('closeFormBtn');
	const admissionForm = document.getElementById('admissionForm');
	const formOverlay = document.getElementById('formOverlay');

	// Open form
	newAdmissionBtn.addEventListener('click', function () {
		admissionForm.classList.add('show');
		formOverlay.style.display = 'block';
		document.body.style.overflow = 'hidden';
		updateAvailableBeds();
	});

	// Close form
	closeFormBtn.addEventListener('click', closeForm);
	formOverlay.addEventListener('click', closeForm);

	function closeForm() {
		admissionForm.classList.remove('show');
		formOverlay.style.display = 'none';
		document.body.style.overflow = 'auto';
	}

	// Fetch available beds
	function updateAvailableBeds() {
		fetch('/api/available-beds')
			.then((response) => response.json())
			.then((data) => {
				const bedSelect = document.getElementById('bedSelect');
				bedSelect.innerHTML = '';

				if (data.availableBeds.length === 0) {
					bedSelect.innerHTML = '<option value="">No beds available</option>';
					return;
				}

				data.availableBeds.forEach((bed) => {
					const option = document.createElement('option');
					option.value = bed.number;
					option.textContent = `Bed ${bed.number}`;
					bedSelect.appendChild(option);
				});

				document.getElementById('availableBedsCount').textContent = data.count;
			});
	}

	// Form submission
	document
		.getElementById('admissionFormData')
		.addEventListener('submit', function (e) {
			e.preventDefault();

			const formData = {
				patient_name: this.patient_name.value,
				bed_number: parseInt(this.bed_number.value),
				doctor: this.doctor.value,
				reason: this.reason.value,
				priority: this.querySelector('input[name="priority"]:checked').value,
			};

			fetch('/api/admit', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
				body: JSON.stringify(formData),
			})
				.then((response) => response.json())
				.then((data) => {
					if (data.success) {
						closeForm();
						// Refresh the page to show new admission
						window.location.reload();
					} else {
						alert('Error: ' + data.message);
					}
				})
				.catch((error) => {
					console.error('Error:', error);
					alert('An error occurred');
				});
		});
});
