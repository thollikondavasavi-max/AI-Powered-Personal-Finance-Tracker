/* FinWise – Budget & Goals JavaScript */

requireAuth();

const now = new Date();
let currentMonth = now.getMonth() + 1;
let currentYear = now.getFullYear();

async function init() {
  setupMonthSelector();
  setupBudgetForm();
  setupGoalForm();
  setupAlertThreshold();
  await Promise.all([loadBudget(), loadGoals(), loadAIRecommendation()]);
}

// ─── Month Selector ───────────────────────────────────────────
function setupMonthSelector() {
  const sel = document.getElementById('budget-month');
  if (!sel) return;
  sel.value = currentMonth;
  sel.addEventListener('change', () => {
    currentMonth = parseInt(sel.value);
    loadBudget();
  });
}

// ─── Load Budget ──────────────────────────────────────────────
async function loadBudget() {
  const el = document.getElementById('budget-overview');
  if (el) el.innerHTML = '<div class="text-center py-8"><i class="fa-solid fa-spinner fa-spin text-2xl text-indigo-400"></i></div>';

  const res = await apiFetch(`/budget?month=${currentMonth}&year=${currentYear}`);
  if (!res) return;

  if (!res.ok || !res.data.budget) {
    if (el) el.innerHTML = `
      <div class="text-center py-8 text-slate-400">
        <i class="fa-solid fa-bullseye text-3xl mb-3 block text-slate-600"></i>
        No budget set for this month.
        <button onclick="openBudgetModal()" class="block mt-3 mx-auto btn btn-primary btn-sm">
          <i class="fa-solid fa-plus"></i> Set Budget
        </button>
      </div>`;
    return;
  }

  const d = res.data;
  const budget = d.budget?.budget || d.budget;
  const pct = Math.min(d.percentage_used || 0, 100);
  const colorClass = pct >= 100 ? 'danger' : pct >= 80 ? 'warning' : 'success';

  if (el) el.innerHTML = `
    <div class="space-y-6">
      <!-- Summary row -->
      <div class="grid grid-cols-3 gap-4 text-center">
        <div class="p-3 rounded-xl bg-indigo-500/10">
          <div class="text-xl font-black gradient-text">₹${(budget?.total_budget || d.budget?.total_budget || 0).toLocaleString('en-IN')}</div>
          <div class="text-xs text-slate-400 mt-1">Total Budget</div>
        </div>
        <div class="p-3 rounded-xl bg-red-500/10">
          <div class="text-xl font-black text-red-400">₹${(d.total_spent || 0).toLocaleString('en-IN')}</div>
          <div class="text-xs text-slate-400 mt-1">Spent</div>
        </div>
        <div class="p-3 rounded-xl ${d.is_over_budget ? 'bg-red-500/10' : 'bg-green-500/10'}">
          <div class="text-xl font-black ${d.is_over_budget ? 'text-red-400' : 'text-green-400'}">₹${Math.abs(d.remaining || 0).toLocaleString('en-IN')}</div>
          <div class="text-xs text-slate-400 mt-1">${d.is_over_budget ? 'Over!' : 'Remaining'}</div>
        </div>
      </div>

      <!-- Progress -->
      <div>
        <div class="flex justify-between text-sm mb-2">
          <span class="text-slate-400">${pct.toFixed(1)}% used</span>
          ${d.is_over_budget ? '<span class="badge badge-expense"><i class="fa-solid fa-exclamation-triangle text-xs"></i> Over Budget</span>' :
            d.is_near_limit ? '<span class="badge badge-warning"><i class="fa-solid fa-triangle-exclamation text-xs"></i> Near Limit</span>' :
            '<span class="badge badge-income"><i class="fa-solid fa-check text-xs"></i> On Track</span>'}
        </div>
        <div class="progress-bar" style="height:12px">
          <div class="progress-fill ${colorClass}" style="width:${pct}%"></div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-3">
        <button onclick="openBudgetModal()" class="btn btn-secondary btn-sm">
          <i class="fa-solid fa-pencil"></i> Edit Budget
        </button>
      </div>
    </div>`;
}

