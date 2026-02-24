import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  if (!id) {
    return NextResponse.json({ detail: "id required" }, { status: 400 });
  }
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(
      `${API_URL}/api/v1/documents/${encodeURIComponent(id)}/download-url`,
      { cache: "no-store", headers }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    console.error("Document download-url proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
