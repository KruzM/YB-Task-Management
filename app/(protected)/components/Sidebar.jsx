"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";

const NAV = [
  { name: "Dashboard", href: "/dashboard" },
  { name: "Clients", href: "/clients" },
  { name: "Tasks", href: "/tasks" },
  { name: "Audit Logs", href: "/audit" },
];

export default function Sidebar() {
  const path = usePathname() || "/";
  return (
    <aside className="sidebar" aria-label="Sidebar">
      <div className="logoWrap">
        <div style={{ width: 44, height: 44, borderRadius: 8, overflow: "hidden", background: "white", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Image src={"/logo.png"} alt="YB Logo" width={44} height={44} style={{ objectFit: "contain" }} />
        </div>
        <div className="brandTitle">YB Task Management</div>
      </div>

      <nav style={{ padding: "8px 6px", marginTop: 8 }}>
        {NAV.map((item) => {
          const active = path.startsWith(item.href);
          return (
            <Link key={item.href} href={item.href} className={`navItem ${active ? "active" : ""}`}>
              {item.name}
            </Link>
          );
        })}
      </nav>
  <div style={{ flex: 1 }} />

      <div style={{ padding: 16, color: "rgba(255,255,255,0.85)", fontSize: 13 }}>
      &copy; {new Date().getFullYear()} YB Bookkeeping
      </div>
    </aside>
  );
}
