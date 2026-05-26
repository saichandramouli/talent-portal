// Handle dismissible alerts automatically after a short timeout
document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            // Check if Bootstrap's Alert instance exists and close it
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                // Fallback for simple fading dismissal
                alert.style.transition = "opacity 0.5s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 500);
            }
        }, 5000); // 5 seconds
    });
});

// Confirmation dialog for delete actions
function confirmDelete(itemName) {
    return confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`);
}
