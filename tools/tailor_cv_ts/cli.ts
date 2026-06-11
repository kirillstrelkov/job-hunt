#!/usr/bin/env tsx
import { program } from "commander";
import { writeFileSync } from "fs";

import { readFile }                              from "./src/reader";
import { toPlainText }                           from "./src/text";
import { logger, setLogLevel }                   from "./src/logger";
import {
  SYSTEM_PROMPT, COVER_LETTER_SYSTEM_PROMPT,
  DEFAULT_HEADER, DEFAULT_FOOTER,
  buildUserMessage, buildCoverLetterMessage,
}                                                from "./src/prompt";
import { callOllama, DEFAULT_MODEL }             from "./src/llm";
import { callGemini }                            from "./src/llm_gemini";
import { convertToPdf }                          from "./src/pdf";

async function callLlm(system: string, userMessage: string, model: string): Promise<string> {
  if (model.startsWith("gemini")) return callGemini(system, userMessage, model);
  return callOllama(system, userMessage, model);
}

program
  .name("tailor_cv")
  .description("Tailor a master CV to a job description using a local or cloud LLM")
  .requiredOption("-i, --input <path>",   "Path to master CV plain text file")
  .requiredOption("-j, --job <path>",     "Path to job description plain text file")
  .requiredOption("-o, --output <path>",  "Output base path (.md or .pdf — both files are always written)")
  .option("-l, --log-level <level>",      "Log level (debug|info|warning|error)", "info")
  .option("-m, --model <model>",          "Model name — prefix with 'gemini' to use Gemini API")
  .option("--cov",                        "Also generate a cover letter")
  .option("--header <path>",              "Header .md file (default placeholder used if omitted)")
  .option("--footer <path>",              "Footer .md file (default placeholder used if omitted)")
  .action(async (opts) => {
    setLogLevel(opts.logLevel);

    const ext = opts.output.split(".").pop()?.toLowerCase();
    if (ext !== "md" && ext !== "pdf") {
      logger.error(`Output must be .md or .pdf, got '.${ext}'`);
      process.exit(1);
    }

    logger.info(`Reading master CV from ${opts.input}`);
    const masterCv = readFile(opts.input);

    logger.info(`Reading job description from ${opts.job}`);
    const jobDescription = toPlainText(readFile(opts.job));

    const model = opts.model ?? DEFAULT_MODEL;
    const userMsg = buildUserMessage(masterCv, jobDescription);

    logger.debug("Messages built, sending to LLM");
    const tailored = await callLlm(SYSTEM_PROMPT, userMsg, model);

    const headerText = opts.header ? readFile(opts.header) : DEFAULT_HEADER;
    const footerText = opts.footer ? readFile(opts.footer) : DEFAULT_FOOTER;
    const fullCv = `${headerText.trimEnd()}\n\n${tailored.trim()}\n\n${footerText.trim()}\n`;

    const base   = opts.output.replace(/\.(md|pdf)$/i, "");
    const mdPath  = `${base}.md`;
    const pdfPath = `${base}.pdf`;

    writeFileSync(mdPath, fullCv, "utf-8");
    logger.success(`Tailored CV Markdown written to ${mdPath}`);
    convertToPdf(mdPath, pdfPath);
    logger.success(`Tailored CV PDF written to ${pdfPath}`);

    if (opts.cov) {
      logger.info("Generating cover letter");
      const covMsg = buildCoverLetterMessage(masterCv, jobDescription);
      const coverText = await callLlm(COVER_LETTER_SYSTEM_PROMPT, covMsg, model);

      const covMd  = `${base}_cover.md`;
      const covPdf = `${base}_cover.pdf`;
      writeFileSync(covMd, coverText, "utf-8");
      logger.success(`Cover letter Markdown written to ${covMd}`);
      convertToPdf(covMd, covPdf);
      logger.success(`Cover letter PDF written to ${covPdf}`);
    }
  });

program.parseAsync(process.argv).catch((err) => {
  console.error(err.message);
  process.exit(1);
});
