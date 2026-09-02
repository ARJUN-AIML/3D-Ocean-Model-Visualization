import './globals.css';
import type { Metadata } from 'next';
import { OceanProvider } from '../context/OceanContext';

export const metadata: Metadata = {
  title: 'OceanTwin 3D | Interactive Ocean Visualization & Model Validation',
  description: 'Next-generation 3D Ocean Intelligence Platform powered by CesiumJS, React, TypeScript, and Tailwind CSS.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet" />
        <link rel="stylesheet" href="/cesium/Widgets/widgets.css" />
      </head>
      <body className="h-full bg-ocean-950 text-slate-100 overflow-hidden font-sans antialiased">
        <OceanProvider>
          {children}
        </OceanProvider>
      </body>
    </html>
  );
}
