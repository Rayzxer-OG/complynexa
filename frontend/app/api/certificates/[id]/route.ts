import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string }> | { id: string } }
) {
  try {
    const params = await Promise.resolve(context.params);
    const { id } = params;
    if (!id) {
      return NextResponse.json({ detail: "id required" }, { status: 400 });
    }
    const auth = request.headers.get("authorization");
    const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
    const res = await fetch(
      `${API_URL}/api/v1/certificates/${encodeURIComponent(id)}`,
      { method: "DELETE", headers }
    );
    if (res.status === 404) {
      return NextResponse.json({ detail: "Certificate not found" }, { status: 404 });
    }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    }
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    console.error("Delete certificate proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
