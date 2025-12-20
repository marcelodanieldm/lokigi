import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lokigi - Auditoría SEO Local",
  description: "Resultados de tu auditoría de SEO Local",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
