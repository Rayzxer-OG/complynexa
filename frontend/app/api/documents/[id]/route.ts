import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ id: string }> | { id: string } }
) {
  try {
    const params = await Promise.resolve(context.params);
    const { id } = params;
    const auth = request.headers.get("authorization");
    const body = await request.text();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(auth && { Authorization: auth }),
    };
    const res = await fetch(`${API_URL}/api/v1/documents/${encodeURIComponent(id)}`, {
      method: "PATCH",
      headers,
      body: body || undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 404) {
      return NextResponse.json({ detail: "Document not found" }, { status: 404 });
    }
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Patch document proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string }> | { id: string } }
) {
  try {
    const params = await Promise.resolve(context.params);
    const { id } = params;
    const auth = request.headers.get("authorization");
    const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
    const res = await fetch(`${API_URL}/api/v1/documents/${id}`, {
      method: "DELETE",
      headers,
    });
    if (res.status === 404) {
      return NextResponse.json({ detail: "Document not found" }, { status: 404 });
    }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    }
    return new NextResponse(null, { status: 204 });
  } catch (err) {
    console.error("Delete document proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
