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
      <body className="h-full bg-ocean-950 text-slate-100 overflow-hidden font-sans antialiased">
        <OceanProvider>
          {children}
        </OceanProvider>
      </body>
    </html>
  );
}
