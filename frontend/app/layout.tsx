import type { Metadata } from 'next';
import { Inter } from 'next/font/google';

import { AppShell } from '@/components/layout/app-shell';
import { Providers } from '@/components/providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Territory Growth Intelligence',
  description: 'Territory Growth Intelligence frontend foundation.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
