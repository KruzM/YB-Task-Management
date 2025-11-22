// app/auth/login/page.jsx
"use client";

import Image from "next/image";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
  e.preventDefault();
  setError("");

  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  try {
const res = await fetch("http://10.0.0.237:8000/auth/login", {
  method: "POST",
  mode: "cors",
  headers: {
    "Content-Type": "application/x-www-form-urlencoded",
  },
  body,
});
    if (!res.ok) {
      setError("Invalid email or password.");
      return;
    }

    const data = await res.json();

    // Save token + user
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));

    router.push("/dashboard");
  } catch (err) {
    console.error(err);
    setError("Login failed.");
  }
};

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-[#F5F6F7]">
      <div className="w-full max-w-md bg-white shadow-lg rounded-2xl p-8 border border-gray-200">
        
        {/* Logo */}
        <div className="w-full flex justify-center mb-6">
          <Image
            src="/logo.png"
            alt="YECNY Logo"
            width={220}
            height={70}
            className="object-contain"
          />
        </div>

        <h2 className="text-center text-2xl font-bold text-gray-800 mb-6">
          Login to Your Account
        </h2>

        {error && (
          <p className="text-red-600 text-sm text-center mb-3">{error}</p>
        )}

        <form onSubmit={handleLogin} className="space-y-5">

          <div>
            <label className="text-sm font-medium text-gray-700">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="mt-1"
            />
          </div>

          <Button
            type="submit"
            className="w-full bg-[#1B7F81] hover:bg-[#16696B] text-white font-semibold py-2 rounded-lg"
          >
            Login
          </Button>
        </form>

        <div className="mt-4 text-center text-sm text-gray-600">
          <a href="#" className="hover:underline text-[#1B7F81]">
            Forgot your password?
          </a>
        </div>
      </div>
    </div>
  );
}
