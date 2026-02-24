import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;
  if (!jobId) {
    return NextResponse.json({ detail: "job_id required" }, { status: 400 });
  }
  const auth = request.headers.get("authorization");
  const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
  try {
    const res = await fetch(
      `${API_URL}/api/v1/processing-status/${encodeURIComponent(jobId)}`,
      { cache: "no-store", headers }
    );
    const data = await res.json().catch(() => ({}));
    if (res.status === 404) {
      return NextResponse.json(data, { status: 404 });
    }
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Processing status proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
