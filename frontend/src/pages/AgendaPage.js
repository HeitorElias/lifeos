import React, { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Calendar, Plus, Clock, MapPin, Trash2, Edit2, X } from 'lucide-react';
import { toast } from 'sonner';
import API from '@/lib/api';

export default function AgendaPage() {
  const [events, setEvents] = useState([]);
  const [period, setPeriod] = useState('week');
  const [showCreate, setShowCreate] = useState(false);
  const [editEvent, setEditEvent] = useState(null);
  const [form, setForm] = useState({ title: '', date: '', time: '', end_time: '', location: '', notes: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => { loadEvents(); }, [period]);

  const loadEvents = async () => {
    try {
      const res = await API.get(`/agenda/events?period=${period}`);
      setEvents(res.data.events || []);
    } catch (e) { console.error(e); }
  };

  const createEvent = async () => {
    if (!form.title || !form.date || !form.time) {
      toast.error('Preencha título, data e hora');
      return;
    }
    setLoading(true);
    try {
      await API.post('/agenda/events', form);
      toast.success('Compromisso criado!');
      setShowCreate(false);
      resetForm();
      loadEvents();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao criar');
    } finally { setLoading(false); }
  };

  const updateEvent = async () => {
    if (!editEvent) return;
    setLoading(true);
    try {
      await API.put(`/agenda/events/${editEvent.id}`, form);
      toast.success('Compromisso atualizado!');
      setEditEvent(null);
      resetForm();
      loadEvents();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao atualizar');
    } finally { setLoading(false); }
  };

  const cancelEvent = async (id) => {
    try {
      await API.delete(`/agenda/events/${id}`);
      toast.success('Compromisso cancelado');
      loadEvents();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao cancelar');
    }
  };

  const resetForm = () => setForm({ title: '', date: '', time: '', end_time: '', location: '', notes: '' });

  const startEdit = (ev) => {
    setForm({ title: ev.title, date: ev.date, time: ev.time, end_time: ev.end_time || '', location: ev.location || '', notes: ev.notes || '' });
    setEditEvent(ev);
  };

  // Group events by date
  const grouped = events.reduce((acc, ev) => {
    const d = ev.date;
    if (!acc[d]) acc[d] = [];
    acc[d].push(ev);
    return acc;
  }, {});

  const formatDate = (d) => {
    const today = new Date().toISOString().slice(0, 10);
    const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10);
    if (d === today) return 'Hoje';
    if (d === tomorrow) return 'Amanhã';
    return new Date(d + 'T12:00:00').toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
  };

  const EventForm = ({ onSubmit, submitLabel }) => (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label className="text-zinc-400 text-sm">Título</Label>
        <Input data-testid="event-title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="Ex: Reunião com equipe" className="bg-white/5 border-white/10 text-white h-10" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label className="text-zinc-400 text-sm">Data</Label>
          <Input data-testid="event-date" type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
        </div>
        <div className="space-y-2">
          <Label className="text-zinc-400 text-sm">Hora</Label>
          <Input data-testid="event-time" type="time" value={form.time} onChange={e => setForm({...form, time: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label className="text-zinc-400 text-sm">Término</Label>
          <Input type="time" value={form.end_time} onChange={e => setForm({...form, end_time: e.target.value})} className="bg-white/5 border-white/10 text-white h-10" />
        </div>
        <div className="space-y-2">
          <Label className="text-zinc-400 text-sm">Local</Label>
          <Input value={form.location} onChange={e => setForm({...form, location: e.target.value})} placeholder="Opcional" className="bg-white/5 border-white/10 text-white h-10" />
        </div>
      </div>
      <div className="space-y-2">
        <Label className="text-zinc-400 text-sm">Notas</Label>
        <Input value={form.notes} onChange={e => setForm({...form, notes: e.target.value})} placeholder="Notas opcionais" className="bg-white/5 border-white/10 text-white h-10" />
      </div>
      <div className="flex gap-2 pt-2">
        <Button onClick={onSubmit} disabled={loading} className="flex-1 bg-violet-500 hover:bg-violet-600 text-white">
          {loading ? 'Salvando...' : submitLabel}
        </Button>
      </div>
    </div>
  );

  return (
    <Layout>
      <div data-testid="agenda-page" className="space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Agenda</h1>
              <p className="text-zinc-500 text-sm">Gerencie seus compromissos</p>
            </div>
          </div>
          <Dialog open={showCreate} onOpenChange={v => { setShowCreate(v); if (!v) resetForm(); }}>
            <DialogTrigger asChild>
              <Button data-testid="create-event-btn" className="bg-violet-500 hover:bg-violet-600 text-white gap-2">
                <Plus className="w-4 h-4" /> Novo
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-[#121214] border-white/10 text-white max-w-md">
              <DialogHeader>
                <DialogTitle className="text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Novo Compromisso</DialogTitle>
              </DialogHeader>
              <EventForm onSubmit={createEvent} submitLabel="Criar Compromisso" />
            </DialogContent>
          </Dialog>
        </div>

        {/* Period tabs */}
        <div className="flex gap-2">
          {['day', 'week', 'month'].map(p => (
            <Button key={p} size="sm" variant={period === p ? 'default' : 'outline'}
              onClick={() => setPeriod(p)}
              className={period === p ? 'bg-violet-500/20 text-violet-400 border-violet-500/30' : 'border-white/10 text-zinc-400'}>
              {p === 'day' ? 'Hoje' : p === 'week' ? 'Semana' : 'Mês'}
            </Button>
          ))}
        </div>

        {/* Events */}
        {Object.keys(grouped).length === 0 && (
          <div className="text-center py-16">
            <Calendar className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
            <p className="text-zinc-500">Nenhum compromisso encontrado</p>
          </div>
        )}

        {Object.entries(grouped).map(([date, evts]) => (
          <div key={date} className="space-y-3">
            <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wide">{formatDate(date)}</h3>
            {evts.map(ev => (
              <Card key={ev.id} data-testid={`event-${ev.id}`} className="glass-card border-0 hover:-translate-y-0.5 transition-all duration-200">
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex gap-3">
                      <div className="w-1 h-full min-h-[48px] rounded-full bg-violet-400 flex-shrink-0" />
                      <div>
                        <h4 className="text-white font-medium">{ev.title}</h4>
                        <div className="flex items-center gap-3 mt-1 text-zinc-500 text-sm">
                          <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{ev.time}{ev.end_time ? ` - ${ev.end_time}` : ''}</span>
                          {ev.location && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{ev.location}</span>}
                        </div>
                        {ev.notes && <p className="text-zinc-600 text-xs mt-1">{ev.notes}</p>}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button size="icon" variant="ghost" className="h-8 w-8 text-zinc-500 hover:text-violet-400"
                        onClick={() => startEdit(ev)}>
                        <Edit2 className="w-3.5 h-3.5" />
                      </Button>
                      <Button size="icon" variant="ghost" className="h-8 w-8 text-zinc-500 hover:text-red-400"
                        data-testid={`cancel-event-${ev.id}`}
                        onClick={() => cancelEvent(ev.id)}>
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ))}

        {/* Edit Dialog */}
        <Dialog open={!!editEvent} onOpenChange={v => { if (!v) { setEditEvent(null); resetForm(); } }}>
          <DialogContent className="bg-[#121214] border-white/10 text-white max-w-md">
            <DialogHeader>
              <DialogTitle className="text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Editar Compromisso</DialogTitle>
            </DialogHeader>
            <EventForm onSubmit={updateEvent} submitLabel="Salvar Alterações" />
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
