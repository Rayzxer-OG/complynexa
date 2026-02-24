import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthNav } from "@/components/AuthNav";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Complyon — AI-powered compliance tracking",
  description: "AI-powered compliance tracking. Automate document expiry detection with AWS Textract OCR and AI extraction.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-16x16.png", type: "image/png", sizes: "16x16" },
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
    ],
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-white font-sans text-slate-900 antialiased">
        <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-white/90">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:h-20">
            <a href="/" className="flex items-center">
              <img
                src="/complyon-logo.png"
                alt="Complyon"
                className="h-12 w-auto object-contain sm:h-14"
              />
            </a>
            <AuthNav />
          </div>
        </header>
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  );
}
