import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const certificate_ids = body?.certificate_ids;
    if (!Array.isArray(certificate_ids)) {
      return NextResponse.json(
        { detail: "certificate_ids must be an array" },
        { status: 400 }
      );
    }
    const auth = request.headers.get("authorization");
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(auth && { Authorization: auth }),
    };
    const res = await fetch(`${API_URL}/api/v1/certificates/bulk-delete`, {
      method: "POST",
      headers,
      body: JSON.stringify({ certificate_ids }),
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
    console.error("Bulk delete certificates proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
