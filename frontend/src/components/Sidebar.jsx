import React from 'react';
import {
  LayoutDashboard,
  BarChart2,
  MessageSquareText,
  FileText,
  ShieldAlert,
} from 'lucide-react';
import ApiStatusBadge from './ApiStatusBadge';

export default function Sidebar({ activeScreen, onSelectScreen }) {
  const navItems = [
    {
      id: 'overview',
      label: 'Overview',
      icon: LayoutDashboard,
      description: 'System metrics & audit feed',
    },
    {
      id: 'eval',
      label: 'Evaluation',
      icon: BarChart2,
      description: 'Retrieval ablation & MRR benchmarks',
    },
    {
      id: 'qa',
      label: 'Policy Q&A',
      icon: MessageSquareText,
      description: 'Grounded RAG retrieval & citations',
    },
    {
      id: 'extract',
      label: 'Document Extraction',
      icon: FileText,
      description: 'Clinical JSON & rule validation',
    },
  ];

  return (
    <aside className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col justify-between shrink-0 h-screen sticky top-0 text-slate-300">
      <div className="p-6">
        {/* Brand header */}
        <div className="flex items-center space-x-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-teal-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
            <span className="text-xl">🩺</span>
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-tight">MediDoc AI</h1>
            <p className="text-xs text-brand-300 font-medium">Clinical Document Assistant</p>
          </div>
        </div>

        {/* Navigation links */}
        <div className="space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeScreen === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectScreen(item.id)}
                className={`w-full flex items-center space-x-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <div className="text-left">
                  <div className="font-semibold leading-tight">{item.label}</div>
                  <div className={`text-[11px] ${isActive ? 'text-brand-100' : 'text-slate-400'}`}>
                    {item.description}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer & Health indicator */}
      <div className="p-4 border-t border-slate-800 space-y-3">
        <ApiStatusBadge />
        <div className="flex items-center space-x-2 text-[11px] text-slate-400 px-1">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span>Synthetic Data Only • Strict Privacy</span>
        </div>
      </div>
    </aside>
  );
}
