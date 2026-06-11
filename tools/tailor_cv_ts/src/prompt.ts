import { readFileSync } from "fs";
import { join } from "path";

export const PROMPTS_DIR = join(__dirname, "..", "prompts");

function load(filename: string): string {
  return readFileSync(join(PROMPTS_DIR, filename), "utf-8");
}

export const SYSTEM_PROMPT               = load("cv_system.txt");
export const USER_TEMPLATE               = load("cv_user.txt");
export const COVER_LETTER_SYSTEM_PROMPT  = load("cover_letter_system.txt");
export const COVER_LETTER_USER_TEMPLATE  = load("cover_letter_user.txt");
export const DEFAULT_HEADER              = load("default_header.md");
export const DEFAULT_FOOTER              = load("default_footer.md");

export function buildUserMessage(masterCv: string, jobDescription: string): string {
  return USER_TEMPLATE.replace("{cv}", masterCv).replace("{job_description}", jobDescription);
}

export function buildCoverLetterMessage(masterCv: string, jobDescription: string): string {
  return COVER_LETTER_USER_TEMPLATE.replace("{cv}", masterCv).replace("{job_description}", jobDescription);
}
