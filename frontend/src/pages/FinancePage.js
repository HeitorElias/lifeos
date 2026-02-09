import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Wallet, Plus, TrendingDown, TrendingUp, Receipt, CreditCard, Loader2, Check, Lightbulb } from 'lucide-react';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import API from '@/lib/api';

const CATEGORIES = ['Alimentação', 'Transporte', 'Moradia', 'Saúde', 'Educação', 'Lazer', 'Assinaturas', 'Roupas', 'Outros'];
const CAT_COLORS = ['#0ea5e9', '#8b5cf6', '#f59e0b', '#22c55e', '#ef4444', '#ec4899', '#14b8a6', '#f97316', '#6b7280'];

export default function FinancePage() {
  const [tab, setTab] = useState('dashboard');
  const [dashData, setDashData] = useState(null);
  const [bills, setBills] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [showBillForm, setShowBillForm] = useState(false);
  const [showExpenseForm, setShowExpenseForm] = useState(false);
  const [billForm, setBillForm] = useState({ name: '', amount: '', due_date: '', category: 'Outros', recurrence: 'once' });
  const [expenseForm, setExpenseForm] = useState({ amount: '', date: new Date().toISOString().slice(0, 10), category: 'Outros', description: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadAll(); }, []);

  const loadAll = () => { loadDashboard(); loadBills(); loadExpenses(); };

  const loadDashboard = async () => {
    try { const r = await API.get('/finance/dashboard'); setDashData(r.data); } catch (e) { console.error(e); }
  };

  const loadBills = async () => {
    try { const r = await API.get('/finance/bills'); setBills(r.data.bills || []); } catch (e) { console.error(e); }
  };

  const loadExpenses = async () => {
    try { const r = await API.get('/finance/expenses'); setExpenses(r.data.expenses || []); } catch (e) { console.error(e); }
  };

  const createBill = async () => {
    if (!billForm.name || !billForm.amount || !billForm.due_date) { toast.error('Preencha todos os campos'); return; }
    setLoading(true);
    try {
      await API.post('/finance/bills', { ...billForm, amount: parseFloat(billForm.amount) });
      toast.success('Conta criada!');
      setShowBillForm(false);
      setBillForm({ name: '', amount: '', due_date: '', category: 'Outros', recurrence: 'once' });
      loadAll();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); } finally { setLoading(false); }
  };

  const createExpense = async () => {
    if (!expenseForm.amount || !expenseForm.description) { toast.error('Preencha valor e descrição'); return; }
    setLoading(true);
    try {
      await API.post('/finance/expenses', { ...expenseForm, amount: parseFloat(expenseForm.amount) });
      toast.success('Gasto registrado!');
      setShowExpenseForm(false);
      setExpenseForm({ amount: '', date: new Date().toISOString().slice(0, 10), category: 'Outros', description: '' });
      loadAll();
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); } finally { setLoading(false); }
  };

  const payBill = async (id) => {
    try {
      await API.put(`/finance/bills/${id}`, { status: 'paid' });
      toast.success('Conta marcada como paga!');
      loadAll();
    } catch (e) { toast.error('Erro ao pagar'); }
  };

  const analyzeFinances = async () => {
    setAnalyzing(true);
    try {
      const r = await API.post('/finance/analyze');
      setAnalysis(r.data);
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro na análise'); } finally { setAnalyzing(false); }
  };

  const fmt = (v) => (v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  return (
    <Layout>
      <div data-testid="finance-page" className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/20 flex items-center justify-center">
              <Wallet className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Finanças</h1>
              <p className="text-zinc-500 text-sm">Controle suas contas e gastos</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Dialog open={showExpenseForm} onOpenChange={setShowExpenseForm}>
              <DialogTrigger asChild>
                <Button data-testid="add-expense-btn" size="sm" className="bg-sky-500 hover:bg-sky-600 text-white gap-1">
                  <Plus className="w-4 h-4" /> Gasto
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#121214] border-white/10 text-white max-w-md">
                <DialogHeader><DialogTitle className="text-white">Registrar Gasto</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="text-zinc-400 text-sm">Valor (R$)</Label>
                      <Input data-testid="expense-amount" type="number" step="0.01" value={expenseForm.amount} onChange={e => setExpenseForm({...expenseForm, amount: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-400 text-sm">Data</Label>
                      <Input type="date" value={expenseForm.date} onChange={e => setExpenseForm({...expenseForm, date: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-sm">Categoria</Label>
                    <Select value={expenseForm.category} onValueChange={v => setExpenseForm({...expenseForm, category: v})}>
                      <SelectTrigger className="bg-white/5 border-white/10 text-white h-10"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-zinc-700">
                        {CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-sm">Descrição</Label>
                    <Input data-testid="expense-desc" value={expenseForm.description} onChange={e => setExpenseForm({...expenseForm, description: e.target.value})} placeholder="Ex: Supermercado" className="bg-white/5 border-white/10 text-white h-10" />
                  </div>
                  <Button data-testid="expense-submit" onClick={createExpense} disabled={loading} className="w-full bg-sky-500 hover:bg-sky-600 text-white">
                    {loading ? 'Salvando...' : 'Registrar Gasto'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={showBillForm} onOpenChange={setShowBillForm}>
              <DialogTrigger asChild>
                <Button data-testid="add-bill-btn" size="sm" variant="outline" className="border-white/10 text-zinc-300 gap-1">
                  <Plus className="w-4 h-4" /> Conta
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-[#121214] border-white/10 text-white max-w-md">
                <DialogHeader><DialogTitle className="text-white">Nova Conta a Pagar</DialogTitle></DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-zinc-400 text-sm">Nome</Label>
                    <Input data-testid="bill-name" value={billForm.name} onChange={e => setBillForm({...billForm, name: e.target.value})} placeholder="Ex: Aluguel" className="bg-white/5 border-white/10 text-white h-10" />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="text-zinc-400 text-sm">Valor (R$)</Label>
                      <Input data-testid="bill-amount" type="number" step="0.01" value={billForm.amount} onChange={e => setBillForm({...billForm, amount: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-400 text-sm">Vencimento</Label>
                      <Input data-testid="bill-due" type="date" value={billForm.due_date} onChange={e => setBillForm({...billForm, due_date: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label className="text-zinc-400 text-sm">Categoria</Label>
                      <Select value={billForm.category} onValueChange={v => setBillForm({...billForm, category: v})}>
                        <SelectTrigger className="bg-white/5 border-white/10 text-white h-10"><SelectValue /></SelectTrigger>
                        <SelectContent className="bg-zinc-900 border-zinc-700">
                          {CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-zinc-400 text-sm">Recorrência</Label>
                      <Select value={billForm.recurrence} onValueChange={v => setBillForm({...billForm, recurrence: v})}>
                        <SelectTrigger className="bg-white/5 border-white/10 text-white h-10"><SelectValue /></SelectTrigger>
                        <SelectContent className="bg-zinc-900 border-zinc-700">
                          <SelectItem value="once">Uma vez</SelectItem>
                          <SelectItem value="monthly">Mensal</SelectItem>
                          <SelectItem value="weekly">Semanal</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <Button data-testid="bill-submit" onClick={createBill} disabled={loading} className="w-full bg-sky-500 hover:bg-sky-600 text-white">
                    {loading ? 'Salvando...' : 'Criar Conta'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="bg-white/5 border border-white/10">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-sky-500/20 data-[state=active]:text-sky-400">Dashboard</TabsTrigger>
            <TabsTrigger value="bills" className="data-[state=active]:bg-sky-500/20 data-[state=active]:text-sky-400">Contas</TabsTrigger>
            <TabsTrigger value="expenses" className="data-[state=active]:bg-sky-500/20 data-[state=active]:text-sky-400">Gastos</TabsTrigger>
            <TabsTrigger value="analysis" className="data-[state=active]:bg-sky-500/20 data-[state=active]:text-sky-400">Análise IA</TabsTrigger>
          </TabsList>

          {/* Dashboard */}
          <TabsContent value="dashboard" className="space-y-5 mt-5">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <Card className="glass-card border-0">
                <CardContent className="pt-6 text-center">
                  <Receipt className="w-6 h-6 text-sky-400 mx-auto mb-2" />
                  <p className="text-zinc-400 text-xs uppercase tracking-wide">Gastos do Mês</p>
                  <p className="text-3xl font-bold text-white mt-1">{fmt(dashData?.total_expenses)}</p>
                </CardContent>
              </Card>
              <Card className="glass-card border-0">
                <CardContent className="pt-6 text-center">
                  <CreditCard className="w-6 h-6 text-amber-400 mx-auto mb-2" />
                  <p className="text-zinc-400 text-xs uppercase tracking-wide">Contas Pendentes</p>
                  <p className="text-3xl font-bold text-amber-400 mt-1">{fmt(dashData?.total_pending_bills)}</p>
                </CardContent>
              </Card>
              <Card className="glass-card border-0">
                <CardContent className="pt-6 text-center">
                  {(dashData?.difference || 0) > 0 ? <TrendingUp className="w-6 h-6 text-red-400 mx-auto mb-2" /> : <TrendingDown className="w-6 h-6 text-green-400 mx-auto mb-2" />}
                  <p className="text-zinc-400 text-xs uppercase tracking-wide">vs Mês Anterior</p>
                  <p className={`text-3xl font-bold mt-1 ${(dashData?.difference || 0) > 0 ? 'text-red-400' : 'text-green-400'}`}>
                    {fmt(dashData?.difference)}
                  </p>
                </CardContent>
              </Card>
            </div>

            {dashData?.categories?.length > 0 && (
              <Card className="glass-card border-0">
                <CardHeader><CardTitle className="text-white text-base">Gastos por Categoria</CardTitle></CardHeader>
                <CardContent>
                  <div className="flex items-center gap-6">
                    <div className="w-48 h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={dashData.categories} cx="50%" cy="50%" innerRadius={45} outerRadius={70} paddingAngle={3} dataKey="amount" nameKey="name">
                            {dashData.categories.map((_, i) => <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />)}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-2 flex-1">
                      {dashData.categories.map((cat, i) => (
                        <div key={cat.name} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: CAT_COLORS[i % CAT_COLORS.length] }} />
                            <span className="text-zinc-400 text-sm">{cat.name}</span>
                          </div>
                          <span className="text-white font-medium text-sm">{fmt(cat.amount)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Bills */}
          <TabsContent value="bills" className="mt-5 space-y-3">
            {bills.length === 0 && <p className="text-zinc-500 text-center py-12">Nenhuma conta cadastrada</p>}
            {bills.map(bill => (
              <Card key={bill.id} className="glass-card border-0">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-white font-medium">{bill.name}</h4>
                        <Badge className={bill.status === 'paid' ? 'bg-green-500/20 text-green-400 border-0' : 'bg-amber-500/20 text-amber-400 border-0'}>
                          {bill.status === 'paid' ? 'Pago' : 'Pendente'}
                        </Badge>
                        {bill.recurrence !== 'once' && (
                          <Badge variant="outline" className="border-white/10 text-zinc-400 text-xs">{bill.recurrence === 'monthly' ? 'Mensal' : 'Semanal'}</Badge>
                        )}
                      </div>
                      <p className="text-zinc-500 text-sm mt-1">Vencimento: {new Date(bill.due_date + 'T12:00:00').toLocaleDateString('pt-BR')}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-white font-bold">{fmt(bill.amount)}</span>
                      {bill.status === 'pending' && (
                        <Button data-testid={`pay-bill-${bill.id}`} size="sm" onClick={() => payBill(bill.id)} className="bg-green-500/20 text-green-400 hover:bg-green-500/30 gap-1">
                          <Check className="w-3 h-3" /> Pagar
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* Expenses */}
          <TabsContent value="expenses" className="mt-5 space-y-3">
            {expenses.length === 0 && <p className="text-zinc-500 text-center py-12">Nenhum gasto registrado</p>}
            {expenses.map(exp => (
              <Card key={exp.id} className="glass-card border-0">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-white font-medium">{exp.description}</h4>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="border-white/10 text-zinc-400 text-xs">{exp.category}</Badge>
                        <span className="text-zinc-500 text-xs">{new Date(exp.date + 'T12:00:00').toLocaleDateString('pt-BR')}</span>
                      </div>
                    </div>
                    <span className="text-red-400 font-bold">{fmt(exp.amount)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </TabsContent>

          {/* AI Analysis */}
          <TabsContent value="analysis" className="mt-5 space-y-5">
            <Card className="glass-card border-0">
              <CardContent className="pt-6 text-center">
                <Lightbulb className="w-8 h-8 text-sky-400 mx-auto mb-3" />
                <h3 className="text-white font-semibold mb-2">Análise com IA</h3>
                <p className="text-zinc-500 text-sm mb-4">A IA vai analisar seus gastos e sugerir onde economizar</p>
                <Button data-testid="finance-analyze-btn" onClick={analyzeFinances} disabled={analyzing} className="bg-sky-500 hover:bg-sky-600 text-white">
                  {analyzing ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analisando...</> : 'Analisar Meus Gastos'}
                </Button>
              </CardContent>
            </Card>

            {analysis && (
              <Card data-testid="finance-analysis-result" className="glass-card border-0 glow-finance">
                <CardContent className="pt-6 space-y-4">
                  {analysis.response_text && <p className="text-white text-sm">{analysis.response_text}</p>}
                  {analysis.analysis?.top_cuts?.length > 0 && (
                    <div>
                      <h4 className="text-sky-400 font-medium text-sm mb-2">Onde Cortar</h4>
                      <ul className="space-y-1">
                        {analysis.analysis.top_cuts.map((c, i) => (
                          <li key={i} className="text-zinc-300 text-sm flex items-start gap-2">
                            <span className="text-sky-400 mt-0.5">•</span>{c}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {analysis.analysis?.simple_actions?.length > 0 && (
                    <div>
                      <h4 className="text-green-400 font-medium text-sm mb-2">Ações Simples</h4>
                      <ul className="space-y-1">
                        {analysis.analysis.simple_actions.map((a, i) => (
                          <li key={i} className="text-zinc-300 text-sm flex items-start gap-2">
                            <span className="text-green-400 mt-0.5">•</span>{a}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
