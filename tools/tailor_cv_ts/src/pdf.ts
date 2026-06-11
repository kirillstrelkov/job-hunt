import { execSync } from "child_process";
import { logger } from "./logger";

export function convertToPdf(mdPath: string, pdfPath: string): void {
  logger.info(`Converting ${mdPath} → ${pdfPath} via pandoc`);
  try {
    execSync(
      `pandoc -V papersize=a4 -V geometry:margin=1.5cm "${mdPath}" -o "${pdfPath}"`,
      { stdio: "pipe" }
    );
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    throw new Error(`pandoc failed:\n${msg}`);
  }
}
