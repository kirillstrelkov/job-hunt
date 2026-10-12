import './style.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import htmlToPdfmake from 'html-to-pdfmake';
import pdfMake from 'pdfmake/build/pdfmake';
import pdfFonts from 'pdfmake/build/vfs_fonts';
import {
  preprocessMarkdown,
  cleanPdfNodes,
  defaultStyles,
  buildDocDef
} from './core.js';

pdfMake.vfs = pdfFonts.pdfMake ? pdfFonts.pdfMake.vfs : pdfFonts;

marked.use({
  gfm: true,
  breaks: true
});

// DOM Elements
const editor = document.getElementById('markdownEditor');
const previewContainer = document.getElementById('previewContainer');
const pdfPlaceholder = document.getElementById('pdfPlaceholder');
const pdfFrame = document.getElementById('pdfFrame');
const tabBtnEdit = document.getElementById('tabBtnEdit');
const tabBtnPreview = document.getElementById('tabBtnPreview');
const tabContentEdit = document.getElementById('tabContentEdit');
const tabContentPreview = document.getElementById('tabContentPreview');
const fileUploadInput = document.getElementById('fileUploadInput');
const btnUpload = document.getElementById('btnUpload');
const btnLoadExample = document.getElementById('btnLoadExample');
const btnClear = document.getElementById('btnClear');
const btnSave = document.getElementById('btnSave');
const btnConvert = document.getElementById('btnConvert');
const convertSpinner = document.getElementById('convertSpinner');
const convertText = document.getElementById('convertText');
const btnDownloadPdf = document.getElementById('btnDownloadPdf');
const btnPrintVector = document.getElementById('btnPrintVector');

// State
let currentPdfDoc = null;
let currentPdfUrl = null;
const STORAGE_KEY = 'resume_md_draft';

function renderMarkdownAsIs(md) {
  if (!md || !md.trim()) {
    return '<p style="color: #94a3b8; font-style: italic;">No markdown content to preview.</p>';
  }
  const preprocessed = preprocessMarkdown(md, marked);
  const rawHtml = marked.parse(preprocessed);
  return DOMPurify.sanitize(rawHtml, {
    ADD_TAGS: ['table', 'tr', 'td', 'div', 'span'],
    ADD_ATTR: ['style', 'class']
  });
}

function updatePreview() {
  const md = editor.value;
  previewContainer.innerHTML = renderMarkdownAsIs(md);
}

function resetConvertButton() {
  btnConvert.disabled = false;
  convertSpinner.classList.add('is-hidden');
  convertText.textContent = 'Convert markdown to PDF';
}

function handleBlobSuccess(blob) {
  if (currentPdfUrl) {
    URL.revokeObjectURL(currentPdfUrl);
  }
  currentPdfUrl = URL.createObjectURL(blob);

  pdfFrame.src = currentPdfUrl;
  pdfPlaceholder.classList.add('is-hidden');
  pdfFrame.classList.remove('is-hidden');

  btnDownloadPdf.disabled = false;
  btnPrintVector.disabled = false;
}

function handleBlobError(error) {
  console.error('Vector PDF generation failed:', error);
  alert('Failed to generate PDF: ' + (error && error.message ? error.message : error));
}

function generatePdf() {
  const md = editor.value;
  if (!md.trim()) {
    pdfPlaceholder.classList.remove('is-hidden');
    pdfFrame.classList.add('is-hidden');
    btnDownloadPdf.disabled = true;
    btnPrintVector.disabled = true;
    return;
  }

  btnConvert.disabled = true;
  convertSpinner.classList.remove('is-hidden');
  convertText.textContent = 'Generating PDF...';

  try {
    const preprocessed = preprocessMarkdown(md, marked);
    const rawHtml = marked.parse(preprocessed);

    let cleanHtml = DOMPurify.sanitize(rawHtml, {
      ADD_TAGS: ['table', 'tr', 'td', 'div', 'span', 'hr'],
      ADD_ATTR: ['style', 'class']
    });

    cleanHtml = cleanHtml.replace(/<hr\s*\/?>/gi, '');

    let pdfContent = htmlToPdfmake(cleanHtml, {
      tableAutoSize: true,
      defaultStyles: defaultStyles
    });

    pdfContent = cleanPdfNodes(pdfContent);
    const docDef = buildDocDef(pdfContent);

    currentPdfDoc = pdfMake.createPdf(docDef);
    currentPdfDoc.getBlob(function (blob) {
      try {
        if (!blob) throw new Error('PDF generation produced an empty result.');
        handleBlobSuccess(blob);
      } catch (innerError) {
        handleBlobError(innerError);
      } finally {
        resetConvertButton();
      }
    });
  } catch (error) {
    handleBlobError(error);
    resetConvertButton();
  }
}

function loadExampleResume() {
  fetch('example.md')
    .then(res => {
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return res.text();
    })
    .then(text => {
      editor.value = text;
      localStorage.setItem(STORAGE_KEY, text);
      updatePreview();
      generatePdf();
    })
    .catch(err => {
      console.error('Failed to load example.md:', err);
      alert('Could not load example.md from server.');
    });
}

// Editor input debouncing
let debounceTimeout = null;
editor.addEventListener('input', () => {
  localStorage.setItem(STORAGE_KEY, editor.value);
  clearTimeout(debounceTimeout);
  debounceTimeout = setTimeout(() => {
    if (tabContentPreview.classList.contains('active')) {
      updatePreview();
    }
  }, 200);
});

// Tab switching
tabBtnEdit.addEventListener('click', () => {
  tabBtnEdit.classList.add('active');
  tabBtnPreview.classList.remove('active');
  tabContentEdit.classList.add('active');
  tabContentPreview.classList.remove('active');
});

tabBtnPreview.addEventListener('click', () => {
  tabBtnPreview.classList.add('active');
  tabBtnEdit.classList.remove('active');
  tabContentPreview.classList.add('active');
  tabContentEdit.classList.remove('active');
  updatePreview();
});

// Toolbar buttons
btnUpload.addEventListener('click', () => fileUploadInput.click());

fileUploadInput.addEventListener('change', event => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = e => {
    editor.value = e.target.result;
    localStorage.setItem(STORAGE_KEY, editor.value);
    updatePreview();
    generatePdf();
  };
  reader.readAsText(file);
  fileUploadInput.value = '';
});

btnLoadExample.addEventListener('click', loadExampleResume);

btnClear.addEventListener('click', () => {
  editor.value = '';
  localStorage.removeItem(STORAGE_KEY);
  updatePreview();
  pdfPlaceholder.classList.remove('is-hidden');
  pdfFrame.classList.add('is-hidden');
  btnDownloadPdf.disabled = true;
  btnPrintVector.disabled = true;
});

btnSave.addEventListener('click', () => {
  const text = editor.value;
  if (!text.trim()) {
    alert('The editor is currently empty.');
    return;
  }
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'resume.md';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

btnDownloadPdf.addEventListener('click', () => {
  if (currentPdfDoc) currentPdfDoc.download('resume.pdf');
});

btnPrintVector.addEventListener('click', () => {
  if (currentPdfDoc) currentPdfDoc.print();
});

btnConvert.addEventListener('click', generatePdf);

// Initialize
const savedDraft = localStorage.getItem(STORAGE_KEY);
if (savedDraft !== null && savedDraft.trim()) {
  editor.value = savedDraft;
  updatePreview();
  generatePdf();
} else {
  loadExampleResume();
}
