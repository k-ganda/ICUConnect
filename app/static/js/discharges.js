document.addEventListener('DOMContentLoaded', async () => {
	try {
		const response = await fetch('/discharges/api/current-patients');
		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();

		if (!data.patients || !Array.isArray(data.patients)) {
			throw new Error('Invalid data format');
		}

		const patientList = document.getElementById('current-patient-list');
		patientList.innerHTML = ''; // Clear old data

		data.patients.forEach((patient) => {
			const li = document.createElement('li');
			li.textContent = `${patient.name} (Bed ${patient.bed_number})`;
			patientList.appendChild(li);
		});
	} catch (error) {
		console.error('Error loading patients:', error);
		alert('Could not load patient data.');
	}
});
