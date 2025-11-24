export default function Topbar({ user }) {
  const initial =
    user?.full_name?.[0]?.toUpperCase() ??
    user?.email?.[0]?.toUpperCase() ??
    "U";

  return (
    <div className="topbar">
      <div />
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: "50%",
            background: "#E5E7EB",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 700,
            color: "#374151",
          }}
        >
          {initial}
        </div>

        <div style={{ fontWeight: 600 }}>
          {user?.full_name ?? user?.email ?? ""}
        </div>
      </div>
    </div>
  );
}
