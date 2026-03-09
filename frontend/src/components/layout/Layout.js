import React, { useEffect, useState } from 'react';
import { Menu } from 'lucide-react';

import { Sidebar } from './Sidebar';

export const Layout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!mobileOpen) return;
    const onEsc = (event) => {
      if (event.key === 'Escape') setMobileOpen(false);
    };
    window.addEventListener('keydown', onEsc);
    return () => window.removeEventListener('keydown', onEsc);
  }, [mobileOpen]);

  return (
    <div className="min-h-screen bg-[#09090b]">
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {mobileOpen && (
        <button
          type="button"
          aria-label="Fechar menu"
          className="fixed inset-0 z-30 bg-black/60 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <main className={`transition-all duration-300 min-h-screen ${collapsed ? 'md:ml-[68px]' : 'md:ml-[220px]'}`}>
        <div className="md:hidden p-4 border-b border-white/5 sticky top-0 z-20 bg-[#09090b]/95 backdrop-blur">
          <button
            type="button"
            data-testid="mobile-menu-toggle"
            className="w-10 h-10 rounded-lg border border-white/10 text-zinc-300 flex items-center justify-center"
            onClick={() => setMobileOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 md:p-6 max-w-7xl mx-auto">{children}</div>
      </main>
    </div>
  );
};
