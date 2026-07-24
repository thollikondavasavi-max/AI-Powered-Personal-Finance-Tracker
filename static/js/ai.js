/* FinWise – AI Insights JavaScript */

requireAuth();

async function init() {
  await Promise.all([loadInsights(), loadExpensePrediction(), loadBudgetRecommendation()]);
}

// ─── Smart Insights ───────────────────────────────────────────
async function loadInsights() {
  const el = document.getElementById('insights-grid');
  if (!el) return;

  const res = await apiFetch('/ai/insights');
  if (!res || !res.ok) return;

  const { insights } = res.data;

  if (!insights.length) {
    el.innerHTML = '<div class="text-slate-400 text-sm">No insights available. Add more transactions for personalized insights.</div>';
    return;
  }

  el.innerHTML = insights.map((insight, i) => `
    <div class="insight-card" style="border-color:${insight.color};animation-delay:${i*100}ms" data-aos="fade-up" data-aos-delay="${i*80}">
      <div class="flex items-start gap-4">
        <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style="background:${insight.color}22;color:${insight.color}">
          <i class="fa-solid ${insight.icon}"></i>
        </div>
        <div>
          <div class="font-bold text-white mb-1">${insight.title}</div>
          <div class="text-sm text-slate-300">${insight.message}</div>
        </div>
        <div class="ml-auto flex-shrink-0">
          <span class="text-xs font-semibold px-2 py-1 rounded-full" style="background:${insight.color}22;color:${insight.color}">
            ${insight.type.toUpperCase()}
          </span>
        </div>
      </div>
    </div>`).join('');
}

// ─── Expense Prediction ───────────────────────────────────────
async function loadExpensePrediction() {
  const el = document.getElementById('expense-prediction');
  if (!el) return;

  const res = await apiFetch('/ai/predict-expense', { method: 'POST', body: JSON.stringify({}) });
  if (!res || !res.ok) return;

  const p = res.data.prediction;

  const trendColor = p.trend === 'Increasing' ? '#ef4444' : p.trend === 'Decreasing' ? '#22c55e' : '#6366f1';
  const trendIcon = p.trend === 'Increasing' ? 'fa-arrow-trend-up' : p.trend === 'Decreasing' ? 'fa-arrow-trend-down' : 'fa-minus';

  el.innerHTML = `
    <div class="space-y-4">
      <div class="text-center p-5 rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-500/20">
        <div class="text-3xl font-black text-blue-400 mb-1">₹${(p.predicted_expense || 0).toLocaleString('en-IN')}</div>
        <div class="text-sm text-slate-400">Predicted ${p.next_month_name} Expenses</div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="p-3 rounded-xl bg-slate-800/50 text-center">
          <div class="text-sm font-bold text-white">₹${(p.linear_regression || 0).toLocaleString('en-IN')}</div>
          <div class="text-xs text-slate-400">Linear Regression</div>
        </div>
        <div class="p-3 rounded-xl bg-slate-800/50 text-center">
          <div class="text-sm font-bold text-white">₹${(p.random_forest || 0).toLocaleString('en-IN')}</div>
          <div class="text-xs text-slate-400">Random Forest</div>
        </div>
      </div>

      <div class="flex items-center justify-between text-sm">
        <div class="flex items-center gap-2">
          <i class="fa-solid ${trendIcon}" style="color:${trendColor}"></i>
          <span class="font-semibold" style="color:${trendColor}">Trend: ${p.trend}</span>
        </div>
        <span class="badge badge-info">
          <i class="fa-solid fa-chart-bar text-xs"></i>
          ${p.confidence} Confidence
        </span>
      </div>

      <div class="text-xs text-slate-500 p-3 rounded-lg bg-slate-800/30">
        <i class="fa-solid fa-info-circle mr-1"></i>
        Based on ${p.data_points} months of data. Ensemble of Linear Regression (40%) + Random Forest (60%).
      </div>
    </div>`;
}

