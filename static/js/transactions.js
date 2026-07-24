/* FinWise – Transactions JavaScript */

requireAuth();

let currentPage = 1;
let totalPages = 1;
let debounceTimer;
let categories = [];

// ─── Initialize ───────────────────────────────────────────────
async function init() {
  await loadCategories();
  loadTransactions();
  setupEventListeners();
  setupTransactionTypeToggle();
  setDefaultDate();
  setupAIPredict();
}

// ─── Load Categories ──────────────────────────────────────────
async function loadCategories() {
  const res = await apiFetch('/categories');
  if (!res || !res.ok) return;
  categories = res.data.categories || [];

  const sel = document.getElementById('filter-category');
  const modalSel = document.getElementById('category-select');

  categories.forEach(c => {
    if (sel) sel.innerHTML += `<option value="${c.id}">${c.name}</option>`;
  });

  updateModalCategories('expense');
}

function updateModalCategories(type) {
  const sel = document.getElementById('category-select');
  if (!sel) return;
  const filtered = categories.filter(c => c.type === type);
  sel.innerHTML = `<option value="">-- Select Category --</option>` +
    filtered.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
}

// ─── Setup Filters ────────────────────────────────────────────
function setupEventListeners() {
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => { currentPage = 1; loadTransactions(); }, 400);
    });
  }

  ['filter-type', 'filter-category', 'filter-month', 'sort-by'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('change', () => { currentPage = 1; loadTransactions(); });
  });

  // Type filter also updates category dropdown
  const typeFilter = document.getElementById('filter-type');
  if (typeFilter) typeFilter.addEventListener('change', () => {
    // No-op here since we don't filter categories in filter bar
  });

  // Export
  const exportBtn = document.getElementById('export-btn');
  if (exportBtn) exportBtn.addEventListener('click', exportCSV);
}

