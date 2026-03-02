import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const auth = request.headers.get("authorization");
    const res = await fetch(`${API_URL}/api/v1/organization/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(auth && { Authorization: auth }) },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    console.error("Organization create proxy error:", err);
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  }
}
