import { NextRequest, NextResponse } from "next/server";

/**
 * Middleware currently handles route-level concerns (e.g. trailing slashes,
 * headers). Auth gating is done client-side in the dashboard layout via
 * the Zustand auth store's hydrate() — the refresh_token cookie is scoped
 * to /api/v1/auth by the backend, so it's invisible to page navigations.
 */

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function middleware(_request: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
