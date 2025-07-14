import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "EZBI Analytics - Early Warning Systems for SMEs",
  description: "Stop financial surprises before they kill your business. Cash Flow Radar, Deal Warning System, and Pipeline Health Monitor for SMEs.",
  keywords: ["SME analytics", "cash flow monitoring", "sales pipeline", "business intelligence", "early warning systems"],
  authors: [{ name: "Philippe Béliveau", url: "mailto:philippebeliveau@ezbi.ca" }],
  creator: "EZBI Analytics",
  publisher: "EZBI Analytics",
  robots: "index, follow",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#000000",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}