// ─── Budget Modal ─────────────────────────────────────────────
function openBudgetModal() {
  const modal = document.getElementById('budget-modal');
  if (modal) modal.classList.add('open');

  // Populate month select
  const sel = document.getElementById('modal-month');
  if (sel) {
    const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    sel.innerHTML = months.map((m, i) => `<option value="${i+1}" ${i+1 === currentMonth ? 'selected' : ''}>${m}</option>`).join('');
  }
  document.getElementById('modal-year').value = currentYear;
}

function closeBudgetModal() {
  document.getElementById('budget-modal')?.classList.remove('open');
}

function setupBudgetForm() {
  document.getElementById('budget-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const res = await apiFetch('/budget', {
      method: 'POST',
      body: JSON.stringify({
        month: parseInt(document.getElementById('modal-month').value),
        year: parseInt(document.getElementById('modal-year').value),
        total_budget: parseFloat(document.getElementById('modal-budget').value),
        alert_threshold: parseFloat(document.getElementById('alert-threshold').value),
      }),
    });

    if (res && res.ok) {
      showToast('Budget saved!', 'success');
      closeBudgetModal();
      loadBudget();
    } else {
      showToast(res?.data?.error || 'Error saving budget.', 'error');
    }
  });
}

function setupAlertThreshold() {
  const slider = document.getElementById('alert-threshold');
  const label = document.getElementById('threshold-label');
  if (slider && label) {
    slider.addEventListener('input', () => {
      label.textContent = `${slider.value}% — Alert when ${slider.value}% is spent`;
    });
  }
}

// ─── Load AI Budget Recommendation ────────────────────────────
async function loadAIRecommendation() {
  const el = document.getElementById('ai-budget-rec');
  if (!el) return;

  const res = await apiFetch('/ai/budget-recommendation');
  if (!res || !res.ok) return;

  const { recommendation: r } = res.data;

  el.innerHTML = `
    <div class="space-y-3">
      <div class="text-center p-3 rounded-xl bg-purple-500/10 border border-purple-500/20">
        <div class="text-lg font-black text-purple-400">₹${(r.recommended_budget || 0).toLocaleString('en-IN')}</div>
        <div class="text-xs text-slate-400">Recommended Monthly Budget</div>
      </div>
      <div class="space-y-2 text-xs">
        <div class="flex justify-between">
          <span class="text-slate-400">Needs (50%)</span>
          <span class="font-semibold text-blue-400">₹${(r.needs_budget || 0).toLocaleString('en-IN')}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-400">Wants (30%)</span>
          <span class="font-semibold text-purple-400">₹${(r.wants_budget || 0).toLocaleString('en-IN')}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-400">Savings (20%)</span>
          <span class="font-semibold text-green-400">₹${(r.savings_target || 0).toLocaleString('en-IN')}</span>
        </div>
      </div>
      <div class="p-2 rounded-lg bg-indigo-500/10 text-xs text-indigo-300">${r.insight || ''}</div>
    </div>`;
}

