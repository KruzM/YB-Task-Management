"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/app/lib/api";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

export default function ProtectedLayout({ children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const u = await apiFetch("/users/me");
        setUser(u);
      } catch (e) {
        console.error("Failed to load user", e);
      }
    }
    load();
  }, []);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <Topbar user={user} />

        <main>{children}</main>
      </div>
    </div>
  );
}