/**
 * CareerMate AI - Core Client Scripts
 */
document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggler
  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const appSidebar = document.getElementById('appSidebar');

  if (sidebarToggleBtn && appSidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      appSidebar.classList.toggle('show');
    });

    // Close when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (
        window.innerWidth < 992 &&
        appSidebar.classList.contains('show') &&
        !appSidebar.contains(e.target) &&
        !sidebarToggleBtn.contains(e.target)
      ) {
        appSidebar.classList.remove('show');
      }
    });
  }

  // Auto-dismiss alerts after 5 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      } catch (err) {
        alert.remove();
      }
    }, 5000);
  });
});

/**
 * Helper to obtain Django CSRF Token from cookie
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + '=') {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
