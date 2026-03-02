import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ id: string }> | { id: string } }
) {
  try {
    const params = await Promise.resolve(context.params);
    const { id } = params;
    const auth = request.headers.get("authorization");
    const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
    const res = await fetch(
      `${API_URL}/api/v1/documents/${encodeURIComponent(id)}/extract-ocr`,
      { method: "GET", headers }
    );
    const data = await res.json().catch(() => ({}));
    if (res.status === 404) {
      return NextResponse.json({ detail: "Document not found" }, { status: 404 });
    }
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Extract OCR proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
