'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AuthForm from '@/components/AuthForm'
import { api } from '@/lib/api'

export default function LoginPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (email: string, password: string) => {
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user_email', data.email)
      localStorage.setItem('sheet_url', data.sheet_url || '')
      document.cookie = `sb-access-token=${data.access_token}; path=/; max-age=604800; SameSite=Lax`
      router.push('/dashboard')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || '登入失敗，請確認帳號密碼')
    } finally {
      setLoading(false)
    }
  }

  return <AuthForm mode="login" onSubmit={handleLogin} loading={loading} error={error} />
}
