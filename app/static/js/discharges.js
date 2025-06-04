document.addEventListener('DOMContentLoaded', function () {
	const newDischargeBtn = document.getElementById('newDischargeBtn');
	const closeFormBtn = document.getElementById('closeDischargeFormBtn');
	const dischargeForm = document.getElementById('dischargeForm');
	const formOverlay = document.getElementById('dischargeFormOverlay');

	// Open form
	newDischargeBtn.addEventListener('click', function () {
		dischargeForm.classList.add('show');
		formOverlay.style.display = 'block';
		document.body.style.overflow = 'hidden';
		loadCurrentPatients();
	});

	// Close form
	closeFormBtn.addEventListener('click', closeForm);
	formOverlay.addEventListener('click', closeForm);

	function closeForm() {
		dischargeForm.classList.remove('show');
		formOverlay.style.display = 'none';
		document.body.style.overflow = 'auto';
	}

	// Load current patients
	function loadCurrentPatients() {
		fetch('/api/current-patients?hospital_id={{ hospital.id }}')
			.then((response) => response.json())
			.then((data) => {
				const patientSelect = document.getElementById('patientSelect');
				patientSelect.innerHTML = '';

				if (data.patients.length === 0) {
					patientSelect.innerHTML =
						'<option value="">No current patients</option>';
					return;
				}

				data.patients.forEach((patient) => {
					const option = document.createElement('option');
					option.value = patient.id;
					option.textContent = `${patient.name} (Bed ${patient.bed_number})`;
					patientSelect.appendChild(option);
				});
			});
	}

	// Form submission
	document
		.getElementById('dischargeFormData')
		.addEventListener('submit', function (e) {
			e.preventDefault();

			const formData = {
				patient_id: this.patient_id.value,
				discharge_type: this.discharge_type.value,
				discharging_doctor: this.discharging_doctor.value,
				notes: this.notes.value,
			};

			fetch('/api/discharge', {
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
						window.location.reload();
					} else {
						alert('Error: ' + data.message);
					}
				});
		});
});
