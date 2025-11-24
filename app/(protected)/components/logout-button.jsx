// app/(protected)/components/logout-button.jsx
"use client";

import { useRouter } from "next/navigation";

export default function LogoutButton() {
  const router = useRouter();

  async function logout() {
    try {
      await fetch((process.env.NEXT_PUBLIC_API_BASE_URL || "") + "/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (err) {
      console.error("Logout request failed:", err);
    } finally {
      try { localStorage.removeItem("user"); } catch {}
      router.push("/login");
    }
  }

  return (
    <button
      onClick={logout}
      className="px-4 py-2 bg-red-600 text-white rounded"
    >
      Logout
    </button>
  );
}