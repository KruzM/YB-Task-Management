export default function Badge({ children, tone = "muted" }) {
  const cls = tone === "muted" ? "badge badge-muted" : "badge badge-accent";
  return <span className={cls}>{children}</span>;
}