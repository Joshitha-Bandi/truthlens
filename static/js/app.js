/**
 * TruthLens — Frontend Application Logic
 * AI-Powered Content Credibility Analyzer
 */

// ─── STATE ───
let currentLang = 'en';
let translations = {};
let isAnalyzing = false;

// ─── DOM ELEMENTS ───
const urlInput = document.getElementById('url-input');
const analyzeBtn = document.getElementById('analyze-btn');
const heroSection = document.getElementById('hero-section');
const searchSection = document.getElementById('search-section');
const loadingOverlay = document.getElementById('loading-overlay');
const resultsSection = document.getElementById('results-section');
const errorSection = document.getElementById('error-section');
const historyPanel = document.getElementById('history-panel');
const historyBackdrop = document.getElementById('history-backdrop');
const historyList = document.getElementById('history-list');
const toastContainer = document.getElementById('toast-container');

// ─── TRANSLATIONS ───
const STRINGS = {
  en: {
    analyze: '🔍 Analyze',
    analyzing: 'Analyzing...',
    summary: 'Summary',
    truth_score: 'Truth Score',
    warnings: 'Warnings & Alerts',
    domain_info: 'Domain Info',
    history: 'History',
    no_history: 'No analyses yet. Try analyzing a URL!',
    enter_url: 'Paste any article URL to analyze...',
    safe: '✅ No warnings detected — content appears safe.',
    step_fetching: 'Fetching webpage content...',
    step_extracting: 'Extracting text & metadata...',
    step_analyzing: 'Running AI credibility analysis...',
    step_scoring: 'Calculating truth score...',
    verdict_high: 'Highly Credible',
    verdict_high_desc: 'This content appears to be from a reliable source with well-structured, factual information.',
    verdict_mid: 'Needs Verification',
    verdict_mid_desc: 'This content has some credibility concerns. Cross-reference with trusted sources before sharing.',
    verdict_low: 'Low Credibility',
    verdict_low_desc: 'This content raises significant red flags. It may contain misleading, toxic, or deceptive information.',
    new_analysis: '← New Analysis',
    error_title: 'Analysis Failed',
    powered_by: 'Powered by AI',
  },
  te: {
    analyze: '🔍 విశ్లేషించు',
    analyzing: 'విశ్లేషిస్తోంది...',
    summary: 'సారాంశం',
    truth_score: 'నిజం స్కోర్',
    warnings: 'హెచ్చరికలు',
    domain_info: 'డొమైన్ సమాచారం',
    history: 'చరిత్ర',
    no_history: 'ఇంకా విశ్లేషణలు లేవు. ఒక URL ని విశ్లేషించండి!',
    enter_url: 'విశ్లేషించడానికి ఏదైనా వ్యాసం URL అతికించండి...',
    safe: '✅ ఎటువంటి హెచ్చరికలు కనుగొనబడలేదు — కంటెంట్ సురక్షితంగా ఉంది.',
    step_fetching: 'వెబ్‌పేజీ కంటెంట్‌ను పొందుతోంది...',
    step_extracting: 'టెక్స్ట్ & మెటాడేటా సేకరిస్తోంది...',
    step_analyzing: 'AI విశ్వసనీయత విశ్లేషణ నిర్వహిస్తోంది...',
    step_scoring: 'నిజం స్కోర్ లెక్కిస్తోంది...',
    verdict_high: 'అధిక విశ్వసనీయత',
    verdict_high_desc: 'ఈ కంటెంట్ నమ్మదగిన మూలం నుండి వచ్చినట్లు కనిపిస్తుంది.',
    verdict_mid: 'ధృవీకరణ అవసరం',
    verdict_mid_desc: 'ఈ కంటెంట్‌కు విశ్వసనీయత సమస్యలు ఉన్నాయి. భాగస్వామ్యం చేయడానికి ముందు విశ్వసనీయ వనరులతో సరిపోల్చండి.',
    verdict_low: 'తక్కువ విశ్వసనీయత',
    verdict_low_desc: 'ఈ కంటెంట్ తప్పుడు, విషపూరిత లేదా మోసపూరిత సమాచారాన్ని కలిగి ఉండవచ్చు.',
    new_analysis: '← కొత్త విశ్లేషణ',
    error_title: 'విశ్లేషణ విఫలమైంది',
    powered_by: 'AI ద్వారా శక్తివంతం',
  }
};

function t(key) {
  return (STRINGS[currentLang] && STRINGS[currentLang][key]) || STRINGS.en[key] || key;
}

// ─── TOAST ───
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.35s forwards';
    setTimeout(() => toast.remove(), 350);
  }, 3000);
}

// ─── HISTORY ───
function toggleHistory() {
  historyPanel.classList.toggle('open');
  historyBackdrop.classList.toggle('active');
  if (historyPanel.classList.contains('open')) {
    fetchHistory();
  }
}

function closeHistory() {
  historyPanel.classList.remove('open');
  historyBackdrop.classList.remove('active');
}

async function fetchHistory() {
  try {
    const resp = await fetch('/api/history');
    const data = await resp.json();
    renderHistory(data.history || []);
  } catch (e) {
    historyList.innerHTML = `<div class="history-empty"><div class="history-empty-icon">📡</div><p>Could not load history</p></div>`;
  }
}