// ─── Load Transactions ────────────────────────────────────────
async function loadTransactions() {
  const body = document.getElementById('transactions-body');
  if (body) body.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Loading...</td></tr>`;

  const params = new URLSearchParams({
    page: currentPage,
    per_page: 10,
    search: document.getElementById('search-input')?.value || '',
    type: document.getElementById('filter-type')?.value || '',
    category_id: document.getElementById('filter-category')?.value || '',
    month: document.getElementById('filter-month')?.value || '',
    sort: document.getElementById('sort-by')?.value || 'date_desc',
  });

  const res = await apiFetch(`/transactions?${params}`);
  if (!res || !res.ok) return;

  const data = res.data;
  totalPages = data.pages || 1;
  currentPage = data.page;

  renderTable(data.transactions || []);
  renderPagination(data);
  updateStrip(data.transactions || []);
}

function renderTable(transactions) {
  const body = document.getElementById('transactions-body');
  if (!body) return;

  if (!transactions.length) {
    body.innerHTML = `<tr><td colspan="6" class="text-center py-12 text-slate-400">
      <i class="fa-solid fa-inbox text-2xl mb-3 block"></i>
      No transactions found.
    </td></tr>`;
    return;
  }

  body.innerHTML = transactions.map(t => `
    <tr class="group animate-fade-in">
      <td class="text-slate-400 text-sm">${formatDate(t.date)}</td>
      <td>
        <div class="font-medium text-white text-sm">${escapeHtml(t.description)}</div>
        ${t.notes ? `<div class="text-xs text-slate-500 truncate max-w-xs">${escapeHtml(t.notes)}</div>` : ''}
      </td>
      <td>
        <div class="flex items-center gap-2">
          <div class="cat-icon" style="background:${t.category_color}22;color:${t.category_color};width:28px;height:28px;font-size:12px">
            <i class="fa-solid ${t.category_icon}"></i>
          </div>
          <span class="text-sm text-slate-300">${t.category_name}</span>
        </div>
      </td>
      <td>
        <span class="badge ${t.type === 'income' ? 'badge-income' : 'badge-expense'}">
          <i class="fa-solid ${t.type === 'income' ? 'fa-arrow-up' : 'fa-arrow-down'} text-xs"></i>
          ${t.type.charAt(0).toUpperCase() + t.type.slice(1)}
        </span>
      </td>
      <td class="text-right font-bold ${t.type === 'income' ? 'text-green-400' : 'text-red-400'}">
        ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
      </td>
      <td class="text-center">
        <div class="flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button class="btn btn-ghost btn-sm" onclick="editTransaction(${JSON.stringify(t).replace(/"/g, '&quot;')})">
            <i class="fa-solid fa-pen-to-square text-indigo-400"></i>
          </button>
          <button class="btn btn-ghost btn-sm" onclick="deleteTransaction(${t.id})">
            <i class="fa-solid fa-trash text-red-400"></i>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

function updateStrip(transactions) {
  let income = 0, expense = 0;
  transactions.forEach(t => {
    if (t.type === 'income') income += t.amount;
    else expense += t.amount;
  });
  const net = income - expense;
  const el = id => document.getElementById(id);
  if (el('strip-income')) el('strip-income').textContent = formatCurrency(income);
  if (el('strip-expense')) el('strip-expense').textContent = formatCurrency(expense);
  if (el('strip-net')) {
    el('strip-net').textContent = (net >= 0 ? '+' : '') + formatCurrency(Math.abs(net));
    el('strip-net').className = `text-xl font-bold ${net >= 0 ? 'gradient-text' : 'text-red-400'}`;
  }
}

function renderPagination(data) {
  const info = document.getElementById('pagination-info');
  const controls = document.getElementById('pagination-controls');
  if (!info || !controls) return;

  const start = (data.page - 1) * data.per_page + 1;
  const end = Math.min(data.page * data.per_page, data.total);
  info.textContent = `Showing ${data.total ? start : 0}–${end} of ${data.total}`;

  controls.innerHTML = '';
  if (data.pages <= 1) return;

  // Prev
  const prevBtn = document.createElement('button');
  prevBtn.className = `btn btn-ghost btn-sm ${!data.has_prev ? 'opacity-40 cursor-not-allowed' : ''}`;
  prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
  prevBtn.disabled = !data.has_prev;
  prevBtn.onclick = () => { currentPage--; loadTransactions(); };
  controls.appendChild(prevBtn);

  // Page numbers
  for (let p = Math.max(1, data.page - 2); p <= Math.min(data.pages, data.page + 2); p++) {
    const btn = document.createElement('button');
    btn.className = `btn btn-sm ${p === data.page ? 'btn-primary' : 'btn-ghost'}`;
    btn.textContent = p;
    btn.onclick = () => { currentPage = p; loadTransactions(); };
    controls.appendChild(btn);
  }

  // Next
  const nextBtn = document.createElement('button');
  nextBtn.className = `btn btn-ghost btn-sm ${!data.has_next ? 'opacity-40 cursor-not-allowed' : ''}`;
  nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
  nextBtn.disabled = !data.has_next;
  nextBtn.onclick = () => { currentPage++; loadTransactions(); };
  controls.appendChild(nextBtn);
}

// ─── Add / Edit Modal ─────────────────────────────────────────
function openTransactionModal(transaction = null) {
  const modal = document.getElementById('transaction-modal');
  const form = document.getElementById('transaction-form');
  const title = document.getElementById('modal-title');

  if (!modal || !form) return;

  form.reset();
  document.getElementById('edit-id').value = '';
  document.getElementById('ai-prediction-result').classList.add('hidden');

  if (transaction) {
    title.textContent = 'Edit Transaction';
    document.getElementById('edit-id').value = transaction.id;
    document.getElementById('amount').value = transaction.amount;
    document.getElementById('description').value = transaction.description;
    document.getElementById('date').value = transaction.date;
    document.getElementById('notes').value = transaction.notes || '';

    // Set type
    const typeRadio = document.querySelector(`input[name=type][value="${transaction.type}"]`);
    if (typeRadio) { typeRadio.checked = true; updateTypeUI(transaction.type); }
    updateModalCategories(transaction.type);
    setTimeout(() => {
      const sel = document.getElementById('category-select');
      if (sel) sel.value = transaction.category_id || '';
    }, 50);
  } else {
    title.textContent = 'Add Transaction';
    setDefaultDate();
    updateTypeUI('expense');
    updateModalCategories('expense');
  }

  modal.classList.add('open');
}

function closeTransactionModal() {
  document.getElementById('transaction-modal')?.classList.remove('open');
}

function setDefaultDate() {
  const dateEl = document.getElementById('date');
  if (dateEl) dateEl.value = new Date().toISOString().split('T')[0];
}

// ─── Type Toggle UI ───────────────────────────────────────────
function setupTransactionTypeToggle() {
  document.querySelectorAll('input[name=type]').forEach(radio => {
    radio.addEventListener('change', () => {
      updateTypeUI(radio.value);
      updateModalCategories(radio.value);
    });
  });
}

function updateTypeUI(type) {
  const expBtn = document.getElementById('type-expense-btn');
  const incBtn = document.getElementById('type-income-btn');
  if (!expBtn || !incBtn) return;

  if (type === 'expense') {
    expBtn.className = 'type-btn p-3 rounded-xl border border-red-500/50 bg-red-500/15 text-center transition-colors';
    incBtn.className = 'type-btn p-3 rounded-xl border border-slate-700 text-center hover:bg-green-500/10 transition-colors';
    incBtn.querySelector('.income-icon').className = 'fa-solid fa-arrow-up text-slate-400 text-lg block mb-1 income-icon';
    incBtn.querySelector('.income-label').className = 'text-sm font-semibold text-slate-400 income-label';
  } else {
    incBtn.className = 'type-btn p-3 rounded-xl border border-green-500/50 bg-green-500/15 text-center transition-colors';
    expBtn.className = 'type-btn p-3 rounded-xl border border-slate-700 text-center hover:bg-red-500/10 transition-colors';
    incBtn.querySelector('.income-icon').className = 'fa-solid fa-arrow-up text-green-400 text-lg block mb-1 income-icon';
    incBtn.querySelector('.income-label').className = 'text-sm font-semibold text-green-400 income-label';
  }
}

// ─── AI Category Prediction ───────────────────────────────────
function setupAIPredict() {
  const btn = document.getElementById('ai-predict-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const desc = document.getElementById('description').value.trim();
    if (!desc) { showToast('Enter a description first.', 'warning'); return; }

    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i>Predicting...';
    btn.disabled = true;

    const res = await apiFetch('/ai/predict-category', {
      method: 'POST',
      body: JSON.stringify({ description: desc }),
    });

    btn.innerHTML = '<i class="fa-solid fa-brain mr-1"></i>AI Predict Category';
    btn.disabled = false;

    if (res && res.ok) {
      const { predicted_category, confidence } = res.data;
      const resultEl = document.getElementById('ai-prediction-result');
      if (resultEl) {
        resultEl.classList.remove('hidden');
        resultEl.innerHTML = `<i class="fa-solid fa-brain mr-1"></i>AI suggests: <strong>${predicted_category}</strong> (${confidence}% confidence)`;
      }

      // Auto-select the category in dropdown
      const sel = document.getElementById('category-select');
      if (sel) {
        const opt = Array.from(sel.options).find(o => o.text.toLowerCase().includes(predicted_category.toLowerCase().split(' ')[0]));
        if (opt) sel.value = opt.value;
      }
    }
  });
}

// ─── Form Submit ──────────────────────────────────────────────
document.getElementById('transaction-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const editId = document.getElementById('edit-id').value;
  const type = document.querySelector('input[name=type]:checked')?.value || 'expense';
  const btn = document.getElementById('save-btn');

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  const body = {
    type,
    amount: parseFloat(document.getElementById('amount').value),
    description: document.getElementById('description').value.trim(),
    category_id: parseInt(document.getElementById('category-select').value) || null,
    date: document.getElementById('date').value,
    notes: document.getElementById('notes').value.trim(),
  };

  const url = editId ? `/transactions/${editId}` : '/transactions';
  const method = editId ? 'PUT' : 'POST';

  const res = await apiFetch(url, { method, body: JSON.stringify(body) });

  btn.disabled = false;
  btn.innerHTML = '<i class="fa-solid fa-check"></i> Save Transaction';

  if (res && res.ok) {
    showToast(editId ? 'Transaction updated!' : 'Transaction added!', 'success');
    closeTransactionModal();
    loadTransactions();
  } else {
    showToast(res?.data?.error || 'Error saving transaction.', 'error');
  }
});

// ─── Edit / Delete ────────────────────────────────────────────
function editTransaction(t) {
  openTransactionModal(t);
}

async function deleteTransaction(id) {
  if (!confirm('Delete this transaction?')) return;
  const res = await apiFetch(`/transactions/${id}`, { method: 'DELETE' });
  if (res && res.ok) {
    showToast('Transaction deleted.', 'success');
    loadTransactions();
  } else {
    showToast('Could not delete transaction.', 'error');
  }
}

// ─── Export CSV ───────────────────────────────────────────────
function exportCSV() {
  const month = document.getElementById('filter-month')?.value || '';
  const type = document.getElementById('filter-type')?.value || '';
  const params = new URLSearchParams({ month, type });
  window.open(`/api/transactions/export?${params}`, '_blank');
  showToast('Downloading CSV...', 'success');
}

// ─── Reset Filters ────────────────────────────────────────────
function resetFilters() {
  ['search-input', 'filter-type', 'filter-category', 'filter-month'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('sort-by').value = 'date_desc';
  currentPage = 1;
  loadTransactions();
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

// Init
init();
