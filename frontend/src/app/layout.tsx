import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({ 
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Lokigi - Local SEO Intelligence",
  description: "Descubra por qué sus clientes no lo encuentran. Análisis de visibilidad local en 60 segundos.",
  keywords: "SEO local, Google Maps, análisis de visibilidad, PYMES, small business",
  authors: [{ name: "Lokigi" }],
  openGraph: {
    title: "Lokigi - Local SEO Intelligence",
    description: "Análisis de visibilidad local en 60 segundos",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}