function renderHistory(items) {
  if (!items.length) {
    historyList.innerHTML = `<div class="history-empty"><div class="history-empty-icon">🕰️</div><p>${t('no_history')}</p></div>`;
    return;
  }

  historyList.innerHTML = items.map(item => {
    const scoreClass = item.truth_score >= 70 ? 'green' : item.truth_score >= 40 ? 'yellow' : 'red';
    let badges = '';
    if (item.is_scam) badges += '<span class="history-badge scam">SCAM</span>';
    if (item.is_toxic) badges += '<span class="history-badge toxic">TOXIC</span>';
    if (item.warning_count > 0 && !item.is_scam && !item.is_toxic)
      badges += `<span class="history-badge warn">${item.warning_count} Warning${item.warning_count > 1 ? 's' : ''}</span>`;

    return `
      <div class="history-item" onclick="analyzeFromHistory('${escapeAttr(item.url)}')">
        <div class="history-item-url">${escapeHTML(item.url)}</div>
        <div class="history-item-meta">
          <span class="history-item-score ${scoreClass}">${item.truth_score}/100</span>
          <span class="history-item-date">${item.analyzed_at}</span>
        </div>
        ${badges ? `<div class="history-item-badges">${badges}</div>` : ''}
      </div>
    `;
  }).join('');
}

function analyzeFromHistory(url) {
  closeHistory();
  urlInput.value = url;
  startAnalysis();
}

// ─── LANGUAGE TOGGLE ───
function toggleLanguage() {
  currentLang = currentLang === 'en' ? 'te' : 'en';
  updateUILanguage();
  showToast(currentLang === 'te' ? 'Telugu భాషకు మార్చబడింది' : 'Switched to English', 'info');

  // Update active state on buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === currentLang);
  });
}

function updateUILanguage() {
  const analyzeBtnText = document.getElementById('analyze-btn-text');
  if (analyzeBtnText && !isAnalyzing) analyzeBtnText.textContent = t('analyze');
  urlInput.placeholder = t('enter_url');

  // Update loading step text
  const stepEls = document.querySelectorAll('.loading-step .step-text');
  const stepKeys = ['step_fetching', 'step_extracting', 'step_analyzing', 'step_scoring'];
  stepEls.forEach((el, i) => { if (stepKeys[i]) el.textContent = t(stepKeys[i]); });
}

// ─── SECTION VISIBILITY ───
function showSection(section) {
  heroSection.style.display = 'none';
  searchSection.style.display = 'none';
  loadingOverlay.classList.remove('active');
  loadingOverlay.style.display = 'none';
  resultsSection.classList.remove('active');
  resultsSection.style.display = 'none';
  errorSection.classList.remove('active');
  errorSection.style.display = 'none';

  switch (section) {
    case 'home':
      heroSection.style.display = 'block';
      searchSection.style.display = 'block';
      break;
    case 'loading':
      searchSection.style.display = 'block';
      loadingOverlay.style.display = 'block';
      setTimeout(() => loadingOverlay.classList.add('active'), 10);
      break;
    case 'results':
      searchSection.style.display = 'block';
      resultsSection.style.display = 'block';
      setTimeout(() => resultsSection.classList.add('active'), 10);
      break;
    case 'error':
      searchSection.style.display = 'block';
      errorSection.style.display = 'block';
      setTimeout(() => errorSection.classList.add('active'), 10);
      break;
  }
}

// ─── LOADING STEPS ANIMATION ───
function animateLoadingSteps() {
  const steps = document.querySelectorAll('.loading-step');
  let current = 0;

  function activateStep() {
    if (current >= steps.length || !isAnalyzing) return;
    steps.forEach((s, i) => {
      s.classList.remove('active', 'done');
      if (i < current) s.classList.add('done');
      if (i === current) s.classList.add('active');
    });
    current++;
    setTimeout(activateStep, 1200 + Math.random() * 800);
  }
  activateStep();
}

// ─── ANALYZE ───
async function startAnalysis() {
  const url = urlInput.value.trim();
  if (!url) {
    showToast('Please enter a URL first', 'error');
    urlInput.focus();
    return;
  }

  isAnalyzing = true;
  analyzeBtn.disabled = true;
  const btnText = document.getElementById('analyze-btn-text');
  if (btnText) btnText.textContent = t('analyzing');

  showSection('loading');
  animateLoadingSteps();

  try {
    const resp = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });

    const data = await resp.json();

    if (!resp.ok || data.error) {
      throw new Error(data.error || `Server error ${resp.status}`);
    }

    renderResults(data);
    showSection('results');
    showToast(t('analysis_complete') || 'Analysis complete!', 'success');

  } catch (err) {
    console.error('Analysis failed:', err);
    document.getElementById('error-msg').textContent = err.message;
    showSection('error');
    showToast('Analysis failed', 'error');
  } finally {
    isAnalyzing = false;
    analyzeBtn.disabled = false;
    const btnText = document.getElementById('analyze-btn-text');
    if (btnText) btnText.textContent = t('analyze');
  }
}

