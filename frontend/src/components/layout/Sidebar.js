import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  LayoutDashboard, Apple, Calendar, Wallet, MessageSquare,
  Settings, LogOut, ChevronLeft, ChevronRight, Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

const navItems = [
  { path: '/dashboard', icon: LayoutDashboard, label: 'Painel', color: 'text-blue-400' },
  { path: '/nutrition', icon: Apple, label: 'Nutrição', color: 'text-lime-400' },
  { path: '/agenda', icon: Calendar, label: 'Agenda', color: 'text-violet-400' },
  { path: '/finance', icon: Wallet, label: 'Finanças', color: 'text-sky-400' },
  { path: '/chat', icon: MessageSquare, label: 'Chat IA', color: 'text-amber-400' },
];

const bottomItems = [
  { path: '/settings', icon: Settings, label: 'Configurações', color: 'text-zinc-400' },
];

export const Sidebar = ({ collapsed, onToggle }) => {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        data-testid="sidebar"
        className={`fixed left-0 top-0 h-screen z-40 flex flex-col border-r border-white/5 bg-[#09090b] transition-all duration-300 ${collapsed ? 'w-[68px]' : 'w-[220px]'}`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 h-16 border-b border-white/5">
          <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center flex-shrink-0">
            <Zap className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="font-bold text-lg tracking-tight text-white" style={{ fontFamily: 'Plus Jakarta Sans' }}>
              Life OS
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-2 space-y-1">
          {navItems.map(({ path, icon: Icon, label, color }) => {
            const active = location.pathname === path;
            return (
              <Tooltip key={path}>
                <TooltipTrigger asChild>
                  <NavLink
                    to={path}
                    data-testid={`nav-${path.slice(1)}`}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                      active
                        ? 'bg-white/10 text-white'
                        : 'text-zinc-500 hover:text-zinc-200 hover:bg-white/5'
                    }`}
                  >
                    <Icon className={`w-5 h-5 flex-shrink-0 ${active ? color : ''}`} />
                    {!collapsed && (
                      <span className="text-sm font-medium truncate">{label}</span>
                    )}
                  </NavLink>
                </TooltipTrigger>
                {collapsed && (
                  <TooltipContent side="right" className="bg-zinc-800 text-white border-zinc-700">
                    {label}
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="py-3 px-2 space-y-1 border-t border-white/5">
          {bottomItems.map(({ path, icon: Icon, label, color }) => (
            <Tooltip key={path}>
              <TooltipTrigger asChild>
                <NavLink
                  to={path}
                  data-testid={`nav-${path.slice(1)}`}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
                    location.pathname === path
                      ? 'bg-white/10 text-white'
                      : 'text-zinc-500 hover:text-zinc-200 hover:bg-white/5'
                  }`}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 ${color}`} />
                  {!collapsed && <span className="text-sm font-medium">{label}</span>}
                </NavLink>
              </TooltipTrigger>
              {collapsed && (
                <TooltipContent side="right" className="bg-zinc-800 text-white border-zinc-700">{label}</TooltipContent>
              )}
            </Tooltip>
          ))}

          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={logout}
                data-testid="logout-btn"
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all w-full"
              >
                <LogOut className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span className="text-sm font-medium">Sair</span>}
              </button>
            </TooltipTrigger>
            {collapsed && (
              <TooltipContent side="right" className="bg-zinc-800 text-white border-zinc-700">Sair</TooltipContent>
            )}
          </Tooltip>

          {/* Toggle */}
          <button
            onClick={onToggle}
            data-testid="sidebar-toggle"
            className="flex items-center justify-center w-full py-2 text-zinc-600 hover:text-zinc-300 transition-colors"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
      </aside>
    </TooltipProvider>
  );
};
