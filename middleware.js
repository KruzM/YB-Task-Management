// middleware.js
import { NextResponse } from "next/server";

const protectedRoutes = ["/dashboard", "/clients"];

export function middleware(req) {
  const { pathname } = req.nextUrl;

  // Allow next internals, static assets and the login page
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/static") ||
    pathname === "/favicon.ico" ||
    pathname === "/login" ||
    pathname.startsWith("/api") // allow api proxied calls if any
  ) {
    return NextResponse.next();
  }

  const needsAuth = protectedRoutes.some((r) => pathname === r || pathname.startsWith(r + "/"));

  // Read token cookie (if present)
  const token = req.cookies.get("token")?.value || null;

  if (needsAuth && !token) {
    // Redirect to frontend login page (not backend)
    const loginUrl = req.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/clients/:path*"],
};