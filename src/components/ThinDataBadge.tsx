export function ThinDataBadge() {
  return (
    <span
      title="Fewer than 6 matches played this season — rating may be unreliable"
      className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
      style={{ backgroundColor: "var(--warning-bg)", color: "var(--warning-fg)" }}
    >
      Limited data
    </span>
  );
}
