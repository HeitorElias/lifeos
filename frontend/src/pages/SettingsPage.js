import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Settings, User, Crown, Shield, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import API from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [quotas, setQuotas] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editForm, setEditForm] = useState({});

  useEffect(() => { loadProfile(); loadQuotas(); }, []);

  const loadProfile = async () => {
    try {
      const res = await API.get('/user/profile');
      setProfile(res.data);
      setEditForm({
        name: res.data.name || '',
        age: res.data.profile?.age || '',
        weight: res.data.profile?.weight || '',
        height: res.data.profile?.height || '',
        gender: res.data.profile?.gender || 'male',
        activity_level: res.data.profile?.activity_level || 'moderate',
        goal: res.data.profile?.goal || 'maintain',
      });
    } catch (e) { console.error(e); }
  };

  const loadQuotas = async () => {
    try { const r = await API.get('/user/quota'); setQuotas(r.data); } catch (e) { console.error(e); }
  };

  const saveProfile = async () => {
    setLoading(true);
    try {
      const payload = { ...editForm };
      if (payload.age) payload.age = parseInt(payload.age);
      if (payload.weight) payload.weight = parseFloat(payload.weight);
      if (payload.height) payload.height = parseFloat(payload.height);
      const res = await API.put('/user/profile', payload);
      setProfile(res.data);
      updateUser({ name: res.data.name });
      toast.success('Perfil atualizado!');
    } catch (e) { toast.error('Erro ao salvar'); } finally { setLoading(false); }
  };

  const simulateUpgrade = async (planId) => {
    try {
      await API.post('/user/simulate-upgrade', { plan_id: planId });
      toast.success(`Upgrade para ${planId} simulado!`);
      loadQuotas();
      loadProfile();
    } catch (e) { toast.error('Erro no upgrade'); }
  };

  const planColors = { free: 'text-zinc-400', pro: 'text-violet-400', premium: 'text-amber-400' };
  const planBg = { free: 'bg-zinc-500/20', pro: 'bg-violet-500/20', premium: 'bg-amber-500/20' };

  return (
    <Layout>
      <div data-testid="settings-page" className="space-y-6 animate-fade-in max-w-3xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-zinc-500/20 flex items-center justify-center">
            <Settings className="w-5 h-5 text-zinc-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Configurações</h1>
            <p className="text-zinc-500 text-sm">Gerencie seu perfil e plano</p>
          </div>
        </div>

        {/* Profile */}
        <Card className="glass-card border-0">
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="w-5 h-5 text-blue-400" />
              <CardTitle className="text-white text-base">Perfil</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2 col-span-2">
                <Label className="text-zinc-400 text-sm">Nome</Label>
                <Input data-testid="settings-name" value={editForm.name || ''} onChange={e => setEditForm({...editForm, name: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Idade</Label>
                <Input type="number" value={editForm.age || ''} onChange={e => setEditForm({...editForm, age: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Gênero</Label>
                <Select value={editForm.gender} onValueChange={v => setEditForm({...editForm, gender: v})}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-700">
                    <SelectItem value="male">Masculino</SelectItem>
                    <SelectItem value="female">Feminino</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Peso (kg)</Label>
                <Input type="number" step="0.1" value={editForm.weight || ''} onChange={e => setEditForm({...editForm, weight: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Altura (cm)</Label>
                <Input type="number" value={editForm.height || ''} onChange={e => setEditForm({...editForm, height: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Atividade</Label>
                <Select value={editForm.activity_level} onValueChange={v => setEditForm({...editForm, activity_level: v})}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-700">
                    <SelectItem value="sedentary">Sedentário</SelectItem>
                    <SelectItem value="light">Leve</SelectItem>
                    <SelectItem value="moderate">Moderado</SelectItem>
                    <SelectItem value="active">Ativo</SelectItem>
                    <SelectItem value="very_active">Muito ativo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-zinc-400 text-sm">Objetivo</Label>
                <Select value={editForm.goal} onValueChange={v => setEditForm({...editForm, goal: v})}>
                  <SelectTrigger className="bg-white/5 border-white/10 text-white h-10"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-zinc-700">
                    <SelectItem value="lose_weight">Perder peso</SelectItem>
                    <SelectItem value="maintain">Manter</SelectItem>
                    <SelectItem value="gain_muscle">Ganhar músculo</SelectItem>
                    <SelectItem value="gain_weight">Ganhar peso</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button data-testid="save-profile-btn" onClick={saveProfile} disabled={loading} className="bg-blue-500 hover:bg-blue-600 text-white gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Salvar Perfil
            </Button>
          </CardContent>
        </Card>

        {/* Plans */}
        <Card className="glass-card border-0">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-amber-400" />
              <CardTitle className="text-white text-base">Plano Atual</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge className={`${planBg[quotas?.plan_id || 'free']} ${planColors[quotas?.plan_id || 'free']} border-0 text-sm px-3 py-1`}>
                {quotas?.plan || 'Free'}
              </Badge>
              <span className="text-zinc-500 text-sm">Plano atual</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {[
                { id: 'free', name: 'Graze (Grátis)', price: 'Grátis' },
                { id: 'pro', name: 'Boost (Pro)', price: 'US$ 24/mês' },
                { id: 'premium', name: 'Thrive (Premium)', price: 'US$ 39/mês' },
              ].map(plan => (
                <div key={plan.id} className={`p-4 rounded-xl border ${quotas?.plan_id === plan.id ? 'border-blue-500/50 bg-blue-500/5' : 'border-white/10 bg-white/5'}`}>
                  <p className="text-white font-medium text-sm">{plan.name}</p>
                  <p className="text-zinc-500 text-xs mt-1">{plan.price}</p>
                  {quotas?.plan_id !== plan.id && (
                    <Button size="sm" variant="outline" onClick={() => simulateUpgrade(plan.id)} className="mt-3 w-full border-white/10 text-zinc-300 text-xs">
                      Simular Upgrade
                    </Button>
                  )}
                </div>
              ))}
            </div>

            <p className="text-zinc-600 text-xs flex items-center gap-1">
              <Shield className="w-3 h-3" /> Cobrança real desativada no MVP. Use "Simular Upgrade" para testar.
            </p>
          </CardContent>
        </Card>

        {/* Quotas */}
        {quotas?.quotas && (
          <Card className="glass-card border-0">
            <CardHeader>
              <CardTitle className="text-white text-base">Uso de Quotas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(quotas.quotas).map(([key, q]) => {
                  const percent = q.unlimited ? 0 : (q.limit > 0 ? Math.round((q.used / q.limit) * 100) : 0);
                  return (
                    <div key={key} className="space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-zinc-400 text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                        <span className="text-white text-sm font-medium">
                          {q.unlimited ? 'Ilimitado' : `${q.used} / ${q.limit}`}
                          {!q.unlimited && <span className="text-zinc-500 text-xs ml-1">({q.period})</span>}
                        </span>
                      </div>
                      {!q.unlimited && (
                        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full transition-all ${percent > 80 ? 'bg-red-400' : percent > 50 ? 'bg-amber-400' : 'bg-blue-400'}`} style={{ width: `${percent}%` }} />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
