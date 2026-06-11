import { existsSync, readFileSync } from "fs";

export function readFile(path: string): string {
  if (!existsSync(path)) {
    throw new Error(`File not found: ${path}`);
  }
  const content = readFileSync(path, "utf-8").trim();
  if (!content) {
    throw new Error(`File is empty: ${path}`);
  }
  return content;
}
