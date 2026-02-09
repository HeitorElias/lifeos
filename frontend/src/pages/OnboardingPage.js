import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Zap, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import API from '@/lib/api';

const restrictions = ['Vegetariano', 'Vegano', 'Sem glúten', 'Sem lactose', 'Low carb', 'Kosher', 'Halal'];

export default function OnboardingPage() {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ age: '', weight: '', height: '', gender: 'male', activity_level: 'moderate', goal: 'maintain', restrictions: [] });
  const [loading, setLoading] = useState(false);
  const { updateUser } = useAuth();
  const navigate = useNavigate();

  const toggleRestriction = (r) => {
    setForm(prev => ({
      ...prev,
      restrictions: prev.restrictions.includes(r) ? prev.restrictions.filter(x => x !== r) : [...prev.restrictions, r]
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const payload = { ...form, age: parseInt(form.age), weight: parseFloat(form.weight), height: parseFloat(form.height) };
      const res = await API.post('/user/onboarding', payload);
      updateUser({ onboarding_complete: true, profile: res.data.profile });
      toast.success(`Meta calórica: ${res.data.calorie_target} kcal/dia`);
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro no onboarding');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-4">
      <div className="w-full max-w-lg animate-fade-in">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-500 mb-4">
            <Zap className="w-7 h-7 text-white" />
          </div>
          <h1 data-testid="onboarding-title" className="text-3xl font-extrabold text-white tracking-tight" style={{ fontFamily: 'Plus Jakarta Sans' }}>
            Seu Perfil
          </h1>
          <p className="text-zinc-500 mt-2 text-sm">Preencha para personalizar suas metas nutricionais</p>
        </div>

        <div className="glass-card rounded-2xl p-8">
          {/* Progress */}
          <div className="flex gap-2 mb-8">
            {[1, 2, 3].map(s => (
              <div key={s} className={`h-1 flex-1 rounded-full transition-all ${s <= step ? 'bg-blue-500' : 'bg-white/10'}`} />
            ))}
          </div>

          {step === 1 && (
            <div className="space-y-5 animate-fade-in">
              <h3 className="text-lg font-semibold text-white">Dados Básicos</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-sm">Idade</Label>
                  <Input data-testid="onboarding-age" type="number" value={form.age} onChange={e => setForm({...form, age: e.target.value})} placeholder="30" className="bg-white/5 border-white/10 text-white h-11" />
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-sm">Gênero</Label>
                  <Select value={form.gender} onValueChange={v => setForm({...form, gender: v})}>
                    <SelectTrigger data-testid="onboarding-gender" className="bg-white/5 border-white/10 text-white h-11"><SelectValue /></SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-700">
                      <SelectItem value="male">Masculino</SelectItem>
                      <SelectItem value="female">Feminino</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-sm">Peso (kg)</Label>
                  <Input data-testid="onboarding-weight" type="number" step="0.1" value={form.weight} onChange={e => setForm({...form, weight: e.target.value})} placeholder="70" className="bg-white/5 border-white/10 text-white h-11" />
                </div>
                <div className="space-y-2">
                  <Label className="text-zinc-400 text-sm">Altura (cm)</Label>
                  <Input data-testid="onboarding-height" type="number" value={form.height} onChange={e => setForm({...form, height: e.target.value})} placeholder="175" className="bg-white/5 border-white/10 text-white h-11" />
                </div>
              </div>
              <Button data-testid="onboarding-next-1" onClick={() => setStep(2)} className="w-full h-11 bg-blue-500 hover:bg-blue-600 text-white mt-4">
                Próximo <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5 animate-fade-in">
              <h3 className="text-lg font-semibold text-white">Seu Estilo de Vida</h3>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Nível de Atividade</Label>
                <Select value={form.activity_level} onValueChange={v => setForm({...form, activity_level: v})}>
                  <SelectTrigger data-testid="onboarding-activity" className="bg-white/5 border-white/10 text-white h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-700">
                    <SelectItem value="sedentary">Sedentário</SelectItem>
                    <SelectItem value="light">Levemente ativo</SelectItem>
                    <SelectItem value="moderate">Moderado</SelectItem>
                    <SelectItem value="active">Ativo</SelectItem>
                    <SelectItem value="very_active">Muito ativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Objetivo</Label>
                <Select value={form.goal} onValueChange={v => setForm({...form, goal: v})}>
                  <SelectTrigger data-testid="onboarding-goal" className="bg-white/5 border-white/10 text-white h-11"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-700">
                    <SelectItem value="lose_weight">Perder peso</SelectItem>
                    <SelectItem value="lose_weight_fast">Perder peso rápido</SelectItem>
                    <SelectItem value="maintain">Manter peso</SelectItem>
                    <SelectItem value="gain_muscle">Ganhar músculo</SelectItem>
                    <SelectItem value="gain_weight">Ganhar peso</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)} className="flex-1 h-11 border-white/10 text-zinc-300">Voltar</Button>
                <Button data-testid="onboarding-next-2" onClick={() => setStep(3)} className="flex-1 h-11 bg-blue-500 hover:bg-blue-600 text-white">
                  Próximo <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-5 animate-fade-in">
              <h3 className="text-lg font-semibold text-white">Restrições Alimentares</h3>
              <p className="text-zinc-500 text-sm">Selecione se houver (opcional)</p>
              <div className="flex flex-wrap gap-2">
                {restrictions.map(r => (
                  <Badge
                    key={r}
                    data-testid={`restriction-${r}`}
                    variant={form.restrictions.includes(r) ? 'default' : 'outline'}
                    className={`cursor-pointer text-sm py-1.5 px-3 transition-all ${
                      form.restrictions.includes(r)
                        ? 'bg-blue-500 text-white border-blue-500'
                        : 'border-white/20 text-zinc-400 hover:border-white/40'
                    }`}
                    onClick={() => toggleRestriction(r)}
                  >
                    {r}
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2 mt-4">
                <Button variant="outline" onClick={() => setStep(2)} className="flex-1 h-11 border-white/10 text-zinc-300">Voltar</Button>
                <Button data-testid="onboarding-submit" onClick={handleSubmit} disabled={loading} className="flex-1 h-11 bg-blue-500 hover:bg-blue-600 text-white">
                  {loading ? 'Salvando...' : 'Começar!'}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
