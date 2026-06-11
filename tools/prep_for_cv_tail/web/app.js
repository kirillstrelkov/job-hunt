'use strict';

const { invoke } = window.__TAURI__.core;

// ── Theme ─────────────────────────────────────────────────────────────────────
const THEME_KEY = 'prep-tail-theme';
let isDark = localStorage.getItem(THEME_KEY) !== 'light';

function applyTheme() {
  document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
  document.getElementById('btn-theme').textContent = isDark ? '🌙' : '☀️';
}
document.getElementById('btn-theme').addEventListener('click', () => {
  isDark = !isDark;
  localStorage.setItem(THEME_KEY, isDark ? 'dark' : 'light');
  applyTheme();
});
applyTheme();

// ── Main-tab switching ────────────────────────────────────────────────────────
document.querySelectorAll('.main-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.main-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
    // Sync mastercv to LLM tab on switch
    if (btn.dataset.tab === 'tab-llm') {
      document.getElementById('llm-mastercv').value =
        document.getElementById('mastercv-editor').value;
    }
  });
});

// ── Resizers ──────────────────────────────────────────────────────────────────
let activeResizer = null, activeLeftPanel = null;

document.addEventListener('mousemove', e => {
  if (!activeResizer) return;
  const rect = activeResizer.parentElement.getBoundingClientRect();
  const pct = ((e.clientX - rect.left) / rect.width) * 100;
  if (pct > 10 && pct < 90) activeLeftPanel.style.width = pct + '%';
});
document.addEventListener('mouseup', () => {
  if (!activeResizer) return;
  activeResizer.classList.remove('dragging');
  document.body.style.cursor = '';
  document.body.style.userSelect = '';
  activeResizer = null;
  activeLeftPanel = null;
});

function initResizer(resizerId, leftPanelId) {
  const resizer = document.getElementById(resizerId);
  const leftPanel = document.getElementById(leftPanelId);
  resizer.addEventListener('mousedown', e => {
    activeResizer = resizer;
    activeLeftPanel = leftPanel;
    resizer.classList.add('dragging');
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
}
initResizer('md-resizer',  'md-left');
initResizer('cv-resizer',  'cv-left');
initResizer('llm-resizer', 'llm-left');

// ── Pane switcher (generic) ───────────────────────────────────────────────────
// Switches .pane children within `container` based on [data-pane] buttons.
function initPaneSwitcher(container, onSwitch) {
  container.querySelectorAll('[data-pane]').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('[data-pane]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const paneId = btn.dataset.pane;
      container.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
      document.getElementById(paneId).classList.add('active');
      if (onSwitch) onSwitch(paneId);
    });
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
async function renderPreview(markdown, targetEl) {
  try {
    targetEl.innerHTML = await invoke('render_markdown', { markdown });
  } catch (e) {
    targetEl.textContent = 'Preview error: ' + e;
  }
}

function setStatus(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
}

// ── Tab 1: MD → PDF ──────────────────────────────────────────────────────────
const mdInput       = document.getElementById('md-input');
const previewContent = document.getElementById('preview-content');
const pdfFrame      = document.getElementById('pdf-frame');
const pdfPlaceholder = document.getElementById('pdf-placeholder');
let hasPdf = false;

initPaneSwitcher(document.getElementById('md-left'), paneId => {
  if (paneId === 'pane-preview') renderPreview(mdInput.value, previewContent);
});

let previewTimer = null;
mdInput.addEventListener('input', () => {
  if (!document.getElementById('pane-preview').classList.contains('active')) return;
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => renderPreview(mdInput.value, previewContent), 250);
});

document.getElementById('btn-load').addEventListener('click', async () => {
  try {
    const content = await invoke('load_markdown_file');
    if (content !== null) {
      mdInput.value = content;
      if (document.getElementById('pane-preview').classList.contains('active')) {
        renderPreview(mdInput.value, previewContent);
      }
      setStatus('md-status', 'Loaded.');
    }
  } catch (e) { setStatus('md-status', 'Error: ' + e); }
});

document.getElementById('btn-convert').addEventListener('click', async () => {
  if (!mdInput.value.trim()) { setStatus('md-status', 'Nothing to convert.'); return; }
  const btn = document.getElementById('btn-convert');
  btn.disabled = true;
  setStatus('md-status', 'Converting…');
  try {
    const b64 = await invoke('convert_to_pdf', { markdown: mdInput.value });
    pdfFrame.src = 'data:application/pdf;base64,' + b64;
    pdfFrame.style.display = 'block';
    pdfPlaceholder.style.display = 'none';
    hasPdf = true;
    document.getElementById('btn-download').disabled = false;
    setStatus('md-status', 'PDF ready.');
  } catch (e) {
    setStatus('md-status', 'Error: ' + e);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('btn-download').addEventListener('click', async () => {
  if (!hasPdf) return;
  try {
    const dest = await invoke('pick_save_path');
    if (!dest) return;
    await invoke('save_pdf', { destination: dest });
    setStatus('md-status', 'Saved.');
  } catch (e) { setStatus('md-status', 'Error: ' + e); }
});

// ── Tab 2: CV Settings ───────────────────────────────────────────────────────
document.getElementById('btn-load-config').addEventListener('click', async () => {
  try {
    const cfg = await invoke('load_yaml_config');
    if (cfg !== null) {
      if (cfg.header !== null) document.getElementById('header-editor').value = cfg.header;
      if (cfg.body   !== null) document.getElementById('body-editor').value   = cfg.body;
      if (cfg.footer !== null) document.getElementById('footer-editor').value = cfg.footer;
      if (cfg.prompt !== null) document.getElementById('prompt-editor').value = cfg.prompt;
      setStatus('cv-status', 'Config loaded.');
    }
  } catch (e) { setStatus('cv-status', 'Error: ' + e); }
});

let activeSection = 'header';

// Section switching: Header / Body / Footer
document.querySelectorAll('#cv-left .sec-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#cv-left .sec-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeSection = btn.dataset.sec;
    document.querySelectorAll('.cv-section').forEach(s => s.classList.remove('active'));
    document.getElementById('cv-sec-' + activeSection).classList.add('active');
  });
});

// View switching: Edit / Preview within each section
document.querySelectorAll('.view-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const section = btn.closest('.cv-section');
    const view = btn.dataset.view;
    section.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    section.querySelector('.view-edit').classList.toggle('active', view === 'edit');
    section.querySelector('.view-preview').classList.toggle('active', view === 'preview');
    if (view === 'preview') {
      const secId = section.id.replace('cv-sec-', '');
      renderPreview(
        document.getElementById(secId + '-editor').value,
        document.getElementById(secId + '-preview')
      );
    }
  });
});

