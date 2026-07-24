/* FinWise – Dashboard JavaScript */

requireAuth();

let incomeExpenseChart, categoryChart, weeklyChart;
const now = new Date();
let currentMonth = now.getMonth() + 1;
let currentYear = now.getFullYear();

// ─── Greet User ───────────────────────────────────────────────
function setGreeting() {
  const hour = now.getHours();
  const user = getUser();
  const name = user ? (user.full_name || user.username) : 'there';
  let greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  const el = document.getElementById('greeting-text');
  if (el) el.textContent = `${greeting}, ${name}! Here's your financial overview.`;
}

// ─── Month Selector ───────────────────────────────────────────
function initMonthSelector() {
  const sel = document.getElementById('month-selector');
  if (!sel) return;
  sel.value = currentMonth;
  sel.addEventListener('change', () => {
    currentMonth = parseInt(sel.value);
    loadDashboard();
  });
}

// ─── Load Summary Stats ───────────────────────────────────────
async function loadSummary() {
  const res = await apiFetch(`/dashboard/summary?month=${currentMonth}&year=${currentYear}`);
  if (!res || !res.ok) return;

  const { summary, budget } = res.data;

  // Animate stat counters
  const balance = parseFloat(summary.current_balance) || 0;
  const income = parseFloat(summary.monthly_income) || 0;
  const expense = parseFloat(summary.monthly_expense) || 0;
  const savings = parseFloat(summary.monthly_savings) || 0;

  const balanceEl = document.getElementById('stat-balance');
  const incomeEl = document.getElementById('stat-income');
  const expenseEl = document.getElementById('stat-expense');
  const savingsEl = document.getElementById('stat-savings');

  if (balanceEl) animateCounter(balanceEl, Math.abs(balance), balance < 0 ? '-₹' : '₹');
  if (incomeEl) animateCounter(incomeEl, income, '₹');
  if (expenseEl) animateCounter(expenseEl, expense, '₹');
  if (savingsEl) animateCounter(savingsEl, savings, '₹');

  // Savings rate
  const savingsRateEl = document.getElementById('stat-savings-change');
  if (savingsRateEl && income > 0) {
    const rate = ((savings / income) * 100).toFixed(1);
    savingsRateEl.querySelector('span').textContent = `${rate}% savings rate`;
  }

  // Budget alert
  if (budget && budget.is_near_limit) {
    const alertEl = document.getElementById('budget-alert');
    const textEl = document.getElementById('budget-alert-text');
    if (alertEl && textEl) {
      alertEl.classList.remove('hidden');
      textEl.textContent = budget.is_over_budget
        ? `Over budget! You've spent ₹${budget.total_spent?.toLocaleString('en-IN')} of ₹${budget.budget?.total_budget?.toLocaleString('en-IN')} budget.`
        : `You've used ${budget.percentage_used}% of your ₹${budget.budget?.total_budget?.toLocaleString('en-IN')} budget.`;
    }
  }

  // Budget section
  renderBudgetSection(budget);
}

function renderBudgetSection(budget) {
  const el = document.getElementById('budget-section');
  if (!el) return;

  if (!budget) {
    el.innerHTML = `
      <div class="text-center py-4 text-slate-400 text-sm">
        <i class="fa-solid fa-circle-info mb-2 block text-xl"></i>
        No budget set for this month.
        <a href="/budget" class="block mt-2 text-indigo-400 hover:underline">Set Budget</a>
      </div>`;
    return;
  }

  const pct = Math.min(budget.percentage_used || 0, 100);
  const colorClass = pct >= 100 ? 'danger' : pct >= 80 ? 'warning' : 'success';

  el.innerHTML = `
    <div class="space-y-4">
      <div class="flex justify-between text-sm">
        <span class="text-slate-400">Spent</span>
        <span class="font-semibold">₹${(budget.total_spent || 0).toLocaleString('en-IN')}</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill ${colorClass}" style="width:${pct}%"></div>
      </div>
      <div class="flex justify-between text-xs text-slate-400">
        <span>${pct.toFixed(1)}% used</span>
        <span>₹${(budget.budget?.total_budget || 0).toLocaleString('en-IN')} total</span>
      </div>
      <div class="flex justify-between p-3 rounded-xl ${budget.is_over_budget ? 'bg-red-500/10 border border-red-500/20' : 'bg-green-500/10 border border-green-500/20'}">
        <span class="text-xs text-slate-400">Remaining</span>
        <span class="text-sm font-bold ${budget.is_over_budget ? 'text-red-400' : 'text-green-400'}">
          ${budget.is_over_budget ? '-' : ''}₹${Math.abs(budget.remaining || 0).toLocaleString('en-IN')}
        </span>
      </div>
    </div>`;
}

