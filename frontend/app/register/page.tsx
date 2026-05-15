'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AuthForm from '@/components/AuthForm'
import { api } from '@/lib/api'

export default function RegisterPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRegister = async (email: string, password: string) => {
    setLoading(true)
    setError('')
    try {
      await api.post('/auth/register', { email, password })
      router.push('/login?registered=1')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr.response?.data?.detail || '註冊失敗，請換一個 Email 或密碼（至少6位）')
    } finally {
      setLoading(false)
    }
  }

  return <AuthForm mode="register" onSubmit={handleRegister} loading={loading} error={error} />
}
