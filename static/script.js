// ---------- Application number (cosmetic, ties to "ledger" theme) ----------
document.getElementById('app-number').textContent =
  String(Math.floor(1000 + Math.random() * 8999));

// ---------- Gauge helpers ----------
const GAUGE_LEN = 251.2; // approx length of the semicircle path
const gaugeFill = document.getElementById('gauge-fill');
const gaugeNeedle = document.getElementById('gauge-needle');
const gaugeValue = document.getElementById('gauge-value');

function setGauge(prob, color) {
  const offset = GAUGE_LEN * (1 - prob);
  gaugeFill.style.strokeDashoffset = offset;
  gaugeFill.style.stroke = color;
  const deg = -90 + prob * 180;
  gaugeNeedle.style.transform = `rotate(${deg}deg)`;
  gaugeValue.textContent = Math.round(prob * 100) + '%';
}

// ---------- Stamp ----------
const stampEl = document.getElementById('stamp');
const stampPlaceholder = document.getElementById('stamp-placeholder');

function showStamp(decision) {
  stampPlaceholder.style.display = 'none';
  stampEl.textContent = decision === 'APPROVED' ? 'Approved' : 'Declined';
  stampEl.className = 'stamp show ' + (decision === 'APPROVED' ? 'approved' : 'declined');
  // restart animation if fired twice
  void stampEl.offsetWidth;
  stampEl.classList.remove('show');
  void stampEl.offsetWidth;
  stampEl.classList.add('show');
}

// ---------- Form ----------
const form = document.getElementById('loan-form');
const submitBtn = document.getElementById('submit-btn');
const fields = ['age', 'income_lakh', 'credit_score', 'loan_amount_lakh', 'existing_loans'];

function clearErrors() {
  fields.forEach(f => {
    document.getElementById('err-' + f).textContent = '';
  });
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearErrors();
  submitBtn.disabled = true;
  submitBtn.querySelector('span').textContent = 'Reviewing…';

  const payload = {};
  fields.forEach(f => {
    payload[f] = document.getElementById(f).value;
  });

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!data.ok) {
      Object.entries(data.errors || {}).forEach(([field, msg]) => {
        const el = document.getElementById('err-' + field);
        if (el) el.textContent = msg;
      });
      return;
    }

    const color = data.decision === 'APPROVED' ? '#4C9A6A' : '#C1483D';
    setGauge(data.probability_approved, color);
    showStamp(data.decision);

    document.getElementById('detail-debt').textContent = data.debt_burden;
    document.getElementById('detail-age-group').textContent = data.age_group;

  } catch (err) {
    console.error(err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.querySelector('span').textContent = 'Submit for review';
  }
});

// ---------- Dashboard ----------
const CHART_TEXT = '#8B93A6';
const CHART_GRID = 'rgba(139,147,166,0.12)';
Chart.defaults.color = CHART_TEXT;
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;

fetch('/api/stats')
  .then(r => r.json())
  .then(stats => {
    document.getElementById('stat-clean-rows').textContent = stats.n_rows_clean.toLocaleString();
    document.getElementById('stat-dupes').textContent = stats.duplicates_removed;
    document.getElementById('stat-approval-rate').textContent = Math.round(stats.approval_rate * 100) + '%';
    document.getElementById('stat-auc').textContent = stats.test_auc;

    // Credit score bucket chart
    const creditLabels = Object.keys(stats.by_credit_bucket);
    const creditValues = Object.values(stats.by_credit_bucket).map(v => Math.round(v * 100));
    new Chart(document.getElementById('chart-credit'), {
      type: 'bar',
      data: {
        labels: creditLabels,
        datasets: [{
          data: creditValues,
          backgroundColor: '#C9A227',
          borderRadius: 3,
          maxBarThickness: 34
        }]
      },
      options: {
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.raw + '% approved' } } },
        scales: {
          y: { beginAtZero: true, max: 100, grid: { color: CHART_GRID }, ticks: { callback: v => v + '%' } },
          x: { grid: { display: false } }
        }
      }
    });

    // Age group chart
    const ageLabels = Object.keys(stats.by_age_group);
    const ageValues = Object.values(stats.by_age_group).map(v => Math.round(v * 100));
    new Chart(document.getElementById('chart-age'), {
      type: 'bar',
      data: {
        labels: ageLabels,
        datasets: [{
          data: ageValues,
          backgroundColor: '#4C9A6A',
          borderRadius: 3,
          maxBarThickness: 46
        }]
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.raw + '% approved' } } },
        scales: {
          x: { beginAtZero: true, max: 100, grid: { color: CHART_GRID }, ticks: { callback: v => v + '%' } },
          y: { grid: { display: false } }
        }
      }
    });

    // Coefficient chart
    const coefEntries = Object.entries(stats.model_coefficients).sort((a, b) => a[1] - b[1]);
    new Chart(document.getElementById('chart-coef'), {
      type: 'bar',
      data: {
        labels: coefEntries.map(e => e[0]),
        datasets: [{
          data: coefEntries.map(e => e[1]),
          backgroundColor: coefEntries.map(e => e[1] >= 0 ? '#4C9A6A' : '#C1483D'),
          borderRadius: 3,
          maxBarThickness: 28
        }]
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: CHART_GRID } },
          y: { grid: { display: false } }
        }
      }
    });
  });
