import type { Metadata } from "next";
import { Figtree, Newsreader } from "next/font/google";

import { Header } from "@/components/Header";
import "./globals.css";

const sans = Figtree({ subsets: ["latin"], variable: "--font-figtree" });
const serif = Newsreader({ subsets: ["latin"], variable: "--font-newsreader" });

export const metadata: Metadata = {
  title: "Multi-Agent Article Studio",
  description: "複数のAIエージェントが役割分担して記事を作成します",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body className={`${sans.variable} ${serif.variable} font-sans antialiased`}>
        <Header />
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
      </body>
    </html>
  );
}
