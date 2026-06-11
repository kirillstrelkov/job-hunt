"use client";

import { useEffect, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";

// ── Types ─────────────────────────────────────────────────────────────────────

type Tab = "main" | "input" | "prompts" | "settings";

interface AppState {
  header: string;
  footer: string;
  masterCv: string;
  jobDesc: string;
  cvSystem: string;
  cvUser: string;
  covSystem: string;
  covUser: string;
  settingsJson: string;
}

interface Output {
  cvMd: string;
  cvPdf: string | null;
}

const DEFAULT_SETTINGS = JSON.stringify(
  {
    GEMINI_API_KEY: "",
    ANTHROPIC_API_KEY: "",
    models: [
      "gemma4:e2b",
      "llama3.1:8b",
      "deepseek-r1:7b",
      "qwen2.5:7b",
      "claude-opus-4-7",
      "claude-sonnet-4-6",
      "claude-haiku-4-5",
      "gemini-3.1-pro-preview",
      "gemini-3-flash-preview",
      "gemini-3.1-flash-lite-preview",
      "gemini-2.5-pro",
      "gemini-2.5-flash",
      "gemini-2.5-flash-lite",
      "gemini-2.0-flash",
    ],
  },
  null,
  2
);

const EMPTY_STATE: AppState = {
  header: "",
  footer: "",
  masterCv: "",
  jobDesc: "",
  cvSystem: "",
  cvUser: "",
  covSystem: "",
  covUser: "",
  settingsJson: DEFAULT_SETTINGS,
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function loadFile(cb: (content: string) => void) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".txt,.md";
  input.onchange = () => {
    const file = input.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => cb(reader.result as string);
    reader.readAsText(file);
  };
  input.click();
}

function downloadText(text: string, filename: string) {
  const blob = new URL(
    URL.createObjectURL(new Blob([text], { type: "text/markdown" }))
  );
  const a = document.createElement("a");
  a.href = blob.href;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(blob.href);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Field({
  label,
  value,
  onChange,
  rows = 14,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
}) {
  return (
    <div className="flex flex-col gap-1 h-full min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          {label}
        </span>
        <button
          onClick={() => loadFile(onChange)}
          className="text-xs px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 transition-colors"
        >
          📂 Load
        </button>
      </div>
      <textarea
        className="mono flex-1 min-h-0"
        rows={rows}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

function PdfPanel({ pdf, filename }: { pdf: string | null; filename: string }) {
  if (!pdf) {
    return (
      <div className="flex items-center justify-center h-full min-h-96 bg-gray-900 rounded border border-gray-700 text-gray-500 text-sm">
        PDF will appear here after tailoring.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-2 h-full">
      <iframe
        src={`data:application/pdf;base64,${pdf}`}
        className="flex-1 rounded border-none min-h-[700px]"
      />
      <a
        href={`data:application/pdf;base64,${pdf}`}
        download={filename}
        className="text-center py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-200 text-sm transition-colors"
      >
        ⬇ Download PDF
      </a>
    </div>
  );
}

function TabBar({
  active,
  onChange,
}: {
  active: Tab;
  onChange: (t: Tab) => void;
}) {
  const tabs: { id: Tab; label: string }[] = [
    { id: "main", label: "Main" },
    { id: "input", label: "Input" },
    { id: "prompts", label: "Prompts" },
    { id: "settings", label: "Settings" },
  ];
  return (
    <div className="flex gap-1 border-b border-gray-700 px-4 shrink-0">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
            active === t.id
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

// ── MarkdownPreview — self-contained markdown/preview editor ──────────────────

function MarkdownPreview({
  value,
  onChange,
  placeholder,
  topRight,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  topRight?: React.ReactNode;
}) {
  const [subTab, setSubTab] = useState<"markdown" | "preview">("markdown");
  return (
    <div className="flex flex-col gap-1 h-full min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <div className="flex gap-1">
          {(["markdown", "preview"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setSubTab(t)}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                subTab === t
                  ? "bg-gray-700 text-gray-100"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {t === "markdown" ? "Markdown" : "Preview"}
            </button>
          ))}
        </div>
        {topRight && <div className="flex items-center gap-1">{topRight}</div>}
      </div>
      <div className="flex-1 min-h-0 bg-gray-900 rounded border border-gray-700 overflow-hidden">
        {subTab === "markdown" ? (
          <textarea
            className="mono w-full h-full bg-transparent p-4 resize-none focus:outline-none text-sm text-gray-300 leading-relaxed"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
          />
        ) : (
          <div className="h-full overflow-y-auto p-4">
            {value ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown>{value}</ReactMarkdown>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">{placeholder}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ── MarkdownField — label + load button + MarkdownPreview ─────────────────────

function MarkdownField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1 h-full min-h-0">
      <div className="flex items-center justify-between shrink-0">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          {label}
        </span>
        <button
          onClick={() => loadFile(onChange)}
          className="text-xs px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 transition-colors"
        >
          📂 Load
        </button>
      </div>
      <div className="flex-1 min-h-0">
        <MarkdownPreview value={value} onChange={onChange} />
      </div>
    </div>
  );
}

// ── MdPanel — MarkdownPreview with download + extra action buttons ────────────

function MdPanel({
  value,
  onChange,
  placeholder,
  downloadName,
  extraActions,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  downloadName: string;
  extraActions?: React.ReactNode;
}) {
  return (
    <MarkdownPreview
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      topRight={
        <>
          {extraActions}
          {value && (
            <button
              onClick={() => downloadText(value, downloadName)}
              className="text-xs px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
            >
              ⬇ .md
            </button>
          )}
        </>
      }
    />
  );
}

// ── LoadingModal ──────────────────────────────────────────────────────────────

function LoadingModal({ model }: { model: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl px-10 py-8 flex flex-col items-center gap-4 shadow-2xl max-w-sm w-full mx-4">
        <div className="w-10 h-10 rounded-full border-4 border-gray-700 border-t-blue-500 animate-spin" />
        <div className="text-center">
          <p className="text-gray-100 font-semibold text-base">Tailoring your CV…</p>
          <p className="text-gray-400 text-sm mt-1">
            Running <span className="text-blue-400 font-mono">{model}</span>
          </p>
          <p className="text-gray-500 text-xs mt-2">This may take a minute or two.</p>
        </div>
      </div>
    </div>
  );
}

// ── ResizeHandle — horizontal drag divider ────────────────────────────────────

function ResizeHandle({
  onMouseDown,
}: {
  onMouseDown: (e: React.MouseEvent) => void;
}) {
  return (
    <div
      onMouseDown={onMouseDown}
      className="w-1.5 shrink-0 self-stretch cursor-col-resize rounded mx-0.5
                 bg-gray-800 hover:bg-blue-500 active:bg-blue-400 transition-colors"
    />
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Home() {
  const [tab, setTab] = useState<Tab>("main");
  const [state, setState] = useState<AppState>(EMPTY_STATE);
  const [model, setModel] = useState("");
  const [output, setOutput] = useState<Output | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // CV markdown panel
  const [editableMd, setEditableMd] = useState("");
  const [pdfConverting, setPdfConverting] = useState(false);

  // Cover letter panel
  const [coverOpen, setCoverOpen] = useState(false);
  const [editableCovMd, setEditableCovMd] = useState("");
  const [covPdf, setCovPdf] = useState<string | null>(null);
  const [covLoading, setCovLoading] = useState(false);
  const [covPdfConverting, setCovPdfConverting] = useState(false);

  // Resizable panels
  const [leftWidth, setLeftWidth] = useState(450);

  const set = useCallback(
    (key: keyof AppState) => (value: string) =>
      setState((s) => ({ ...s, [key]: value })),
    []
  );

  useEffect(() => {
    if (!output) return;
    setEditableMd(output.cvMd);
  }, [output]);

  useEffect(() => {
    fetch("/api/prompts")
      .then((r) => r.json())
      .then((d) => {
        setState((s) => ({
          ...s,
          header: d.header,
          footer: d.footer,
          cvSystem: d.cvSystem,
          cvUser: d.cvUser,
          covSystem: d.covSystem,
          covUser: d.covUser,
        }));
      });
  }, []);

  const settings = (() => {
    try {
      return JSON.parse(state.settingsJson);
    } catch {
      return {};
    }
  })();
  const models = (settings.models ?? ["gemma4:e2b"]) as string[];
  const activeModel = model || models[0] || "gemma4:e2b";

  function handleCvResizeMouseDown(e: React.MouseEvent) {
    e.preventDefault();
    const startX = e.clientX;
    const startW = leftWidth;
    const onMove = (ev: MouseEvent) =>
      setLeftWidth(Math.max(200, startW + ev.clientX - startX));
    const onUp = () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
  }

  async function handleTailor() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/tailor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          masterCv: state.masterCv,
          jobDesc: state.jobDesc,
          header: state.header,
          footer: state.footer,
          cvSystem: state.cvSystem,
          cvUser: state.cvUser,
          covSystem: state.covSystem,
          covUser: state.covUser,
          model: activeModel,
          genCover: false,
          geminiApiKey: settings.GEMINI_API_KEY ?? "",
          claudeApiKey: settings.ANTHROPIC_API_KEY ?? "",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Request failed");
      setOutput({ cvMd: data.cvMd, cvPdf: data.cvPdf });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateCover() {
    if (!state.masterCv?.trim()) {
      setError("Master CV is empty");
      return;
    }
    if (!state.jobDesc?.trim()) {
      setError("Job Description is empty");
      return;
    }
    setCovLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/cover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          masterCv: state.masterCv,
          jobDesc: state.jobDesc,
          covSystem: state.covSystem,
          covUser: state.covUser,
          model: activeModel,
          geminiApiKey: settings.GEMINI_API_KEY ?? "",
          claudeApiKey: settings.ANTHROPIC_API_KEY ?? "",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Request failed");
      setEditableCovMd(data.covMd);
      setCovPdf(data.covPdf);
      setCoverOpen(true);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCovLoading(false);
    }
  }

  async function handleConvertPdf() {
    if (!editableMd.trim()) return;
    setPdfConverting(true);
    setError(null);
    try {
      const res = await fetch("/api/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown: editableMd }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "PDF conversion failed");
      setOutput({ cvMd: editableMd, cvPdf: data.pdf });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setPdfConverting(false);
    }
  }

  async function handleConvertCovPdf() {
    if (!editableCovMd.trim()) return;
    setCovPdfConverting(true);
    setError(null);
    try {
      const res = await fetch("/api/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ markdown: editableCovMd }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "PDF conversion failed");
      setCovPdf(data.pdf);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCovPdfConverting(false);
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100">
      {loading && <LoadingModal model={activeModel} />}
      <div className="px-4 py-3 border-b border-gray-800 shrink-0">
        <h1 className="text-lg font-bold tracking-tight">📄 TailorCV</h1>
      </div>

      <TabBar active={tab} onChange={setTab} />

      <div className="flex-1 overflow-hidden">
        {/* ── Main ─────────────────────────────────────────────────────────── */}
        {tab === "main" && (
          <div className="flex flex-col h-full p-4 gap-3">
            {/* Controls */}
            <div className="flex items-end gap-3 shrink-0">
              <div className="flex flex-col gap-1">
                <label className="text-xs text-gray-400">Model</label>
                <select
                  value={activeModel}
                  onChange={(e) => setModel(e.target.value)}
                  className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
                >
                  {models.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleGenerateCover}
                disabled={covLoading}
                className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50
                           rounded text-sm font-semibold transition-colors self-end"
              >
                {covLoading ? "⏳ Generating…" : "✉  Generate Cover Letter"}
              </button>

              <div className="ml-auto flex gap-2">
                <button
                  onClick={handleConvertPdf}
                  disabled={pdfConverting || !editableMd.trim()}
                  className="px-4 py-1.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50
                             rounded text-sm font-semibold transition-colors"
                >
                  {pdfConverting
                    ? "⏳ Converting…"
                    : "📄 Convert Markdown to PDF"}
                </button>
                <button
                  onClick={handleTailor}
                  disabled={loading}
                  className="px-6 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50
                             rounded text-sm font-semibold transition-colors"
                >
                  {loading ? "⏳ Tailoring…" : "▶  Tailor CV with LLM"}
                </button>
              </div>
            </div>

            {error && (
              <div className="shrink-0 px-3 py-2 bg-red-900/40 border border-red-700 rounded text-red-300 text-sm">
                {error}
              </div>
            )}

            {/* Panels */}
            <div className="flex flex-1 min-h-0">
              {/* CV Markdown */}
              <div
                style={{ width: leftWidth, minWidth: 200, flexShrink: 0 }}
                className="min-h-0"
              >
                <MdPanel
                  value={editableMd}
                  onChange={setEditableMd}
                  placeholder="Tailored CV will appear here after clicking Tailor CV with LLM."
                  downloadName="tailored_cv.md"
                />
              </div>

              <ResizeHandle onMouseDown={handleCvResizeMouseDown} />

              {/* CV PDF */}
              <div className="flex-1 flex flex-col gap-2 min-h-0">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide shrink-0">
                  PDF
                </span>
                <div className="flex-1 min-h-0">
                  <PdfPanel
                    pdf={output?.cvPdf ?? null}
                    filename="tailored_cv.pdf"
                  />
                </div>
              </div>

              {/* Cover Letter expandable panel */}
              <div
                className={`flex shrink-0 min-h-0 transition-all duration-300 ease-in-out pl-2 ${
                  coverOpen ? "w-[420px]" : "w-8"
                }`}
              >
                <button
                  onClick={() => setCoverOpen((p) => !p)}
                  title={
                    coverOpen ? "Collapse cover letter" : "Expand cover letter"
                  }
                  className="w-8 shrink-0 flex items-center justify-center bg-gray-800 hover:bg-gray-700
                             border border-gray-700 rounded transition-colors"
                >
                  <span
                    className="text-xs text-gray-400 font-medium select-none"
                    style={{
                      writingMode: "vertical-lr",
                      transform: "rotate(180deg)",
                    }}
                  >
                    Cover Letter{editableCovMd ? " ●" : ""}
                  </span>
                </button>

                <div
                  className={`flex-1 flex flex-col gap-2 min-h-0 overflow-hidden pl-2
                                transition-opacity duration-200 ${
                                  coverOpen
                                    ? "opacity-100"
                                    : "opacity-0 pointer-events-none"
                                }`}
                >
                  <MdPanel
                    value={editableCovMd}
                    onChange={setEditableCovMd}
                    placeholder="Cover letter will appear here after clicking Generate Cover Letter."
                    downloadName="cover_letter.md"
                    extraActions={
                      editableCovMd ? (
                        <button
                          onClick={handleConvertCovPdf}
                          disabled={covPdfConverting}
                          className="text-xs px-2 py-0.5 bg-gray-700 hover:bg-gray-600
                                     disabled:opacity-50 rounded text-gray-300"
                        >
                          {covPdfConverting ? "⏳" : "📄 PDF"}
                        </button>
                      ) : undefined
                    }
                  />
                  {covPdf && (
                    <a
                      href={`data:application/pdf;base64,${covPdf}`}
                      download="cover_letter.pdf"
                      className="shrink-0 text-center py-1.5 bg-gray-700 hover:bg-gray-600
                                 rounded text-gray-200 text-sm transition-colors"
                    >
                      ⬇ Download Cover Letter PDF
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Input ────────────────────────────────────────────────────────── */}
        {tab === "input" && (
          <div className="grid grid-cols-3 gap-4 h-full p-4">
            <div className="flex flex-col gap-4 min-h-0">
              <div className="flex-1 min-h-0">
                <MarkdownField
                  label="Header"
                  value={state.header}
                  onChange={set("header")}
                />
              </div>
              <div className="flex-1 min-h-0">
                <MarkdownField
                  label="Footer"
                  value={state.footer}
                  onChange={set("footer")}
                />
              </div>
            </div>
            <div className="min-h-0">
              <MarkdownField
                label="Master CV"
                value={state.masterCv}
                onChange={set("masterCv")}
              />
            </div>
            <div className="min-h-0">
              <Field
                label="Job Description"
                value={state.jobDesc}
                onChange={set("jobDesc")}
                rows={40}
              />
            </div>
          </div>
        )}

        {/* ── Prompts ──────────────────────────────────────────────────────── */}
        {tab === "prompts" && (
          <div className="grid grid-cols-2 gap-4 h-full p-4">
            <div className="flex flex-col gap-4 min-h-0">
              <div className="flex-1 min-h-0">
                <Field
                  label="CV System Prompt"
                  value={state.cvSystem}
                  onChange={set("cvSystem")}
                  rows={18}
                />
              </div>
              <div className="flex-1 min-h-0">
                <Field
                  label="CV User Template"
                  value={state.cvUser}
                  onChange={set("cvUser")}
                  rows={18}
                />
              </div>
            </div>
            <div className="flex flex-col gap-4 min-h-0">
              <div className="flex-1 min-h-0">
                <Field
                  label="Cover Letter System Prompt"
                  value={state.covSystem}
                  onChange={set("covSystem")}
                  rows={18}
                />
              </div>
              <div className="flex-1 min-h-0">
                <Field
                  label="Cover Letter User Template"
                  value={state.covUser}
                  onChange={set("covUser")}
                  rows={18}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Settings ─────────────────────────────────────────────────────── */}
        {tab === "settings" && (
          <div className="flex flex-col gap-3 p-4 max-w-2xl">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                Configuration (JSON)
              </span>
              <button
                onClick={() => {
                  try {
                    JSON.parse(state.settingsJson);
                    setError(null);
                    alert("Valid JSON ✓");
                  } catch (e: unknown) {
                    setError(e instanceof Error ? e.message : "Invalid JSON");
                  }
                }}
                className="text-xs px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300"
              >
                Validate
              </button>
            </div>
            <textarea
              className="mono"
              rows={20}
              value={state.settingsJson}
              onChange={(e) => set("settingsJson")(e.target.value)}
            />
            <p className="text-xs text-gray-500">
              <code>models</code> populates the model dropdown. Set{" "}
              <code>ANTHROPIC_API_KEY</code> for Claude models (prefix with{" "}
              <code>claude</code>), <code>GEMINI_API_KEY</code> for Gemini
              models (prefix with <code>gemini</code>). Models without a prefix
              use local Ollama.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
