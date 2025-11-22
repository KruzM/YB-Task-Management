"use client";
import { useAuth } from "../hooks/useAuth";

export default function ProtectedLayout({ children }) {
  const { user } = useAuth();

  if (!user) return null; // while redirecting

  return <>{children}</>;
}