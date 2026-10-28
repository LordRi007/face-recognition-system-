// ==========================================================================
// Face Recognition Management System (FRMS) - Core Client Script
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initSidebarToggle();
  initFlashAutoDismiss();
  initLucideIcons();
});

// Initialize Lucide Icons if loaded
function initLucideIcons() {
  if (window.lucide && typeof window.lucide.createIcons === "function") {
    window.lucide.createIcons();
  }
}

// Light / Dark Mode Toggle
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("frms_theme", next);
  updateThemeIcon(next);
}
window.toggleTheme = toggleTheme;

function initThemeToggle() {
  const toggleBtn = document.getElementById("themeToggleBtn");
  const storedTheme = localStorage.getItem("frms_theme");

  if (storedTheme) {
    document.documentElement.setAttribute("data-theme", storedTheme);
    updateThemeIcon(storedTheme);
  } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    document.documentElement.setAttribute("data-theme", "dark");
    updateThemeIcon("dark");
  }

  if (toggleBtn) {
    toggleBtn.addEventListener("click", toggleTheme);
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById("themeIcon");
  if (!icon) return;
  if (theme === "dark") {
    icon.setAttribute("data-lucide", "sun");
  } else {
    icon.setAttribute("data-lucide", "moon");
  }
  initLucideIcons();
}

// Mobile Sidebar Toggle
function initSidebarToggle() {
  const sidebar = document.getElementById("appSidebar");
  const toggleBtn = document.getElementById("sidebarToggleBtn");
  const backdrop = document.getElementById("sidebarBackdrop");

  if (toggleBtn && sidebar && backdrop) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("show");
      backdrop.classList.toggle("show");
    });

    backdrop.addEventListener("click", () => {
      sidebar.classList.remove("show");
      backdrop.classList.remove("show");
    });
  }
}

// Auto-dismiss bootstrap flash alerts
function initFlashAutoDismiss() {
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach((alert) => {
    setTimeout(() => {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {
        alert.remove();
      }
    }, 6000);
  });
}

// Toast notification helper
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  const toastEl = document.createElement("div");
  toastEl.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0 show mb-2`;
  toastEl.setAttribute("role", "alert");
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  container.appendChild(toastEl);
  setTimeout(() => toastEl.remove(), 5000);
}
