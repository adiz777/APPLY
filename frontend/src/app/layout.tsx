import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "APPLY — Autonomous Personal Application & Recruitment Intelligence System",
  description:
    "AI-powered international recruitment command centre, visa sponsorship intelligence, factual CV tailoring, and human-approved application automation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#050914] text-slate-100 antialiased selection:bg-sky-500/30 selection:text-sky-200">
        {children}
      </body>
    </html>
  );
}
