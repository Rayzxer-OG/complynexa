import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const res = await fetch(`${API_URL}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const contentType = res.headers.get("content-type") ?? "";
    let data: Record<string, unknown> = {};
    if (contentType.includes("application/json")) {
      data = await res.json().catch(() => ({}));
    } else {
      const text = await res.text().catch(() => "");
      if (text) data = { detail: text };
    }
    if (!res.ok) {
      // Log backend error so we can see it in the Next.js terminal
      console.error("[register proxy] Backend %d:", res.status, data);
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error("Register proxy error (backend unreachable?):", err);
    return NextResponse.json(
      { detail: "Backend unreachable" },
      { status: 502 }
    );
  }
}
