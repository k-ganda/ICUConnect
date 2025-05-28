$(document).ready(function () {
	// Sidebar toggle
	$('#sidebarCollapse').on('click', function () {
		$('#sidebar').toggleClass('active');
		$(this).find('i').toggleClass('fa-chevron-left fa-chevron-right');
	});

	// Update time display every second
	function updateTime() {
		const now = new Date();
		const options = {
			weekday: 'long',
			year: 'numeric',
			month: 'long',
			day: 'numeric',
		};
		const dateStr = now.toLocaleDateString('en-US', options);
		const timeStr = now.toLocaleTimeString('en-US');
		$('#datetime').text(`${dateStr}, ${timeStr}`);
	}
	updateTime();
	setInterval(updateTime, 1000);

	// Notification button
	$('#notificationsBtn').on('click', function () {
		alert('Notifications will appear here');
	});

	// Search button
	$('#searchBtn').on('click', function () {
		alert('Search functionality coming soon');
	});
});
