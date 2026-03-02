import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(auth && { Authorization: auth }),
  };
  try {
    const body = await request.text();
    const res = await fetch(`${API_URL}/api/v1/compliance/compliance-attributes`, {
      method: "POST",
      headers,
      body: body || undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Compliance attributes proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
