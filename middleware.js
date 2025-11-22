import { NextResponse } from "next/server";

export function middleware(req) {
  const token = req.cookies.get("token")?.value || req.headers.get("authorization") || null;

  const isAuthPage = req.nextUrl.pathname.startsWith("/auth");
  const isProtected = req.nextUrl.pathname.startsWith("/dashboard");

  // Not logged in ? trying to access protected route
  if (!token && isProtected) {
    return NextResponse.redirect(new URL("/auth/login", req.url));
  }

  // Logged in ? trying to access login page
  if (token && isAuthPage) {
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/auth/:path*"
  ]
};
