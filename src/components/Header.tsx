const NAV_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#fixtures", label: "Matches" },
  { href: "#ratings", label: "Ratings" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3.5 sm:px-6">
        <a href="#" className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand text-xs font-bold text-brand-foreground">
            G
          </span>
          <span className="font-semibold tracking-tight">gambitParlay</span>
          <span className="hidden text-sm font-normal text-muted sm:inline">EPL predictions</span>
        </a>
        <nav className="hidden gap-6 text-sm font-medium text-muted sm:flex">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="transition-colors hover:text-foreground">
              {l.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
