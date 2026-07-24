/* FinWise – Profile JavaScript */

requireAuth();

async function init() {
  await loadProfile();
  setupForms();
}

async function loadProfile() {
  const res = await apiFetch('/auth/me');
  if (!res || !res.ok) return;

  const { user } = res.data;
  setUser(user);  // update stored user

  // Avatar display
  const avatarEl = document.getElementById('profile-avatar-display');
  if (avatarEl) {
    if (user.profile_pic) {
      avatarEl.innerHTML = `<img src="${user.profile_pic}" class="w-full h-full object-cover" />`;
    } else {
      avatarEl.textContent = (user.full_name || user.username || 'U').charAt(0).toUpperCase();
    }
  }

  // Set text fields
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || ''; };
  const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ''; };

  set('profile-name', user.full_name || user.username);
  set('profile-email', user.email);
  set('profile-joined', user.created_at ? `Member since ${new Date(user.created_at).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}` : '');

  setVal('pf-fullname', user.full_name);
  setVal('pf-username', user.username);
  setVal('pf-email', user.email);
  setVal('pf-phone', user.phone);
  if (document.getElementById('pf-currency')) document.getElementById('pf-currency').value = user.currency || 'INR';

  // Load stats
  await loadStats();
}

async function loadStats() {
  const res = await apiFetch('/transactions?per_page=1');
  if (res && res.ok) {
    const el = document.getElementById('stat-total-txns');
    if (el) el.textContent = res.data.total || 0;
  }

  const summaryRes = await apiFetch('/dashboard/summary');
  if (summaryRes && summaryRes.ok) {
    const { summary } = summaryRes.data;
    const el = document.getElementById('stat-total-saved');
    if (el) el.textContent = formatCurrency(summary.current_balance || 0);
  }
}

function setupForms() {
  // Profile form
  document.getElementById('profile-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const res = await apiFetch('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify({
        full_name: document.getElementById('pf-fullname').value.trim(),
        phone: document.getElementById('pf-phone').value.trim(),
        currency: document.getElementById('pf-currency').value,
      }),
    });

    if (res && res.ok) {
      setUser(res.data.user);
      showToast('Profile updated!', 'success');
      loadProfile();
    } else {
      showToast(res?.data?.error || 'Error updating profile.', 'error');
    }
  });

  // Password form
  document.getElementById('password-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newPw = document.getElementById('new-password').value;
    const confirmPw = document.getElementById('confirm-new-password').value;

    if (newPw !== confirmPw) {
      showToast('Passwords do not match.', 'error');
      return;
    }

    const res = await apiFetch('/auth/change-password', {
      method: 'PUT',
      body: JSON.stringify({
        current_password: document.getElementById('current-password').value,
        new_password: newPw,
      }),
    });

    if (res && res.ok) {
      showToast('Password changed successfully!', 'success');
      document.getElementById('password-form').reset();
    } else {
      showToast(res?.data?.error || 'Error changing password.', 'error');
    }
  });
}

async function uploadAvatar(input) {
  const file = input.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  const token = getToken();
  const res = await fetch('/api/auth/upload-avatar', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  });

  const data = await res.json();
  if (res.ok) {
    showToast('Profile picture updated!', 'success');
    loadProfile();
  } else {
    showToast(data.error || 'Upload failed.', 'error');
  }
}

init();
