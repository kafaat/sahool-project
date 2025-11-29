import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sahool Farmer Dashboard',
  description: 'Smart agriculture SaaS platform - field monitoring dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