// ─── Savings Goals ────────────────────────────────────────────
async function loadGoals() {
  const el = document.getElementById('goals-grid');
  if (!el) return;

  const res = await apiFetch('/budget/savings-goals');
  if (!res || !res.ok) return;

  const { goals } = res.data;

  if (!goals.length) {
    el.innerHTML = `
      <div class="col-span-full text-center py-12 text-slate-400">
        <i class="fa-solid fa-bullseye text-4xl mb-4 block text-slate-700"></i>
        No savings goals yet.<br/>
        <button onclick="openGoalModal()" class="mt-4 btn btn-primary btn-sm">
          <i class="fa-solid fa-plus"></i> Add Your First Goal
        </button>
      </div>`;
    return;
  }

  el.innerHTML = goals.map(g => `
    <div class="glass-card card-glow p-5" data-aos="fade-up">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background:${g.color}22;color:${g.color}">
            <i class="fa-solid ${g.icon}"></i>
          </div>
          <div>
            <div class="font-semibold text-sm text-white">${escapeHtml(g.name)}</div>
            ${g.deadline ? `<div class="text-xs text-slate-500">Due: ${formatDate(g.deadline)}</div>` : ''}
          </div>
        </div>
        <div class="flex items-center gap-1">
          ${g.is_completed ? '<span class="badge badge-income"><i class="fa-solid fa-check text-xs"></i> Done</span>' : ''}
          <button class="btn btn-ghost btn-sm" onclick="editGoal(${JSON.stringify(g).replace(/"/g,'&quot;')})">
            <i class="fa-solid fa-pencil text-xs"></i>
          </button>
          <button class="btn btn-ghost btn-sm" onclick="deleteGoal(${g.id})">
            <i class="fa-solid fa-trash text-xs text-red-400"></i>
          </button>
        </div>
      </div>

      <div class="flex justify-between text-sm mb-1">
        <span class="text-slate-400">₹${(g.current_amount||0).toLocaleString('en-IN')}</span>
        <span class="font-bold">₹${(g.target_amount||0).toLocaleString('en-IN')}</span>
      </div>

      <div class="progress-bar mb-2">
        <div class="progress-fill ${g.is_completed ? 'success' : ''}" style="width:${g.progress_percent}%;background:${g.color}"></div>
      </div>

      <div class="flex justify-between items-center">
        <span class="text-xs text-slate-400">${g.progress_percent}% complete</span>
        <span class="text-xs font-semibold" style="color:${g.color}">₹${((g.target_amount||0)-(g.current_amount||0)).toLocaleString('en-IN')} to go</span>
      </div>
    </div>`).join('');
}

function openGoalModal(goal = null) {
  const modal = document.getElementById('goal-modal');
  if (!modal) return;
  document.getElementById('goal-form').reset();
  document.getElementById('goal-edit-id').value = '';
  document.getElementById('goal-modal-title').textContent = 'Add Savings Goal';
  if (goal) {
    document.getElementById('goal-modal-title').textContent = 'Edit Savings Goal';
    document.getElementById('goal-edit-id').value = goal.id;
    document.getElementById('goal-name').value = goal.name;
    document.getElementById('goal-target').value = goal.target_amount;
    document.getElementById('goal-current').value = goal.current_amount;
    if (goal.deadline) document.getElementById('goal-deadline').value = goal.deadline;
    document.getElementById('goal-icon').value = goal.icon;
    document.getElementById('goal-color').value = goal.color;
  }
  modal.classList.add('open');
}

function closeGoalModal() {
  document.getElementById('goal-modal')?.classList.remove('open');
}

function editGoal(g) { openGoalModal(g); }

async function deleteGoal(id) {
  if (!confirm('Delete this goal?')) return;
  const res = await apiFetch(`/budget/savings-goals/${id}`, { method: 'DELETE' });
  if (res && res.ok) { showToast('Goal deleted.', 'success'); loadGoals(); }
  else showToast('Error deleting goal.', 'error');
}

function setupGoalForm() {
  document.getElementById('goal-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const editId = document.getElementById('goal-edit-id').value;
    const body = {
      name: document.getElementById('goal-name').value.trim(),
      target_amount: parseFloat(document.getElementById('goal-target').value),
      current_amount: parseFloat(document.getElementById('goal-current').value || 0),
      deadline: document.getElementById('goal-deadline').value || null,
      icon: document.getElementById('goal-icon').value,
      color: document.getElementById('goal-color').value,
    };

    const url = editId ? `/budget/savings-goals/${editId}` : '/budget/savings-goals';
    const method = editId ? 'PUT' : 'POST';
    const res = await apiFetch(url, { method, body: JSON.stringify(body) });

    if (res && res.ok) {
      showToast(editId ? 'Goal updated!' : 'Goal created!', 'success');
      closeGoalModal();
      loadGoals();
    } else {
      showToast(res?.data?.error || 'Error saving goal.', 'error');
    }
  });
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

init();
