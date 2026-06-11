import { NextRequest, NextResponse } from "next/server";
import { writeFileSync, readFileSync, unlinkSync } from "fs";
import { join } from "path";
import { tailorTmpDir } from "@/src/tmpdir";

import { toPlainText }    from "@/src/text";
import { callOllama }     from "@/src/llm";
import { callGemini }     from "@/src/llm_gemini";
import { callClaude }     from "@/src/llm_claude";
import { convertToPdf }   from "@/src/pdf";

// Allow long-running LLM calls (Vercel / Next.js limit)
export const maxDuration = 300;

interface TailorRequest {
  masterCv:    string;
  jobDesc:     string;
  header:      string;
  footer:      string;
  cvSystem:    string;
  cvUser:      string;
  covSystem:   string;
  covUser:     string;
  model:         string;
  genCover:      boolean;
  geminiApiKey?: string;
  claudeApiKey?: string;
}

async function callLlm(
  system: string,
  userMessage: string,
  model: string,
  geminiApiKey?: string,
  claudeApiKey?: string,
): Promise<string> {
  if (model.startsWith("gemini")) {
    if (geminiApiKey) process.env.GEMINI_API_KEY = geminiApiKey;
    return callGemini(system, userMessage, model);
  }
  if (model.startsWith("claude")) {
    if (claudeApiKey) process.env.ANTHROPIC_API_KEY = claudeApiKey;
    return callClaude(system, userMessage, model);
  }
  return callOllama(system, userMessage, model);
}

function makePdf(mdText: string): string | null {
  const ts    = Date.now();
  const mdPath  = join(tailorTmpDir(), `tailor_${ts}.md`);
  const pdfPath = join(tailorTmpDir(), `tailor_${ts}.pdf`);
  try {
    writeFileSync(mdPath, mdText, "utf-8");
    convertToPdf(mdPath, pdfPath);
    return readFileSync(pdfPath).toString("base64");
  } catch {
    return null;
  } finally {
    try { unlinkSync(mdPath);  } catch {}
    try { unlinkSync(pdfPath); } catch {}
  }
}

export async function POST(req: NextRequest) {
  const body: TailorRequest = await req.json();
  const { masterCv, jobDesc, header, footer, cvSystem, cvUser, covSystem, covUser, model, genCover, geminiApiKey, claudeApiKey } = body;

  if (!masterCv?.trim()) return NextResponse.json({ error: "Master CV is empty" }, { status: 400 });
  if (!jobDesc?.trim())  return NextResponse.json({ error: "Job Description is empty" }, { status: 400 });

  const cleanJobDesc = toPlainText(jobDesc);
  const userMsg = cvUser.replace("{cv}", masterCv).replace("{job_description}", cleanJobDesc);

  try {
    const tailored = await callLlm(cvSystem, userMsg, model, geminiApiKey, claudeApiKey);
    const fullCv   = `${header.trimEnd()}\n\n${tailored.trim()}\n\n${footer.trim()}\n`;
    const cvPdf    = makePdf(fullCv);

    let covMd:  string | null = null;
    let covPdf: string | null = null;

    if (genCover) {
      const covMsg = covUser.replace("{cv}", masterCv).replace("{job_description}", cleanJobDesc);
      covMd  = await callLlm(covSystem, covMsg, model, geminiApiKey, claudeApiKey);
      covPdf = makePdf(covMd);
    }

    return NextResponse.json({ cvMd: fullCv, cvPdf, covMd, covPdf });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