// ─── RENDER RESULTS ───
function renderResults(data) {
  const score = data.truth_score || 0;
  const scoreClass = score >= 70 ? 'green' : score >= 40 ? 'yellow' : 'red';
  const circumference = 326;
  const offset = circumference - (score / 100) * circumference;

  // Verdict
  let verdict, verdictDesc;
  if (score >= 70) {
    verdict = t('verdict_high');
    verdictDesc = t('verdict_high_desc');
  } else if (score >= 40) {
    verdict = t('verdict_mid');
    verdictDesc = t('verdict_mid_desc');
  } else {
    verdict = t('verdict_low');
    verdictDesc = t('verdict_low_desc');
  }

  // Score card
  document.getElementById('truth-score-card').innerHTML = `
    <div class="card-header">
      <div class="card-icon icon-blue">🎯</div>
      <span class="card-label">${t('truth_score')}</span>
    </div>
    <div class="score-container">
      <div class="score-circle">
        <svg viewBox="0 0 120 120">
          <circle class="bg-ring" cx="60" cy="60" r="52"/>
          <circle class="progress-ring ${scoreClass}" cx="60" cy="60" r="52"
            style="stroke-dashoffset: ${offset}"/>
        </svg>
        <div class="score-value">
          <div class="score-number ${scoreClass}">${score}</div>
          <div class="score-label-small">/ 100</div>
        </div>
      </div>
      <div class="score-details">
        <div class="score-verdict ${scoreClass}">${verdict}</div>
        <div class="score-desc">${verdictDesc}</div>
      </div>
    </div>
  `;

  // Summary card
  document.getElementById('summary-card').innerHTML = `
    <div class="card-header">
      <div class="card-icon icon-blue">📝</div>
      <span class="card-label">${t('summary')}</span>
    </div>
    <div class="summary-text">${escapeHTML(data.summary || 'No summary available.')}</div>
  `;

  // Warnings card
  const warnings = data.warnings || [];
  let warningsHTML = '';
  if (warnings.length === 0) {
    warningsHTML = `<div class="no-warnings">✅ ${t('safe')}</div>`;
  } else {
    warningsHTML = '<div class="warnings-list">' + warnings.map(w => {
      const sev = w.severity || 'low';
      return `
        <div class="warning-item severity-${sev}">
          <span class="warning-icon">${sev === 'high' ? '🚨' : sev === 'medium' ? '⚠️' : 'ℹ️'}</span>
          <div>
            <div>${escapeHTML(w.message)}</div>
            ${w.details ? `<div style="font-size:12px;color:var(--text-muted);margin-top:4px;">${w.details.map(d => escapeHTML(d)).join(', ')}</div>` : ''}
          </div>
        </div>`;
    }).join('') + '</div>';
  }

  document.getElementById('warnings-card').innerHTML = `
    <div class="card-header">
      <div class="card-icon ${warnings.length ? 'icon-red' : 'icon-green'}">
        ${warnings.length ? '⚠️' : '🛡️'}
      </div>
      <span class="card-label">${t('warnings')} ${warnings.length ? `(${warnings.length})` : ''}</span>
    </div>
    ${warningsHTML}
  `;

  // Domain info card
  const domain = data.domain_info || {};
  let tags = '';
  tags += `<span class="domain-tag neutral">🌐 ${escapeHTML(domain.domain || 'Unknown')}</span>`;
  if (domain.has_https) tags += '<span class="domain-tag secure">🔒 HTTPS</span>';
  else tags += '<span class="domain-tag insecure">🔓 No HTTPS</span>';
  if (domain.is_credible_source) tags += '<span class="domain-tag credible">✅ Credible Source</span>';
  else tags += '<span class="domain-tag not-credible">⚡ Unverified Source</span>';
  tags += `<span class="domain-tag neutral">📊 ${data.analysis_method || 'heuristic'}</span>`;

  document.getElementById('domain-card').innerHTML = `
    <div class="card-header">
      <div class="card-icon icon-blue">🔗</div>
      <span class="card-label">${t('domain_info')}</span>
    </div>
    <div class="domain-info">${tags}</div>
  `;

  // Results header
  document.getElementById('result-url-display').textContent = data.url || '';
  document.getElementById('result-title-display').textContent = data.title || 'Analysis Results';
}

// ─── BACK TO HOME ───
function backToHome() {
  showSection('home');
}

// ─── UTILS ───
function escapeHTML(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function escapeAttr(str) {
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

// ─── EVENT LISTENERS ───
analyzeBtn.addEventListener('click', startAnalysis);
urlInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') startAnalysis();
});

document.getElementById('history-btn').addEventListener('click', toggleHistory);
document.getElementById('history-close-btn').addEventListener('click', closeHistory);
historyBackdrop.addEventListener('click', closeHistory);

document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    currentLang = btn.dataset.lang;
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    updateUILanguage();
    showToast(currentLang === 'te' ? 'Telugu భాషకు మార్చబడింది' : 'Switched to English', 'info');
  });
});

document.getElementById('back-btn').addEventListener('click', backToHome);

// ─── INIT ───
updateUILanguage();
