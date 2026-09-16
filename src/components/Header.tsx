const NAV_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#fixtures", label: "Fixtures" },
  { href: "#ratings", label: "Ratings" },
  { href: "#evaluator", label: "Bet evaluator" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-black/10 bg-white/80 backdrop-blur dark:border-white/10 dark:bg-black/60">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
        <a href="#" className="font-semibold tracking-tight">
          Pitch Model <span className="text-neutral-400">·</span>{" "}
          <span className="text-sm font-normal text-neutral-500">EPL predictions</span>
        </a>
        <nav className="hidden gap-5 text-sm text-neutral-600 sm:flex dark:text-neutral-300">
          {NAV_LINKS.map((l) => (
            <a key={l.href} href={l.href} className="hover:text-neutral-900 dark:hover:text-white">
              {l.label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
