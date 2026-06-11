import { mkdirSync } from "fs";

const TAILOR_TMP = "/tmp/tailor_cv";
mkdirSync(TAILOR_TMP, { recursive: true });

export function tailorTmpDir(): string {
  return TAILOR_TMP;
}