// Master CV pane switching
initPaneSwitcher(document.getElementById('cv-right'), paneId => {
  if (paneId === 'mastercv-preview-pane') {
    renderPreview(
      document.getElementById('mastercv-editor').value,
      document.getElementById('mastercv-preview')
    );
  }
});

// Combine: header + body + footer → mastercv
document.getElementById('btn-combine').addEventListener('click', () => {
  const parts = ['header', 'body', 'footer']
    .map(sec => document.getElementById(sec + '-editor').value.trim())
    .filter(Boolean);
  document.getElementById('mastercv-editor').value = parts.join('\n\n');
  setStatus('cv-status', 'Combined into Master CV.');
});

// Load into the currently active section
document.getElementById('btn-cv-load').addEventListener('click', async () => {
  try {
    const content = await invoke('load_markdown_file');
    if (content !== null) {
      document.getElementById(activeSection + '-editor').value = content;
      setStatus('cv-status', 'Loaded into ' + activeSection + '.');
    }
  } catch (e) { setStatus('cv-status', 'Error: ' + e); }
});

// Load file directly into Master CV
document.getElementById('btn-mastercv-load').addEventListener('click', async () => {
  try {
    const content = await invoke('load_markdown_file');
    if (content !== null) {
      document.getElementById('mastercv-editor').value = content;
      setStatus('cv-status', 'Master CV loaded.');
    }
  } catch (e) { setStatus('cv-status', 'Error: ' + e); }
});

// ── Tab 3: LLM Settings ──────────────────────────────────────────────────────
initPaneSwitcher(document.getElementById('llm-left'));

// Switch the LLM left panel to a specific pane by ID
function activateLlmPane(paneId) {
  const btn = document.querySelector(`#llm-left [data-pane="${paneId}"]`);
  if (btn) btn.click();
}

document.getElementById('btn-load-prompt').addEventListener('click', async () => {
  try {
    const content = await invoke('load_markdown_file');
    if (content !== null) {
      document.getElementById('prompt-editor').value = content;
      activateLlmPane('llm-pane-prompt');
      setStatus('llm-status', 'Prompt loaded.');
    }
  } catch (e) { setStatus('llm-status', 'Error: ' + e); }
});

document.getElementById('btn-create-prompt').addEventListener('click', () => {
  const prompt = document.getElementById('prompt-editor').value.trim();
  const cv     = document.getElementById('llm-mastercv').value.trim();
  const jd     = document.getElementById('jd-editor').value.trim();
  document.getElementById('llm-output').value =
    `${prompt}\n<cv>\n${cv}\n</cv>\n<job_description>\n${jd}\n</job_description>`;
  setStatus('llm-status', 'Prompt created.');
});

document.getElementById('btn-copy-output').addEventListener('click', async () => {
  const text = document.getElementById('llm-output').value;
  if (!text) { setStatus('llm-status', 'Nothing to copy.'); return; }
  try {
    await navigator.clipboard.writeText(text);
    setStatus('llm-status', 'Copied to clipboard.');
  } catch (e) { setStatus('llm-status', 'Copy failed: ' + e); }
});

document.getElementById('btn-save-output').addEventListener('click', async () => {
  const text = document.getElementById('llm-output').value;
  if (!text) { setStatus('llm-status', 'Nothing to save.'); return; }
  try {
    await invoke('save_text', { content: text });
    setStatus('llm-status', 'Saved.');
  } catch (e) { setStatus('llm-status', 'Error: ' + e); }
});
