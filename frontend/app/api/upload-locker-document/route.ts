import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    if (!file || !(file instanceof Blob)) {
      return NextResponse.json(
        { detail: "A PDF file is required" },
        { status: 400 }
      );
    }
    const backendFormData = new FormData();
    backendFormData.append("file", file);
    const auth = request.headers.get("authorization");
    const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
    const res = await fetch(`${API_URL}/api/v1/upload-locker-document`, {
      method: "POST",
      body: backendFormData,
      headers,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Upload locker document proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