// ─── Load Recent Transactions ──────────────────────────────────
async function loadRecentTransactions() {
  const res = await apiFetch('/dashboard/recent-transactions?limit=8');
  if (!res || !res.ok) return;

  const { transactions } = res.data;
  const el = document.getElementById('recent-transactions');
  if (!el) return;

  if (!transactions.length) {
    el.innerHTML = `<div class="text-center py-8 text-slate-400 text-sm">
      <i class="fa-solid fa-inbox text-2xl mb-2 block"></i>
      No transactions yet. <a href="/transactions" class="text-indigo-400">Add your first one!</a>
    </div>`;
    return;
  }

  el.innerHTML = transactions.map((t) => `
    <div class="txn-row">
      <div class="cat-icon flex-shrink-0" style="background:${t.category_color}22;color:${t.category_color}">
        <i class="fa-solid ${t.category_icon}"></i>
      </div>
      <div class="flex-1 min-w-0">
        <div class="txn-desc">${escapeHtml(t.description)}</div>
        <div class="txn-meta">${t.category_name} · ${formatDate(t.date)}</div>
      </div>
      <div class="txn-amount ${t.type === 'income' ? 'income' : 'expense'}">
        ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
      </div>
    </div>
  `).join('');
}

// ─── Charts ───────────────────────────────────────────────────
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(99,102,241,0.1)';

async function loadIncomeExpenseChart() {
  const res = await apiFetch('/charts/income-vs-expense?months=6');
  if (!res || !res.ok) return;

  const { labels, income, expense } = res.data;
  const ctx = document.getElementById('income-expense-chart');
  if (!ctx) return;

  if (incomeExpenseChart) incomeExpenseChart.destroy();

  incomeExpenseChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Income',
          data: income,
          backgroundColor: 'rgba(99,102,241,0.6)',
          borderColor: '#6366f1',
          borderWidth: 2,
          borderRadius: 6,
        },
        {
          label: 'Expenses',
          data: expense,
          backgroundColor: 'rgba(239,68,68,0.5)',
          borderColor: '#ef4444',
          borderWidth: 2,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: 'rgba(99,102,241,0.08)' }, ticks: { callback: v => '₹' + (v >= 1000 ? (v/1000)+'k' : v) } },
      },
    },
  });
}

async function loadCategoryChart() {
  const res = await apiFetch(`/charts/category-pie?month=${currentMonth}&year=${currentYear}`);
  if (!res || !res.ok) return;

  const { labels, data, colors } = res.data;
  const ctx = document.getElementById('category-chart');
  if (!ctx) return;

  if (categoryChart) categoryChart.destroy();

  if (!data.length) {
    ctx.parentElement.innerHTML = '<div class="text-center py-8 text-slate-400 text-sm">No expense data for this month</div>';
    return;
  }

  categoryChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data, backgroundColor: colors, borderWidth: 0, hoverOffset: 8 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.raw.toLocaleString('en-IN')}` } },
      },
    },
  });

  // Legend
  const legend = document.getElementById('category-legend');
  if (legend) {
    legend.innerHTML = labels.slice(0, 4).map((l, i) => `
      <div class="flex items-center gap-2 text-xs">
        <span class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0" style="background:${colors[i]}"></span>
        <span class="text-slate-400 flex-1 truncate">${l}</span>
        <span class="text-white font-medium">₹${data[i]?.toLocaleString('en-IN')}</span>
      </div>`).join('');
  }
}

async function loadWeeklyChart() {
  const res = await apiFetch('/charts/weekly-spending');
  if (!res || !res.ok) return;

  const { labels, amounts } = res.data;
  const ctx = document.getElementById('weekly-chart');
  if (!ctx) return;

  if (weeklyChart) weeklyChart.destroy();

  weeklyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: amounts,
        backgroundColor: labels.map((_, i) => res.data.is_today[i] ? '#6366f1' : 'rgba(99,102,241,0.3)'),
        borderRadius: 6,
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: { display: false },
      },
    },
  });
}

// ─── Escape HTML ──────────────────────────────────────────────
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
}

// ─── Quick Add transaction from topbar ────────────────────────
function openQuickAdd() {
  window.location.href = '/transactions';
}

// ─── Initialize Dashboard ─────────────────────────────────────
async function loadDashboard() {
  setGreeting();
  // Load all data in parallel
  await Promise.all([
    loadSummary(),
    loadRecentTransactions(),
    loadIncomeExpenseChart(),
    loadCategoryChart(),
    loadWeeklyChart(),
  ]);
}

// Run on page load
loadDashboard();
