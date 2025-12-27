import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rivet - Voice-First CMMS for Field Technicians",
  description: "Create work orders by voice. Ask AI about any schematic. Works on Telegram - no app to install.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
