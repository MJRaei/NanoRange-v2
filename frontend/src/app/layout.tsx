import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NanOrange | Nanoparticle Image Analysis",
  description: "AI-powered nanoparticle detection and analysis from cryo-TEM microscopy images",
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
