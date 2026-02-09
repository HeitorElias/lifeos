# Life OS - PRD (Product Requirements Document)

## Problema Original
App SaaS premium "3 em 1" — Nutrição + Agenda + Finanças — com IA como analisador principal, quotas por plano, e arquitetura modular.

## Arquitetura
- **Frontend**: React + TailwindCSS + shadcn/ui (dark premium theme)
- **Backend**: FastAPI (Python) + MongoDB
- **IA**: Google Gemini 3 Flash via emergentintegrations (pluggable)
- **Food DB**: 80 alimentos TACO/USDA com dados nutricionais por 100g

## User Personas
- Profissionais 25-45 anos que querem controlar nutrição, agenda e finanças em um só lugar
- Usuários preocupados com saúde e economia

## Funcionalidades Implementadas (09/02/2026)
- [x] Auth (registro/login com JWT, bcrypt)
- [x] Onboarding (perfil de saúde, cálculo de meta calórica Mifflin-St Jeor)
- [x] Dashboard 3 em 1 (nutrição + agenda + finanças)
- [x] Nutrição: análise por foto (IA visão) e texto (IA NLP)
- [x] Nutrição: cálculo nutricional via tabelas TACO/USDA (80 alimentos)
- [x] Nutrição: dashboard com calorias/macros, gráficos, streak
- [x] Agenda: CRUD de eventos, agrupamento por data
- [x] Agenda: lembretes (estrutura pronta, mocked para MVP)
- [x] Finanças: contas a pagar (CRUD + marcar pago)
- [x] Finanças: gastos do mês (registro + dashboard por categoria)
- [x] Finanças: análise com IA (sugestões de economia)
- [x] Chat IA: interface central para nutrição, agenda e finanças
- [x] Sistema de quotas por plano (FREE/PRO/PREMIUM) com reset mensal/semanal
- [x] Simulação de upgrade de plano (admin endpoint)
- [x] Auditoria: logging de ações da IA
- [x] Interface em Português BR
- [x] Tema escuro premium com glassmorphism

## 3 Planos
- **Graze (Free)**: 3 fotos/mês, 15 ações agenda, 17 lembretes financeiros
- **Boost (Pro)**: US$ 24/mês - 90 fotos, agenda ilimitada, 60 análises
- **Thrive (Premium)**: US$ 39/mês - 200 fotos, 200 lembretes, exportação

## Integrações MOCKED (estrutura pronta)
- WhatsApp (Meta Cloud API)
- Email (AWS SES/SendGrid)
- Google Calendar OAuth
- Stripe (pagamentos)

## Backlog Priorizado
### P0 (Próxima iteração)
- Geração de plano alimentar completo (7 dias) via IA
- Exportação PDF/CSV de relatórios (Premium)
- Daily Briefing automático

### P1
- Integração real com Email (SendGrid/SES)
- Integração real com Google Calendar OAuth
- Worker de lembretes com filas (Celery/Redis)
- Histórico de chat persistente com contexto

### P2
- Integração WhatsApp (Meta Cloud API)
- Stripe real para cobrança
- React Native (mobile)
- Internacionalização (i18n inglês)
- "Calorias economizadas" com sugestão de alternativas
