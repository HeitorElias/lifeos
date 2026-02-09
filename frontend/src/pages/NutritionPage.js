import React, { useState, useEffect, useRef } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Apple, Camera, Type, Flame, TrendingUp, Utensils, Target, Loader2, Upload } from 'lucide-react';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import API from '@/lib/api';

const MACRO_COLORS = { protein: '#84cc16', carbs: '#f59e0b', fat: '#ef4444' };

export default function NutritionPage() {
  const [tab, setTab] = useState('dashboard');
  const [dashData, setDashData] = useState(null);
  const [meals, setMeals] = useState([]);
  const [textInput, setTextInput] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [period, setPeriod] = useState('week');
  const fileRef = useRef(null);

  useEffect(() => { loadDashboard(); loadMeals(); }, [period]);

  const loadDashboard = async () => {
    try {
      const res = await API.get(`/nutrition/dashboard?period=${period}`);
      setDashData(res.data);
    } catch (e) { console.error(e); }
  };

  const loadMeals = async () => {
    try {
      const res = await API.get('/nutrition/meals?limit=20');
      setMeals(res.data.meals || []);
    } catch (e) { console.error(e); }
  };

  const analyzeText = async () => {
    if (!textInput.trim()) return;
    setAnalyzing(true);
    try {
      const res = await API.post('/nutrition/analyze-text', { text: textInput });
      setLastResult(res.data);
      setTextInput('');
      toast.success('Refeição registrada!');
      loadDashboard();
      loadMeals();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro na análise');
    } finally { setAnalyzing(false); }
  };

  const handlePhoto = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalyzing(true);
    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64 = reader.result.split(',')[1];
        try {
          const res = await API.post('/nutrition/analyze-photo', { image_base64: base64 });
          setLastResult(res.data);
          toast.success('Foto analisada!');
          loadDashboard();
          loadMeals();
        } catch (err) {
          toast.error(err.response?.data?.detail || 'Erro na análise da foto');
        } finally { setAnalyzing(false); }
      };
      reader.readAsDataURL(file);
    } catch (err) {
      toast.error('Erro ao processar imagem');
      setAnalyzing(false);
    }
  };

  const calTarget = dashData?.calorie_target || 2000;
  const calToday = dashData?.today?.calories || 0;
  const calPercent = Math.min(100, Math.round((calToday / calTarget) * 100));

  const macroData = dashData?.today ? [
    { name: 'Proteínas', value: dashData.today.protein_g || 0 },
    { name: 'Carboidratos', value: dashData.today.carbs_g || 0 },
    { name: 'Gorduras', value: dashData.today.fat_g || 0 },
  ] : [];

  return (
    <Layout>
      <div data-testid="nutrition-page" className="space-y-6 animate-fade-in">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-lime-500/20 flex items-center justify-center">
            <Apple className="w-5 h-5 text-lime-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Nutrição</h1>
            <p className="text-zinc-500 text-sm">Acompanhe suas refeições e nutrientes</p>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="bg-white/5 border border-white/10">
            <TabsTrigger data-testid="nutrition-tab-dashboard" value="dashboard" className="data-[state=active]:bg-lime-500/20 data-[state=active]:text-lime-400">Dashboard</TabsTrigger>
            <TabsTrigger data-testid="nutrition-tab-register" value="register" className="data-[state=active]:bg-lime-500/20 data-[state=active]:text-lime-400">Registrar</TabsTrigger>
            <TabsTrigger data-testid="nutrition-tab-history" value="history" className="data-[state=active]:bg-lime-500/20 data-[state=active]:text-lime-400">Histórico</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-5 mt-5">
            {/* Period selector */}
            <div className="flex gap-2">
              {['day', 'week', 'month'].map(p => (
                <Button key={p} size="sm" variant={period === p ? 'default' : 'outline'}
                  onClick={() => setPeriod(p)}
                  className={period === p ? 'bg-lime-500/20 text-lime-400 border-lime-500/30' : 'border-white/10 text-zinc-400'}>
                  {p === 'day' ? 'Hoje' : p === 'week' ? 'Semana' : 'Mês'}
                </Button>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
              {/* Calories card */}
              <Card className="col-span-12 md:col-span-5 glass-card border-0">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <Flame className="w-8 h-8 text-orange-400 mx-auto mb-2" />
                    <p className="text-4xl font-bold text-white">{Math.round(calToday)}</p>
                    <p className="text-zinc-500 text-sm">de {calTarget} kcal</p>
                    <Progress value={calPercent} className="h-2 mt-4 bg-white/10" />
                    <p className="text-xs text-zinc-500 mt-2">{calPercent}% da meta diária</p>
                  </div>
                  {dashData?.streak > 0 && (
                    <div className="mt-4 text-center">
                      <Badge className="bg-lime-500/20 text-lime-400 border-lime-500/30">
                        <Target className="w-3 h-3 mr-1" /> {dashData.streak} dias na meta
                      </Badge>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Macros pie */}
              <Card className="col-span-12 md:col-span-7 glass-card border-0">
                <CardHeader><CardTitle className="text-white text-base">Macros Hoje</CardTitle></CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <div className="w-40 h-40">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={macroData} cx="50%" cy="50%" innerRadius={40} outerRadius={65} paddingAngle={4} dataKey="value">
                            {macroData.map((_, i) => (
                              <Cell key={i} fill={Object.values(MACRO_COLORS)[i]} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3 flex-1">
                      {macroData.map((m, i) => (
                        <div key={m.name} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: Object.values(MACRO_COLORS)[i] }} />
                            <span className="text-zinc-400 text-sm">{m.name}</span>
                          </div>
                          <span className="text-white font-medium text-sm">{Math.round(m.value)}g</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Weekly chart */}
              {dashData?.daily_stats?.length > 0 && (
                <Card className="col-span-12 glass-card border-0">
                  <CardHeader><CardTitle className="text-white text-base">Calorias por Dia</CardTitle></CardHeader>
                  <CardContent>
                    <div className="h-52">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={dashData.daily_stats}>
                          <XAxis dataKey="date" tickFormatter={d => d.slice(5)} stroke="#52525b" fontSize={12} />
                          <YAxis stroke="#52525b" fontSize={12} />
                          <ReTooltip contentStyle={{ background: '#1c1c1f', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#fff' }} />
                          <Bar dataKey="calories" fill="#84cc16" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Register Tab */}
          <TabsContent value="register" className="space-y-5 mt-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Text input */}
              <Card className="glass-card border-0">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Type className="w-5 h-5 text-lime-400" />
                    <CardTitle className="text-white text-base">Descrever Refeição</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input
                    data-testid="nutrition-text-input"
                    value={textInput}
                    onChange={e => setTextInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && analyzeText()}
                    placeholder="Ex: arroz, feijão, frango 150g, salada"
                    className="bg-white/5 border-white/10 text-white h-11"
                  />
                  <Button
                    data-testid="nutrition-text-submit"
                    onClick={analyzeText}
                    disabled={analyzing || !textInput.trim()}
                    className="w-full bg-lime-500 hover:bg-lime-600 text-black font-medium"
                  >
                    {analyzing ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analisando...</> : 'Registrar Refeição'}
                  </Button>
                </CardContent>
              </Card>

              {/* Photo input */}
              <Card className="glass-card border-0">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <Camera className="w-5 h-5 text-lime-400" />
                    <CardTitle className="text-white text-base">Foto do Prato</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <input ref={fileRef} type="file" accept="image/*" onChange={handlePhoto} className="hidden" />
                  <div
                    data-testid="nutrition-photo-upload"
                    onClick={() => fileRef.current?.click()}
                    className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center cursor-pointer hover:border-lime-500/30 transition-colors"
                  >
                    <Upload className="w-8 h-8 text-zinc-500 mx-auto mb-2" />
                    <p className="text-zinc-400 text-sm">Clique para enviar foto</p>
                    <p className="text-zinc-600 text-xs mt-1">JPG, PNG ou WEBP</p>
                  </div>
                  {analyzing && (
                    <div className="flex items-center justify-center gap-2 text-lime-400">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span className="text-sm">Analisando foto com IA...</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Last result */}
            {lastResult && (
              <Card data-testid="nutrition-result" className="glass-card border-0 glow-nutrition">
                <CardHeader>
                  <CardTitle className="text-white text-base flex items-center gap-2">
                    <Utensils className="w-5 h-5 text-lime-400" /> Resultado da Análise
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {lastResult.items?.map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${item.matched ? 'bg-lime-400' : 'bg-amber-400'}`} />
                          <div>
                            <p className="text-white text-sm">{item.food_name_matched || item.food_name}</p>
                            <p className="text-zinc-500 text-xs">{item.grams}g • {item.source || 'Não encontrado na tabela'}</p>
                          </div>
                        </div>
                        {item.nutrients && (
                          <span className="text-lime-400 text-sm font-medium">{Math.round(item.nutrients.calories)} kcal</span>
                        )}
                      </div>
                    ))}
                    <div className="pt-3 border-t border-white/10 flex items-center justify-between">
                      <span className="text-zinc-400 font-medium">Total</span>
                      <div className="flex gap-4 text-sm">
                        <span className="text-white font-bold">{Math.round(lastResult.total?.calories || 0)} kcal</span>
                        <span className="text-lime-400">P: {Math.round(lastResult.total?.protein_g || 0)}g</span>
                        <span className="text-amber-400">C: {Math.round(lastResult.total?.carbs_g || 0)}g</span>
                        <span className="text-red-400">G: {Math.round(lastResult.total?.fat_g || 0)}g</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" className="mt-5">
            <div className="space-y-3">
              {meals.length === 0 && (
                <p className="text-zinc-500 text-center py-12">Nenhuma refeição registrada ainda</p>
              )}
              {meals.map(meal => (
                <Card key={meal.id} className="glass-card border-0">
                  <CardContent className="py-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-lime-500/20 text-lime-400 border-0 text-xs">{meal.meal_type}</Badge>
                        <Badge variant="outline" className="border-white/10 text-zinc-400 text-xs">{meal.type === 'photo' ? 'Foto' : 'Texto'}</Badge>
                      </div>
                      <span className="text-zinc-500 text-xs">{new Date(meal.created_at).toLocaleString('pt-BR')}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2 flex-wrap">
                        {meal.items?.slice(0, 3).map((item, i) => (
                          <span key={i} className="text-zinc-300 text-sm">{item.food_name_matched || item.food_name}</span>
                        ))}
                        {meal.items?.length > 3 && <span className="text-zinc-500 text-sm">+{meal.items.length - 3}</span>}
                      </div>
                      <span className="text-white font-semibold text-sm">{Math.round(meal.total_nutrients?.calories || 0)} kcal</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
