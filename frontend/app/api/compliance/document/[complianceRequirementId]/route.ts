import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ complianceRequirementId: string }> }
) {
  const { complianceRequirementId } = await params;
  if (!complianceRequirementId) {
    return NextResponse.json({ detail: "complianceRequirementId required" }, { status: 400 });
  }
  const auth = _request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(
      `${API_URL}/api/v1/compliance/document/${encodeURIComponent(complianceRequirementId)}`,
      { cache: "no-store", headers }
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return NextResponse.json(data, { status: res.status });
    return NextResponse.json(data);
  } catch (err) {
    console.error("Compliance document proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
