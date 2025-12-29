// frontend/src/app/api/alert-radar/route.ts
import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  // Cambia la URL según tu backend real
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/alert-radar";
  const res = await fetch(backendUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return new Response(JSON.stringify(data), {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
