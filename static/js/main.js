/* FinWise – Main JavaScript utilities */

// ─── API Client ───────────────────────────────────────────────
const API_BASE = '/api';

function getToken() {
  return localStorage.getItem('fw_token');
}

function setToken(token) {
  localStorage.setItem('fw_token', token);
}

function clearAuth() {
  localStorage.removeItem('fw_token');
  localStorage.removeItem('fw_user');
}

function getUser() {
  const u = localStorage.getItem('fw_user');
  return u ? JSON.parse(u) : null;
}

function setUser(user) {
  localStorage.setItem('fw_user', JSON.stringify(user));
}

let _redirectingToLogin = false;

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    if (!_redirectingToLogin) {
      _redirectingToLogin = true;
      clearAuth();
      window.location.href = '/login';
    }
    return null;
  }

  const data = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data };
}

// ─── Auth Guard (for protected pages) ────────────────────────
function requireAuth() {
  const token = getToken();
  if (!token) {
    window.location.href = '/login';
    return false;
  }
  return true;
}

// Redirect logged-in users away from auth pages
function redirectIfAuth() {
  const token = getToken();
  if (token) {
    window.location.href = '/dashboard';
  }
}

// ─── Toast Notifications ──────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const icons = {
    success: 'fa-check',
    error: 'fa-times',
    warning: 'fa-exclamation',
    info: 'fa-info',
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div class="toast-icon"><i class="fa-solid ${icons[type] || icons.info}"></i></div>
    <span>${message}</span>
    <button onclick="this.parentElement.remove()" class="ml-auto text-slate-400 hover:text-white transition-colors">
      <i class="fa-solid fa-times text-xs"></i>
    </button>
  `;

  const container = document.getElementById('toast-container');
  if (container) {
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
}

// ─── Button Ripple Effect ─────────────────────────────────────
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn');
  if (!btn) return;

  const ripple = document.createElement('span');
  ripple.className = 'btn-ripple';
  const rect = btn.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  ripple.style.cssText = `
    width: ${size}px; height: ${size}px;
    left: ${e.clientX - rect.left - size / 2}px;
    top: ${e.clientY - rect.top - size / 2}px;
  `;
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
});

// ─── Animated Counter ─────────────────────────────────────────
function animateCounter(el, target, prefix = '', suffix = '', duration = 1200) {
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
    const current = Math.floor(eased * target);
    el.textContent = prefix + current.toLocaleString('en-IN') + suffix;

    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = prefix + target.toLocaleString('en-IN') + suffix;
  }

  requestAnimationFrame(update);
}

// ─── Format Currency ──────────────────────────────────────────
function formatCurrency(amount, currency = 'INR') {
  const num = parseFloat(amount) || 0;
  if (currency === 'INR') {
    return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }
  return '$' + num.toFixed(2);
}

// ─── Format Date ──────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ─── Skeleton Loaders ─────────────────────────────────────────
function showSkeletons(container, count = 3) {
  container.innerHTML = Array(count).fill(`
    <div class="glass-card p-4 mb-3">
      <div class="flex items-center gap-3">
        <div class="skeleton w-10 h-10 rounded-lg flex-shrink-0"></div>
        <div class="flex-1">
          <div class="skeleton h-4 w-3/4 mb-2"></div>
          <div class="skeleton h-3 w-1/2"></div>
        </div>
        <div class="skeleton h-5 w-20"></div>
      </div>
    </div>
  `).join('');
}

// ─── Dark / Light Mode Toggle ─────────────────────────────────
function initTheme() {
  const saved = localStorage.getItem('fw_theme') || 'dark';
  applyTheme(saved);
}

function applyTheme(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  document.body.classList.toggle('light-mode', theme === 'light');
  localStorage.setItem('fw_theme', theme);
}

function toggleTheme() {
  const current = localStorage.getItem('fw_theme') || 'dark';
  applyTheme(current === 'dark' ? 'light' : 'dark');
  updateThemeIcon();
}

function updateThemeIcon() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const isDark = localStorage.getItem('fw_theme') === 'dark';
  btn.innerHTML = `<i class="fa-solid ${isDark ? 'fa-sun' : 'fa-moon'}"></i>`;
}

// ─── Sidebar Active Link ───────────────────────────────────────
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') {
      item.classList.add('active');
    } else if (href === '/' && path === '/') {
      item.classList.add('active');
    } else if (href === '/dashboard' && path === '/dashboard') {
      item.classList.add('active');
    }
  });
}

// ─── Mobile Sidebar ────────────────────────────────────────────
function initMobileSidebar() {
  const toggleBtn = document.getElementById('mobile-menu-btn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobile-overlay');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (overlay) overlay.classList.toggle('show');
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }
}

// ─── Logout ────────────────────────────────────────────────────
function logout() {
  clearAuth();
  showToast('Logged out successfully.', 'info');
  setTimeout(() => window.location.href = '/login', 500);
}

// ─── Populate User Info in Sidebar ────────────────────────────
function populateUserInfo() {
  const user = getUser();
  if (!user) return;

  const nameEl = document.getElementById('sidebar-username');
  const emailEl = document.getElementById('sidebar-email');
  const avatarEl = document.getElementById('sidebar-avatar');

  if (nameEl) nameEl.textContent = user.full_name || user.username || 'User';
  if (emailEl) emailEl.textContent = user.email || '';
  if (avatarEl) {
    if (user.profile_pic) {
      avatarEl.innerHTML = `<img src="${user.profile_pic}" class="w-full h-full object-cover rounded-full" />`;
    } else {
      const initials = (user.full_name || user.username || 'U').charAt(0).toUpperCase();
      avatarEl.textContent = initials;
    }
  }
}

// ─── Global Quick Add (topbar button – redirects to transactions) ─
function openQuickAdd() {
  window.location.href = '/transactions';
}

// ─── Page Load Animation ───────────────────────────────────────
window.addEventListener('load', () => {
  const loading = document.getElementById('loading-screen');
  if (loading) {
    loading.style.transition = 'opacity 0.3s';
    loading.style.opacity = '0';
    setTimeout(() => loading.remove(), 300);
  }

  initTheme();
  updateThemeIcon();
  setActiveNav();
  initMobileSidebar();
  populateUserInfo();
});

// ─── Staggered entrance animations for cards ─────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Stat cards get a small stagger via CSS animation-delay
  document.querySelectorAll('.stat-card').forEach((el, i) => {
    el.style.animationDelay = `${i * 80}ms`;
    el.classList.add('anim-fade-up');
  });

  // Glass cards stagger slightly
  document.querySelectorAll('.glass-card').forEach((el, i) => {
    el.style.animationDelay = `${80 + i * 60}ms`;
    el.classList.add('anim-fade-up');
  });
});
