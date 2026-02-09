import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Zap, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const user = await login(email, password);
      toast.success('Bem-vindo de volta!');
      navigate(user.onboarding_complete ? '/dashboard' : '/onboarding');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-500 mb-4">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1
            data-testid="login-title"
            className="text-3xl font-extrabold text-white tracking-tight"
            style={{ fontFamily: 'Plus Jakarta Sans' }}
          >
            Life OS
          </h1>
          <p className="text-zinc-500 mt-2 text-sm">Seu sistema operacional de vida</p>
        </div>

        {/* Form */}
        <div className="glass-card rounded-2xl p-8">
          <h2 className="text-xl font-semibold text-white mb-6" style={{ fontFamily: 'Plus Jakarta Sans' }}>
            Entrar
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-400 text-sm">Email</Label>
              <Input
                id="email"
                type="email"
                data-testid="login-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                className="bg-white/5 border-white/10 text-white placeholder:text-zinc-600 focus:border-blue-500 h-11"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-400 text-sm">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  data-testid="login-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="bg-white/5 border-white/10 text-white placeholder:text-zinc-600 focus:border-blue-500 h-11 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              data-testid="login-submit"
              disabled={loading}
              className="w-full h-11 bg-blue-500 hover:bg-blue-600 text-white font-medium shadow-[0_0_20px_rgba(59,130,246,0.25)] hover:shadow-[0_0_30px_rgba(59,130,246,0.4)] transition-all"
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </form>

          <p className="text-center text-zinc-500 text-sm mt-6">
            Não tem conta?{' '}
            <Link to="/register" data-testid="register-link" className="text-blue-400 hover:text-blue-300 font-medium">
              Criar conta
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
