import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(req: NextRequest) {
  const accessToken = req.cookies.get('sb-access-token')?.value

  const protectedPaths = ['/dashboard', '/history']
  const isProtected = protectedPaths.some(p => req.nextUrl.pathname.startsWith(p))
  const isAuthPage = ['/login', '/register'].includes(req.nextUrl.pathname)

  if (isProtected && !accessToken) {
    return NextResponse.redirect(new URL('/login', req.url))
  }

  if (isAuthPage && accessToken) {
    return NextResponse.redirect(new URL('/dashboard', req.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/history/:path*', '/login', '/register'],
}
