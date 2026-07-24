/* FinWise – Charts/Analytics JavaScript */

requireAuth();

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(99,102,241,0.08)';

let barChart, savingsChart, pieChart, weeklyChart;
const now = new Date();

async function loadAllCharts() {
  const period = parseInt(document.getElementById('chart-period')?.value || 6);
  const month = parseInt(document.getElementById('pie-month')?.value || now.getMonth() + 1);
  const year = now.getFullYear();

  await Promise.all([
    loadBarChart(period),
    loadSavingsChart(period),
    loadPieChart(month, year),
    loadWeeklyChart(),
    loadBudgetProgress(month, year),
  ]);
}

// ─── Income vs Expense Bar Chart ─────────────────────────────
async function loadBarChart(months = 6) {
  const res = await apiFetch(`/charts/income-vs-expense?months=${months}`);
  if (!res || !res.ok) return;

  const { labels, income, expense } = res.data;
  const ctx = document.getElementById('bar-chart');
  if (!ctx) return;

  if (barChart) barChart.destroy();

  barChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Income',
          data: income,
          backgroundColor: 'rgba(99,102,241,0.65)',
          borderColor: '#6366f1',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        },
        {
          label: 'Expenses',
          data: expense,
          backgroundColor: 'rgba(239,68,68,0.55)',
          borderColor: '#ef4444',
          borderWidth: 2,
          borderRadius: 8,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 1000, easing: 'easeOutQuart' },
      plugins: {
        legend: {
          labels: { usePointStyle: true, pointStyle: 'circle', padding: 20 },
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ₹${ctx.raw.toLocaleString('en-IN')}`,
          },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: 'rgba(99,102,241,0.07)' },
          ticks: { callback: v => '₹' + (v >= 1000 ? Math.round(v/1000) + 'k' : v) },
        },
      },
    },
  });
}

// ─── Savings Trend Line Chart ─────────────────────────────────
async function loadSavingsChart(months = 6) {
  const res = await apiFetch(`/charts/savings-trend?months=${months}`);
  if (!res || !res.ok) return;

  const { labels, monthly_savings, cumulative_savings } = res.data;
  const ctx = document.getElementById('savings-chart');
  if (!ctx) return;

  if (savingsChart) savingsChart.destroy();

  savingsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Monthly Savings',
          data: monthly_savings,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99,102,241,0.1)',
          borderWidth: 2.5,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#6366f1',
          pointRadius: 4,
        },
        {
          label: 'Cumulative',
          data: cumulative_savings,
          borderColor: '#a855f7',
          borderWidth: 2,
          fill: false,
          tension: 0.4,
          borderDash: [5, 5],
          pointRadius: 3,
          pointBackgroundColor: '#a855f7',
        },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 1000 },
      plugins: {
        legend: { labels: { usePointStyle: true, pointStyle: 'circle', padding: 20 } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.dataset.label}: ₹${ctx.raw.toLocaleString('en-IN')}` } },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: 'rgba(99,102,241,0.07)' },
          ticks: { callback: v => '₹' + (v >= 1000 ? Math.round(v/1000) + 'k' : v) },
        },
      },
    },
  });
}

