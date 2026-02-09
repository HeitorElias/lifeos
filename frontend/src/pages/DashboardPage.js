import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Apple, Calendar, Wallet, TrendingUp, Flame, Target, ArrowRight } from 'lucide-react';
import API from '@/lib/api';

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [nutritionData, setNutritionData] = useState(null);
  const [financeData, setFinanceData] = useState(null);
  const [events, setEvents] = useState([]);
  const [quotas, setQuotas] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [nRes, fRes, eRes, qRes] = await Promise.all([
          API.get('/nutrition/dashboard?period=day').catch(() => null),
          API.get('/finance/dashboard').catch(() => null),
          API.get('/agenda/events?period=day').catch(() => null),
          API.get('/user/quota').catch(() => null),
        ]);
        if (nRes) setNutritionData(nRes.data);
        if (fRes) setFinanceData(fRes.data);
        if (eRes) setEvents(eRes.data.events || []);
        if (qRes) setQuotas(qRes.data);
      } catch (e) { console.error(e); }
    };
    load();
  }, []);

  const calTarget = nutritionData?.calorie_target || 2000;
  const calToday = nutritionData?.today?.calories || 0;
  const calPercent = Math.min(100, Math.round((calToday / calTarget) * 100));

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Bom dia';
    if (h < 18) return 'Boa tarde';
    return 'Boa noite';
  };

  return (
    <Layout>
      <div data-testid="dashboard-page" className="space-y-8 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight" style={{ fontFamily: 'Plus Jakarta Sans' }}>
              {greeting()}, {user?.name?.split(' ')[0]}
            </h1>
            <p className="text-zinc-500 mt-1 text-sm">
              Aqui está seu resumo do dia — <span className="text-blue-400">{quotas?.plan || 'Free'}</span>
            </p>
          </div>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
          {/* Nutrition Hero Card */}
          <Card
            data-testid="dashboard-nutrition-card"
            className="col-span-12 md:col-span-8 glass-card border-0 glow-nutrition cursor-pointer hover:-translate-y-1 transition-all duration-300"
            onClick={() => navigate('/nutrition')}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-lime-500/20 flex items-center justify-center">
                    <Apple className="w-5 h-5 text-lime-400" />
                  </div>
                  <CardTitle className="text-white text-lg">Nutrição Hoje</CardTitle>
                </div>
                <ArrowRight className="w-5 h-5 text-zinc-500" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Flame className="w-4 h-4 text-orange-400" />
                    <span className="text-zinc-400 text-xs uppercase tracking-wide">Calorias</span>
                  </div>
                  <p className="text-3xl font-bold text-white">{Math.round(calToday)}</p>
                  <p className="text-zinc-500 text-xs mt-1">de {calTarget} kcal</p>
                  <Progress value={calPercent} className="h-1.5 mt-2 bg-white/10" />
                </div>
                <div>
                  <span className="text-zinc-400 text-xs uppercase tracking-wide">Proteínas</span>
                  <p className="text-2xl font-bold text-lime-400 mt-1">{Math.round(nutritionData?.today?.protein_g || 0)}g</p>
                </div>
                <div>
                  <span className="text-zinc-400 text-xs uppercase tracking-wide">Carboidratos</span>
                  <p className="text-2xl font-bold text-amber-400 mt-1">{Math.round(nutritionData?.today?.carbs_g || 0)}g</p>
                </div>
                <div>
                  <span className="text-zinc-400 text-xs uppercase tracking-wide">Gorduras</span>
                  <p className="text-2xl font-bold text-red-400 mt-1">{Math.round(nutritionData?.today?.fat_g || 0)}g</p>
                </div>
              </div>
              {nutritionData?.streak > 0 && (
                <div className="mt-4 flex items-center gap-2 text-sm text-lime-400">
                  <Target className="w-4 h-4" />
                  <span>{nutritionData.streak} dias dentro da meta!</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Agenda */}
          <Card
            data-testid="dashboard-agenda-card"
            className="col-span-12 md:col-span-4 glass-card border-0 glow-agenda cursor-pointer hover:-translate-y-1 transition-all duration-300"
            onClick={() => navigate('/agenda')}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-violet-400" />
                  </div>
                  <CardTitle className="text-white text-lg">Agenda</CardTitle>
                </div>
                <ArrowRight className="w-5 h-5 text-zinc-500" />
              </div>
            </CardHeader>
            <CardContent>
              {events.length > 0 ? (
                <div className="space-y-3">
                  {events.slice(0, 4).map(ev => (
                    <div key={ev.id} className="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                      <div className="w-1 h-8 rounded-full bg-violet-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{ev.title}</p>
                        <p className="text-xs text-zinc-500">{ev.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-zinc-500 text-sm">Nenhum compromisso hoje</p>
              )}
            </CardContent>
          </Card>

          {/* Finance Card */}
          <Card
            data-testid="dashboard-finance-card"
            className="col-span-12 md:col-span-6 glass-card border-0 glow-finance cursor-pointer hover:-translate-y-1 transition-all duration-300"
            onClick={() => navigate('/finance')}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-sky-500/20 flex items-center justify-center">
                    <Wallet className="w-5 h-5 text-sky-400" />
                  </div>
                  <CardTitle className="text-white text-lg">Finanças</CardTitle>
                </div>
                <ArrowRight className="w-5 h-5 text-zinc-500" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-zinc-400 text-xs uppercase tracking-wide">Gastos do Mês</span>
                  <p className="text-2xl font-bold text-white mt-1">
                    R$ {(financeData?.total_expenses || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <div>
                  <span className="text-zinc-400 text-xs uppercase tracking-wide">Contas Pendentes</span>
                  <p className="text-2xl font-bold text-amber-400 mt-1">
                    R$ {(financeData?.total_pending_bills || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
              {financeData?.difference !== undefined && financeData?.difference !== 0 && (
                <div className={`mt-3 flex items-center gap-1 text-sm ${financeData.difference > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  <TrendingUp className="w-4 h-4" />
                  <span>{financeData.difference > 0 ? '+' : ''}{financeData.difference.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} vs mês anterior</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quota Card */}
          <Card
            data-testid="dashboard-quota-card"
            className="col-span-12 md:col-span-6 glass-card border-0 cursor-pointer hover:-translate-y-1 transition-all duration-300"
            onClick={() => navigate('/settings')}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Target className="w-5 h-5 text-blue-400" />
                </div>
                <CardTitle className="text-white text-lg">Uso do Plano</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {quotas?.quotas && (
                <div className="space-y-3">
                  {Object.entries(quotas.quotas).slice(0, 4).map(([key, q]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-zinc-400 text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="text-white text-sm font-medium">
                        {q.unlimited ? 'Ilimitado' : `${q.used}/${q.limit}`}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
