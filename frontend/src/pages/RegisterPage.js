import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Zap, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error('A senha deve ter pelo menos 6 caracteres');
      return;
    }
    setLoading(true);
    try {
      await register(name, email, password);
      toast.success('Conta criada com sucesso!');
      navigate('/onboarding');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao criar conta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-4">
      <div className="w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-500 mb-4">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1
            data-testid="register-title"
            className="text-3xl font-extrabold text-white tracking-tight"
            style={{ fontFamily: 'Plus Jakarta Sans' }}
          >
            Criar Conta
          </h1>
          <p className="text-zinc-500 mt-2 text-sm">Comece a organizar sua vida hoje</p>
        </div>

        <div className="glass-card rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-zinc-400 text-sm">Nome</Label>
              <Input
                id="name"
                data-testid="register-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Seu nome"
                className="bg-white/5 border-white/10 text-white placeholder:text-zinc-600 h-11"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-400 text-sm">Email</Label>
              <Input
                id="email"
                type="email"
                data-testid="register-email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                className="bg-white/5 border-white/10 text-white placeholder:text-zinc-600 h-11"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-zinc-400 text-sm">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPass ? 'text' : 'password'}
                  data-testid="register-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 6 caracteres"
                  className="bg-white/5 border-white/10 text-white placeholder:text-zinc-600 h-11 pr-10"
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
              data-testid="register-submit"
              disabled={loading}
              className="w-full h-11 bg-blue-500 hover:bg-blue-600 text-white font-medium shadow-[0_0_20px_rgba(59,130,246,0.25)] transition-all"
            >
              {loading ? 'Criando...' : 'Criar Conta Grátis'}
            </Button>
          </form>

          <p className="text-center text-zinc-500 text-sm mt-6">
            Já tem conta?{' '}
            <Link to="/login" data-testid="login-link" className="text-blue-400 hover:text-blue-300 font-medium">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
