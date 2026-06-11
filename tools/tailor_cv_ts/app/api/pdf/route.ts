import { NextRequest, NextResponse } from "next/server";
import { writeFileSync, readFileSync, unlinkSync } from "fs";
import { join } from "path";
import { tailorTmpDir } from "@/src/tmpdir";

import { convertToPdf } from "@/src/pdf";

export async function POST(req: NextRequest) {
  const { markdown } = await req.json();
  if (!markdown?.trim()) {
    return NextResponse.json({ error: "Markdown is empty" }, { status: 400 });
  }

  const ts      = Date.now();
  const mdPath  = join(tailorTmpDir(), `tailor_pdf_${ts}.md`);
  const pdfPath = join(tailorTmpDir(), `tailor_pdf_${ts}.pdf`);
  try {
    writeFileSync(mdPath, markdown, "utf-8");
    convertToPdf(mdPath, pdfPath);
    const pdf = readFileSync(pdfPath).toString("base64");
    return NextResponse.json({ pdf });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: msg }, { status: 500 });
  } finally {
    try { unlinkSync(mdPath);  } catch {}
    try { unlinkSync(pdfPath); } catch {}
  }
}
