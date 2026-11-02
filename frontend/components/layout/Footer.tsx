import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-6 text-sm sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p className="text-muted-foreground">TermsGuard <span aria-hidden="true">·</span> Educational screening, not legal advice.</p>
        <div className="flex gap-5">
          <Link href="/about" className="text-muted-foreground transition-colors hover:text-foreground">Methodology</Link>
          <Link href="/research" className="text-muted-foreground transition-colors hover:text-foreground">Research</Link>
        </div>
      </div>
    </footer>
  );
}