// ─── Category Prediction ──────────────────────────────────────
async function predictCategory() {
  const input = document.getElementById('predict-input');
  if (!input || !input.value.trim()) {
    showToast('Enter a description to predict.', 'warning');
    return;
  }

  const resultEl = document.getElementById('prediction-result');
  if (resultEl) resultEl.classList.add('hidden');

  const res = await apiFetch('/ai/predict-category', {
    method: 'POST',
    body: JSON.stringify({ description: input.value.trim() }),
  });

  if (!res || !res.ok) {
    showToast('Prediction failed.', 'error');
    return;
  }

  const d = res.data;
  const resultDiv = document.getElementById('prediction-result');
  const catEl = document.getElementById('predicted-cat');
  const confEl = document.getElementById('pred-confidence');
  const altEl = document.getElementById('pred-alternatives');

  if (catEl) catEl.textContent = d.predicted_category;
  if (confEl) confEl.textContent = `${d.confidence}%`;

  if (altEl) {
    altEl.innerHTML = `<div class="text-slate-500 text-xs mb-1">Other possibilities:</div>` +
      (d.alternatives || []).map(a => `
        <div class="flex items-center justify-between text-xs py-1">
          <span class="text-slate-300">${a.category}</span>
          <div class="flex items-center gap-2">
            <div class="w-20 h-1.5 rounded-full bg-slate-700 overflow-hidden">
              <div class="h-full rounded-full bg-indigo-400" style="width:${a.confidence}%"></div>
            </div>
            <span class="text-slate-400">${a.confidence}%</span>
          </div>
        </div>`).join('');
  }

  if (resultDiv) resultDiv.classList.remove('hidden');

  // GSAP animation
  if (typeof gsap !== 'undefined') {
    gsap.from(resultDiv, { y: 10, opacity: 0, duration: 0.3, ease: 'power2.out' });
  }
}

function predictExample(text) {
  const input = document.getElementById('predict-input');
  if (input) {
    input.value = text;
    predictCategory();
  }
}

// ─── Budget Recommendation ────────────────────────────────────
async function loadBudgetRecommendation() {
  const el = document.getElementById('budget-recommendation');
  if (!el) return;

  const res = await apiFetch('/ai/budget-recommendation');
  if (!res || !res.ok) return;

  const r = res.data.recommendation;

  const cats = r.category_suggestions || {};
  const catHtml = Object.entries(cats).map(([name, amount]) => `
    <div class="flex items-center justify-between p-3 rounded-xl bg-slate-800/30 text-sm">
      <span class="text-slate-300">${name}</span>
      <span class="font-bold text-white">₹${amount.toLocaleString('en-IN')}</span>
    </div>`).join('');

  el.innerHTML = `
    <div class="grid lg:grid-cols-3 gap-6">
      <!-- 50/30/20 pie -->
      <div class="text-center">
        <div class="relative inline-block mb-4">
          <svg viewBox="0 0 100 100" class="w-40 h-40 -rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(99,102,241,0.1)" stroke-width="12"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="#6366f1" stroke-width="12"
              stroke-dasharray="${50 * 2.51} ${50 * 2.51}" stroke-dashoffset="0" stroke-linecap="round"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="#a855f7" stroke-width="12"
              stroke-dasharray="${30 * 2.51} ${70 * 2.51}" stroke-dashoffset="${-50 * 2.51}" stroke-linecap="round"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="#22c55e" stroke-width="12"
              stroke-dasharray="${20 * 2.51} ${80 * 2.51}" stroke-dashoffset="${-80 * 2.51}" stroke-linecap="round"/>
          </svg>
          <div class="absolute inset-0 flex flex-col items-center justify-center">
            <div class="text-xs text-slate-400">Rule</div>
            <div class="text-lg font-black gradient-text">50/30</div>
            <div class="text-xs text-slate-400">/20</div>
          </div>
        </div>

        <div class="space-y-2 text-xs text-left">
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-indigo-500"></span>
            <span class="text-slate-400">Needs 50%</span>
            <span class="ml-auto font-bold text-indigo-400">₹${(r.needs_budget||0).toLocaleString('en-IN')}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-purple-500"></span>
            <span class="text-slate-400">Wants 30%</span>
            <span class="ml-auto font-bold text-purple-400">₹${(r.wants_budget||0).toLocaleString('en-IN')}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-green-500"></span>
            <span class="text-slate-400">Savings 20%</span>
            <span class="ml-auto font-bold text-green-400">₹${(r.savings_target||0).toLocaleString('en-IN')}</span>
          </div>
        </div>
      </div>

      <!-- Category suggestions -->
      <div class="lg:col-span-2">
        <h3 class="text-sm font-bold text-slate-300 mb-3">Category-wise Budget Suggestions</h3>
        <div class="grid grid-cols-2 gap-2">
          ${catHtml}
        </div>
        <div class="mt-4 p-3 rounded-xl border border-green-500/20 bg-green-500/5 text-sm text-green-300">
          <i class="fa-solid fa-lightbulb mr-2 text-green-400"></i>
          ${r.insight}
        </div>
      </div>
    </div>`;
}

// Enter key for predict
document.getElementById('predict-input')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') predictCategory();
});

init();
