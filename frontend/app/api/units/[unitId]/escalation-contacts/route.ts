import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getUnitUrl(unitId: string) {
  return `${API_URL}/api/v1/units/${encodeURIComponent(unitId)}/escalation-contacts`;
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ unitId: string }> }
) {
  const { unitId } = await params;
  const auth = _request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(getUnitUrl(unitId), { cache: "no-store", headers });
    if (res.status === 401) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    if (res.status === 404) return NextResponse.json({ detail: "Unit not found" }, { status: 404 });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json(data, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    console.error("Escalation contacts proxy error:", err);
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ unitId: string }> }
) {
  const { unitId } = await params;
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(auth && { Authorization: auth }),
  };
  try {
    const body = await request.text();
    const res = await fetch(getUnitUrl(unitId), {
      method: "PUT",
      headers,
      body: body || undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (res.status === 401) return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    if (res.status === 404) return NextResponse.json({ detail: "Unit not found" }, { status: 404 });
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    console.error("Escalation contacts PUT proxy error:", err);
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  }
}
