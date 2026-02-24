import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const skip = searchParams.get("skip") ?? "0";
  const limit = searchParams.get("limit") ?? "20";
  const status = searchParams.get("status");
  const url = new URL(`${API_URL}/api/v1/certificates`);
  url.searchParams.set("skip", skip);
  url.searchParams.set("limit", limit);
  if (status) {
    url.searchParams.set("status_filter", status);
  }
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(url.toString(), {
      cache: "no-store",
      headers,
    });
    if (res.status === 401) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("Certificates proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
