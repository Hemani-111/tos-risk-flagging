export function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 py-8 sm:flex-row">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">TermsGuard · Educational screening, not legal advice</span>
          </div>
          <a href="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Methodology and limitations</a>
        </div>
      </div>
    </footer>
  );
}