// ─── Category Pie Chart ───────────────────────────────────────
async function loadPieChart(month, year) {
  const res = await apiFetch(`/charts/category-pie?month=${month}&year=${year}`);
  if (!res || !res.ok) return;

  const { labels, data, colors, percentages } = res.data;
  const ctx = document.getElementById('pie-chart');
  if (!ctx) return;

  if (pieChart) pieChart.destroy();

  if (!data.length) {
    ctx.parentElement.innerHTML = '<div class="text-center py-8 text-slate-400 text-sm">No expense data for this period</div>';
    return;
  }

  pieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#1e293b',
        hoverOffset: 12,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '60%',
      animation: { duration: 1000 },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ₹${ctx.raw.toLocaleString('en-IN')} (${percentages[ctx.dataIndex]}%)`,
          },
        },
      },
    },
  });

  // Legend
  const legend = document.getElementById('pie-legend');
  if (legend) {
    legend.innerHTML = labels.map((l, i) => `
      <div class="flex items-center gap-2 text-xs">
        <span class="inline-block w-3 h-3 rounded-sm flex-shrink-0" style="background:${colors[i]}"></span>
        <span class="text-slate-300 flex-1 truncate">${l}</span>
        <span class="text-white font-semibold">₹${data[i]?.toLocaleString('en-IN')}</span>
        <span class="text-slate-500">${percentages[i]}%</span>
      </div>`).join('');
  }
}

// ─── Weekly Spending Bar Chart ────────────────────────────────
async function loadWeeklyChart() {
  const res = await apiFetch('/charts/weekly-spending');
  if (!res || !res.ok) return;

  const { labels, amounts, is_today } = res.data;
  const ctx = document.getElementById('weekly-spending-chart');
  if (!ctx) return;

  if (weeklyChart) weeklyChart.destroy();

  weeklyChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Spending',
        data: amounts,
        backgroundColor: labels.map((_, i) => is_today[i] ? '#6366f1' : 'rgba(99,102,241,0.3)'),
        borderRadius: 8,
        borderWidth: 0,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: { duration: 800 },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.raw.toLocaleString('en-IN')}` } },
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: 'rgba(99,102,241,0.07)' },
          ticks: { callback: v => '₹' + (v >= 1000 ? Math.round(v/1000) + 'k' : v) },
        },
      },
    },
  });

  // Stats below chart
  const total = amounts.reduce((a, b) => a + b, 0);
  const avg = amounts.reduce((a, b) => a + b, 0) / 7;
  const max = Math.max(...amounts);
  const id = el => document.getElementById(el);
  if (id('weekly-total')) id('weekly-total').textContent = formatCurrency(total);
  if (id('daily-avg')) id('daily-avg').textContent = formatCurrency(avg);
  if (id('highest-day')) id('highest-day').textContent = formatCurrency(max);
}

// ─── Budget Progress ──────────────────────────────────────────
async function loadBudgetProgress(month, year) {
  const res = await apiFetch(`/charts/budget-progress?month=${month}&year=${year}`);
  const el = document.getElementById('budget-progress-section');
  if (!el) return;

  if (!res || !res.ok || !res.data.has_budget) {
    el.innerHTML = `<div class="text-center py-6 text-slate-400 text-sm">
      No budget set for this month.
      <a href="/budget" class="block mt-2 text-indigo-400 hover:underline">Set a budget</a>
    </div>`;
    return;
  }

  const d = res.data;
  const pct = Math.min(d.percentage_used, 100);
  const colorClass = pct >= 100 ? 'danger' : pct >= 80 ? 'warning' : 'success';

  el.innerHTML = `
    <div class="grid grid-cols-3 gap-6 mb-6">
      <div class="text-center p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
        <div class="text-2xl font-black gradient-text">₹${(d.total_budget||0).toLocaleString('en-IN')}</div>
        <div class="text-xs text-slate-400 mt-1">Total Budget</div>
      </div>
      <div class="text-center p-4 rounded-xl bg-red-500/10 border border-red-500/20">
        <div class="text-2xl font-black text-red-400">₹${(d.total_spent||0).toLocaleString('en-IN')}</div>
        <div class="text-xs text-slate-400 mt-1">Total Spent</div>
      </div>
      <div class="text-center p-4 rounded-xl ${d.is_over_budget ? 'bg-red-500/10 border-red-500/20' : 'bg-green-500/10 border-green-500/20'} border">
        <div class="text-2xl font-black ${d.is_over_budget ? 'text-red-400' : 'text-green-400'}">₹${Math.abs(d.remaining||0).toLocaleString('en-IN')}</div>
        <div class="text-xs text-slate-400 mt-1">${d.is_over_budget ? 'Over Budget' : 'Remaining'}</div>
      </div>
    </div>
    <div class="mb-2 flex justify-between text-sm">
      <span class="text-slate-400">Budget Usage</span>
      <span class="font-bold ${pct >= 100 ? 'text-red-400' : pct >= 80 ? 'text-yellow-400' : 'text-green-400'}">${pct.toFixed(1)}%</span>
    </div>
    <div class="progress-bar" style="height:12px">
      <div class="progress-fill ${colorClass}" style="width:${pct}%"></div>
    </div>`;
}

// ─── Event Listeners ──────────────────────────────────────────
document.getElementById('chart-period')?.addEventListener('change', () => {
  const period = parseInt(document.getElementById('chart-period').value);
  loadBarChart(period);
  loadSavingsChart(period);
});

document.getElementById('pie-month')?.addEventListener('change', () => {
  const month = parseInt(document.getElementById('pie-month').value);
  loadPieChart(month, new Date().getFullYear());
  loadBudgetProgress(month, new Date().getFullYear());
});

// Init
document.getElementById('pie-month').value = now.getMonth() + 1;
loadAllCharts();
