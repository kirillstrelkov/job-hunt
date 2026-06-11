import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TailorCV",
  description: "Tailor your CV to a job description with a local LLM",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full bg-gray-950 text-gray-100">
      <body className="h-full">{children}</body>
    </html>
  );
}
