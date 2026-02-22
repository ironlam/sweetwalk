import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sweet Walk",
  description: "Find the most beautiful walk from A to B",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased h-screen w-screen overflow-hidden">{children}</body>
    </html>
  );
}
