import { NextResponse } from "next/server";
import { readFileSync } from "fs";
import { join } from "path";

const DIR = join(process.cwd(), "prompts");
const read = (f: string) => readFileSync(join(DIR, f), "utf-8");

export async function GET() {
  return NextResponse.json({
    header:    read("default_header.md"),
    footer:    read("default_footer.md"),
    cvSystem:  read("cv_system.txt"),
    cvUser:    read("cv_user.txt"),
    covSystem: read("cover_letter_system.txt"),
    covUser:   read("cover_letter_user.txt"),
  });
}
