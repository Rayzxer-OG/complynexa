import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");
  const url = new URL(`${API_URL}/api/v1/documents`);
  if (status && ["active", "expiring_soon", "expired"].includes(status)) {
    url.searchParams.set("status", status);
  }
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(url.toString(), {
      cache: "no-store",
      headers,
    });
    if (!res.ok) {
      return NextResponse.json(
        { detail: "Failed to fetch documents" },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("Documents proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
