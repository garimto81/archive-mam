/**
 * Root Layout
 * Next.js 14 App Router root layout with navigation
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Link from 'next/link';
import { Search, Download, Heart, LayoutDashboard, Home } from 'lucide-react';
import './globals.css';
import { APP_CONFIG } from '@/lib/api-config';
import { cn } from '@/lib/utils';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: APP_CONFIG.APP_NAME,
  description: 'WSOP Archive - Search and download poker hand clips',
  keywords: ['poker', 'WSOP', 'tournament', 'archive', 'video'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/* Navigation */}
        <header className="sticky top-0 z-40 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center">
            <div className="mr-4 flex">
              <Link href="/" className="mr-6 flex items-center space-x-2">
                <LayoutDashboard className="h-6 w-6" />
                <span className="hidden font-bold sm:inline-block">{APP_CONFIG.APP_NAME}</span>
              </Link>
            </div>

            <nav className="flex items-center space-x-6 text-sm font-medium flex-1">
              <NavLink href="/" icon={<Home className="h-4 w-4" />}>
                Home
              </NavLink>
              <NavLink href="/search" icon={<Search className="h-4 w-4" />}>
                Search
              </NavLink>
              <NavLink href="/favorites" icon={<Heart className="h-4 w-4" />}>
                Favorites
              </NavLink>
              <NavLink href="/downloads" icon={<Download className="h-4 w-4" />}>
                Downloads
              </NavLink>
            </nav>

            {/* User menu placeholder */}
            <div className="ml-auto flex items-center space-x-4">
              <Link
                href="/admin"
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
              >
                Admin
              </Link>
            </div>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1">{children}</main>

        {/* Footer */}
        <footer className="border-t">
          <div className="container flex h-16 items-center justify-between py-4">
            <p className="text-sm text-muted-foreground">
              © 2024 GG Production. All rights reserved.
            </p>
            <p className="text-xs text-muted-foreground">
              Built with Next.js 14 + shadcn/ui
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

// Navigation link component
function NavLink({
  href,
  icon,
  children,
}: {
  href: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary',
        'text-muted-foreground'
      )}
    >
      {icon}
      <span className="hidden sm:inline">{children}</span>
    </Link>
  );
}
