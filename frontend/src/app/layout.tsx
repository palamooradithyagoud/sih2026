import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Criminal Investigation Knowledge Graph | SIH 2026",
  description:
    "AI-Assisted Investigation over an Officer-Verified Criminal Knowledge Graph - Phase 1 Base Project",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <div className="bg-mesh" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
