import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(request: NextRequest) {
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(`${API_URL}/api/v1/certificates/grouped`, {
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
    console.error("Certificates grouped proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
