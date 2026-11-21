import React, { useState, useEffect, useCallback } from 'react';
import { getHealth } from '../api/client';
import { Activity, RefreshCw } from 'lucide-react';

export default function ApiStatusBadge() {
  const [health, setHealth] = useState({
    status: 'checking', // 'checking' | 'online' | 'offline'
    database: 'unknown',
    version: '',
    error: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  const checkHealth = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await getHealth();
      setHealth({
        status: data.status === 'ok' ? 'online' : 'offline',
        database: data.database || 'unknown',
        version: data.version || '1.0.0',
        error: null,
      });
    } catch (err) {
      setHealth({
        status: 'offline',
        database: 'unreachable',
        version: '',
        error: err.message,
      });
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const isOnline = health.status === 'online';
  const isChecking = health.status === 'checking';

  return (
    <div
      className="p-3 bg-slate-800/80 rounded-xl border border-slate-700 text-xs text-slate-300"
      title={health.error || `DB: ${health.database} | Version: ${health.version || 'v1.0.0'}`}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center space-x-2">
          <Activity className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-slate-200">System Status</span>
        </div>
        <button
          onClick={checkHealth}
          disabled={isRefreshing}
          className="text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          aria-label="Refresh API Health"
          title="Refresh API Health"
        >
          <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin text-brand-400' : ''}`} />
        </button>
      </div>

      <div className="flex items-center justify-between text-[11px]">
        <div className="flex items-center space-x-1.5">
          <span
            className={`w-2 h-2 rounded-full ${
              isChecking
                ? 'bg-amber-400 animate-pulse'
                : isOnline
                ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                : 'bg-rose-500'
            }`}
          />
          <span className="font-medium text-slate-200">
            {isChecking ? 'Checking API...' : isOnline ? 'API Connected' : 'API Offline'}
          </span>
        </div>
        <span className="text-[10px] text-slate-400 font-mono">
          DB: {health.database}
        </span>
      </div>
    </div>
  );
}
