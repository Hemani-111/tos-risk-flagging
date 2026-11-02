"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "@/components/ThemeProvider";
import { Button } from "@/components/ui/Button";
import { FileText, Moon, Sun, Menu, X, Upload } from "lucide-react";
import { useState } from "react";

function NavbarContent() {
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navLinks = [
    { href: "/about", label: "Methodology" },
    { href: "/research", label: "Research" },
  ];

  const linkClass = (href: string) =>
    `rounded-md px-3 py-2 text-sm font-medium transition-colors ${pathname === href ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary/70 hover:text-foreground"}`;

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
      <nav aria-label="Main navigation" className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 rounded-md text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" aria-label="TermsGuard home">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground"><FileText className="h-4 w-4" aria-hidden="true" /></span>
          <span className="text-base font-semibold tracking-tight">TermsGuard</span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => <Link key={link.href} href={link.href} className={linkClass(link.href)} aria-current={pathname === link.href ? "page" : undefined}>{link.label}</Link>)}
        </div>

        <div className="hidden items-center gap-2 md:flex">
          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}>
            {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>
          <Link href="/analyze"><Button size="sm"><Upload className="mr-2 h-4 w-4" />Analyze document</Button></Link>
        </div>

        <div className="flex items-center gap-1 md:hidden">
          <Button variant="ghost" size="icon" onClick={toggleTheme} aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}>
            {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen((open) => !open)} aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={mobileMenuOpen} aria-controls="mobile-navigation">
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </nav>

      {mobileMenuOpen && <div id="mobile-navigation" className="border-t border-border bg-background px-4 py-3 md:hidden">
        <div className="mx-auto flex max-w-6xl flex-col gap-1">
          {navLinks.map((link) => <Link key={link.href} href={link.href} className={linkClass(link.href)} aria-current={pathname === link.href ? "page" : undefined} onClick={() => setMobileMenuOpen(false)}>{link.label}</Link>)}
          <Link href="/analyze" className="mt-2" onClick={() => setMobileMenuOpen(false)}><Button className="w-full"><Upload className="mr-2 h-4 w-4" />Analyze document</Button></Link>
        </div>
      </div>}
    </header>
  );
}

export function Navbar() {
  return <NavbarContent />;
}
