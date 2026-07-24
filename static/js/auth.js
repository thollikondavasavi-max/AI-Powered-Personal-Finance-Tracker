/* FinWise – Authentication JavaScript */

// ─── Google Sign-In Callback ──────────────────────────────────
// Called by Google Identity Services after the user picks an account.
async function handleGoogleSignIn(googleResponse) {
  const btn = document.getElementById('google-loading');
  if (btn) {
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>Signing in with Google...';
    btn.classList.remove('hidden');
  }

  showToast('Verifying with Google…', 'info');

  const res = await apiFetch('/auth/google', {
    method: 'POST',
    body: JSON.stringify({ credential: googleResponse.credential }),
  });

  if (res && res.ok) {
    setToken(res.data.access_token);
    setUser(res.data.user);
    showToast(res.data.message || 'Welcome!', 'success');
    window.location.href = '/dashboard';
  } else {
    const msg = res?.data?.error || 'Google Sign-In failed. Please try again.';
    showToast(msg, 'error');
    if (btn) btn.classList.add('hidden');
  }
}

// ─── Login Form ────────────────────────────────────────────────
const loginForm = document.getElementById('login-form');
if (loginForm) {
  redirectIfAuth();

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = loginForm.querySelector('[type=submit]');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing in...';

    const identifier = loginForm.querySelector('#identifier').value.trim();
    const password = loginForm.querySelector('#password').value;

    const res = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ identifier, password }),
    });

    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-arrow-right-to-bracket"></i> Sign In';

    if (res && res.ok) {
      setToken(res.data.access_token);
      setUser(res.data.user);
      showToast(res.data.message || 'Welcome back!', 'success');
      window.location.href = '/dashboard';
    } else {
      const msg = res?.data?.error || 'Login failed. Please try again.';
      showToast(msg, 'error');
      // CSS shake animation on error
      const card = document.querySelector('.auth-card');
      if (card) {
        card.style.animation = 'none';
        card.style.animation = 'shake 0.4s ease';
      }
    }
  });
}

// ─── Signup Form ───────────────────────────────────────────────
const signupForm = document.getElementById('signup-form');
if (signupForm) {
  redirectIfAuth();

  const passwordInput = document.getElementById('password');
  const strengthBar   = document.getElementById('strength-bar');
  const strengthText  = document.getElementById('strength-text');

  if (passwordInput && strengthBar) {
    passwordInput.addEventListener('input', () => {
      const pw = passwordInput.value;
      const strength = getPasswordStrength(pw);
      strengthBar.style.width = strength.percent + '%';
      strengthBar.className = 'progress-fill ' + strength.class;
      if (strengthText) {
        strengthText.textContent = strength.label;
        strengthText.className = 'text-xs font-semibold ' + strength.textClass;
      }
    });
  }

  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = signupForm.querySelector('[type=submit]');

    const password = signupForm.querySelector('#password').value;
    const confirm  = signupForm.querySelector('#confirm-password').value;

    if (password !== confirm) {
      showToast('Passwords do not match.', 'error');
      return;
    }

    if (!signupForm.querySelector('#terms').checked) {
      showToast('Please accept the terms to continue.', 'error');
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating account...';

    const res = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username:  signupForm.querySelector('#username').value.trim(),
        email:     signupForm.querySelector('#email').value.trim(),
        password,
        full_name: signupForm.querySelector('#full-name').value.trim(),
      }),
    });

    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';

    if (res && res.ok) {
      setToken(res.data.access_token);
      setUser(res.data.user);
      showToast('Account created! Welcome to FinWise 🎉', 'success');
      window.location.href = '/dashboard';
    } else {
      showToast(res?.data?.error || 'Registration failed.', 'error');
    }
  });

}

// ─── Password Strength ─────────────────────────────────────────
function getPasswordStrength(pw) {
  let score = 0;
  if (pw.length >= 8)          score++;
  if (pw.length >= 12)         score++;
  if (/[A-Z]/.test(pw))       score++;
  if (/[0-9]/.test(pw))       score++;
  if (/[^a-zA-Z0-9]/.test(pw)) score++;

  if (score <= 1) return { percent: 20,  class: 'danger',  label: 'Weak',        textClass: 'text-red-400'    };
  if (score === 2) return { percent: 40,  class: 'danger',  label: 'Fair',        textClass: 'text-orange-400' };
  if (score === 3) return { percent: 60,  class: 'warning', label: 'Good',        textClass: 'text-yellow-400' };
  if (score === 4) return { percent: 80,  class: 'success', label: 'Strong',      textClass: 'text-green-400'  };
  return              { percent: 100, class: 'success', label: 'Very Strong', textClass: 'text-emerald-400' };
}

// ─── Toggle Password Visibility ────────────────────────────────
document.querySelectorAll('.toggle-password').forEach(btn => {
  btn.addEventListener('click', () => {
    const input = document.getElementById(btn.dataset.target);
    if (!input) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    btn.querySelector('i').className =
      `fa-solid ${input.type === 'password' ? 'fa-eye' : 'fa-eye-slash'}`;
  });
});
