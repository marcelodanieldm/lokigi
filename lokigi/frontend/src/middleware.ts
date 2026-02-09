// frontend/src/middleware.ts

import { NextRequest, NextResponse } from 'next/server';
import { getSubscriptionStatus } from './utils/getSubscriptionStatus';

export async function middleware(req: NextRequest) {
  const url = req.nextUrl.clone();
  // Solo proteger la ruta premium
  if (url.pathname.startsWith('/dashboard/premium')) {
    // Simulación: extraer userId de cookie/session (ajusta según tu auth)
    const userId = req.cookies.get('user_id')?.value || '';
    const status = await getSubscriptionStatus(userId);
    if (status !== 'active') {
      url.pathname = '/dashboard/payment-required';
      return NextResponse.redirect(url);
    }
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/premium/:path*'],
};
