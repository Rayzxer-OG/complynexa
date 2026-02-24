import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");
    const files = formData.getAll("files");
    const hasMultiple = files.length > 0 && files.every((f) => f instanceof Blob);
    const hasSingle = file && file instanceof Blob;

    const backendFormData = new FormData();
    if (hasMultiple) {
      for (const f of files) backendFormData.append("files", f as Blob);
    } else if (hasSingle) {
      backendFormData.append("file", file as Blob);
    } else {
      return NextResponse.json(
        { detail: "No file(s) provided. Use 'file' or 'files'." },
        { status: 400 }
      );
    }

    const auth = request.headers.get("authorization");
    const headers: HeadersInit = { ...(auth && { Authorization: auth }) };
    const res = await fetch(`${API_URL}/api/v1/upload-document`, {
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
    console.error("Upload document proxy error:", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
