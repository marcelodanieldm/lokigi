// API route: /api/worker/approve
// Simula la aprobación de una respuesta (puedes conectar a Supabase o backend real)
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  // Aquí podrías guardar la aprobación en la base de datos
  return NextResponse.json({ ok: true });
}
