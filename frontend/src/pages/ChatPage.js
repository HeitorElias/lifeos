import React, { useState, useEffect, useRef } from 'react';
import { Layout } from '@/components/layout/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageSquare, Send, Apple, Calendar, Wallet, Loader2, Bot, User } from 'lucide-react';
import API from '@/lib/api';

const MODULES = [
  { id: 'nutrition', label: 'Nutrição', icon: Apple, color: 'text-lime-400', bg: 'bg-lime-500/20', border: 'border-lime-500/30' },
  { id: 'agenda', label: 'Agenda', icon: Calendar, color: 'text-violet-400', bg: 'bg-violet-500/20', border: 'border-violet-500/30' },
  { id: 'finance', label: 'Finanças', icon: Wallet, color: 'text-sky-400', bg: 'bg-sky-500/20', border: 'border-sky-500/30' },
];

export default function ChatPage() {
  const [module, setModule] = useState('nutrition');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { loadHistory(); }, [module]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadHistory = async () => {
    try {
      const res = await API.get(`/chat/history?module=${module}&limit=30`);
      setMessages(res.data.messages || []);
    } catch (e) { console.error(e); }
  };

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput('');
    setSending(true);

    setMessages(prev => [...prev, { id: 'temp', role: 'user', content: text, module, created_at: new Date().toISOString() }]);

    try {
      const res = await API.post('/chat/message', { message: text, module });
      setMessages(prev => [
        ...prev.filter(m => m.id !== 'temp'),
        { id: `u-${Date.now()}`, role: 'user', content: text, module, created_at: new Date().toISOString() },
        { id: `a-${Date.now()}`, role: 'assistant', content: res.data.message, module, data: res.data.data, created_at: new Date().toISOString() },
      ]);
    } catch (e) {
      setMessages(prev => [
        ...prev.filter(m => m.id !== 'temp'),
        { id: `u-${Date.now()}`, role: 'user', content: text, module, created_at: new Date().toISOString() },
        { id: `e-${Date.now()}`, role: 'assistant', content: e.response?.data?.detail || 'Erro ao processar. Tente novamente.', module, created_at: new Date().toISOString() },
      ]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const currentMod = MODULES.find(m => m.id === module);

  const placeholders = {
    nutrition: 'Ex: "comi arroz, feijão e frango 150g"',
    agenda: 'Ex: "marca reunião amanhã às 14h"',
    finance: 'Ex: "gastei R$ 50 no supermercado"',
  };

  return (
    <Layout>
      <div data-testid="chat-page" className="h-[calc(100vh-48px)] flex flex-col animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>Chat IA</h1>
              <p className="text-zinc-500 text-sm">Converse para gerenciar tudo</p>
            </div>
          </div>
        </div>

        {/* Module selector */}
        <div className="flex gap-2 pb-4">
          {MODULES.map(m => (
            <Button
              key={m.id}
              data-testid={`chat-module-${m.id}`}
              size="sm"
              variant={module === m.id ? 'default' : 'outline'}
              onClick={() => setModule(m.id)}
              className={module === m.id ? `${m.bg} ${m.color} ${m.border} border` : 'border-white/10 text-zinc-400'}
            >
              <m.icon className="w-4 h-4 mr-1.5" /> {m.label}
            </Button>
          ))}
        </div>

        {/* Chat area */}
        <Card className="flex-1 glass-card border-0 flex flex-col min-h-0">
          <ScrollArea ref={scrollRef} className="flex-1 p-4">
            <div className="space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-20">
                  <Bot className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                  <p className="text-zinc-500 text-sm">Envie uma mensagem para começar</p>
                  <p className="text-zinc-600 text-xs mt-1">{placeholders[module]}</p>
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'assistant' && (
                    <div className={`w-8 h-8 rounded-lg ${currentMod?.bg} flex items-center justify-center flex-shrink-0`}>
                      <Bot className={`w-4 h-4 ${currentMod?.color}`} />
                    </div>
                  )}
                  <div className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-500/20 text-white'
                      : 'bg-white/5 text-zinc-200'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-zinc-600 text-xs mt-1.5">{new Date(msg.created_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-blue-400" />
                    </div>
                  )}
                </div>
              ))}
              {sending && (
                <div className="flex gap-3 justify-start">
                  <div className={`w-8 h-8 rounded-lg ${currentMod?.bg} flex items-center justify-center`}>
                    <Bot className={`w-4 h-4 ${currentMod?.color}`} />
                  </div>
                  <div className="bg-white/5 rounded-2xl px-4 py-3">
                    <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-4 border-t border-white/5">
            <div className="flex gap-3">
              <Input
                ref={inputRef}
                data-testid="chat-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                placeholder={placeholders[module]}
                className="bg-white/5 border-white/10 text-white h-11 flex-1"
                disabled={sending}
              />
              <Button
                data-testid="chat-send"
                onClick={sendMessage}
                disabled={sending || !input.trim()}
                className={`h-11 w-11 ${currentMod?.bg} ${currentMod?.color} border ${currentMod?.border}`}
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </Layout>
  );
}
