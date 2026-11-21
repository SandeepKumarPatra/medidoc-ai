import React, { useState, useEffect, useCallback } from 'react';
import { getStatsOverview, getStatsAudit } from '../api/client';
import {
  FileText,
  FileCheck2,
  AlertTriangle,
  MessageSquare,
  Clock,
  ShieldCheck,
  RefreshCw,
  Loader2,
  AlertCircle,
  BarChart3,
  Activity,
  Layers,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';

export default function Overview() {
  const [stats, setStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const [overviewData, auditData] = await Promise.all([
        getStatsOverview(),
        getStatsAudit(10),
      ]);
      setStats(overviewData);
      setAuditLogs(auditData.recent_logs || []);
    } catch (err) {
      setError(err.message || 'Failed to load system overview statistics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Transform documents_by_type for Recharts
  const docTypeData = stats?.documents_by_type
    ? Object.entries(stats.documents_by_type).map(([type, count]) => ({
        type: type.toUpperCase(),
        label: type === 'sop' ? 'SOP Policies' : type === 'discharge' ? 'Discharge' : 'Lab Reports',
        count,
      }))
    : [];

  // Compute average latency across active endpoints
  const endpointLatencies = stats?.avg_latency_ms_by_endpoint
    ? Object.entries(stats.avg_latency_ms_by_endpoint)
    : [];
  const averageLatency =
    endpointLatencies.length > 0
      ? endpointLatencies.reduce((sum, [, lat]) => sum + lat, 0) / endpointLatencies.length
      : 0;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-8 py-5 shrink-0 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-100 text-brand-800 border border-brand-200">
                Phase 6a
              </span>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Overview Dashboard</h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Aggregated operational metrics, corpus composition, and metadata-only privacy audit trail.
            </p>
          </div>

          <button
            onClick={() => fetchData(true)}
            disabled={loading || refreshing}
            className="inline-flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm transition-all disabled:opacity-50 cursor-pointer self-start md:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-brand-600' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Metrics'}</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-8 max-w-6xl w-full mx-auto space-y-6">
        {/* Loading State */}
        {loading && (
          <div className="bg-white rounded-2xl border border-brand-200 shadow-sm p-12 flex flex-col items-center justify-center space-y-4 text-center">
            <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-800">Loading System Statistics...</p>
              <p className="text-xs text-slate-500">Querying database aggregations and recent audit records.</p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-start space-x-3 text-rose-800">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-900">Failed to Load Dashboard</h4>
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {stats && !loading && (
          <>
            {/* KPI Cards Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Card 1: Documents Indexed */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Documents Indexed
                  </span>
                  <div className="p-2 bg-brand-50 text-brand-600 rounded-xl">
                    <FileText className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-slate-900">{stats.total_documents}</div>
                  <div className="text-[11px] text-slate-400 mt-1 flex items-center space-x-1">
                    <Layers className="w-3 h-3 text-slate-400" />
                    <span>{stats.parents_total} parents • {stats.children_total} chunks</span>
                  </div>
                </div>
              </div>

              {/* Card 2: Extractions Run */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Extractions Run
                  </span>
                  <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl">
                    <FileCheck2 className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-slate-900">{stats.extractions_total}</div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {stats.extractions_with_issues} flagged with issues
                  </div>
                </div>
              </div>

              {/* Card 3: Validation Issue Rate */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Issue Rate
                  </span>
                  <div className="p-2 bg-amber-50 text-amber-600 rounded-xl">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-slate-900">
                    {(stats.issue_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-[11px] text-amber-700 font-medium mt-1">
                    {stats.extractions_with_issues} of {stats.extractions_total} reports
                  </div>
                </div>
              </div>

              {/* Card 4: Queries Answered */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Queries Answered
                  </span>
                  <div className="p-2 bg-indigo-50 text-indigo-600 rounded-xl">
                    <MessageSquare className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-slate-900">{stats.asks_total}</div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Grounded RAG /ask queries
                  </div>
                </div>
              </div>

              {/* Card 5: Average Latency */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Average Latency
                  </span>
                  <div className="p-2 bg-purple-50 text-purple-600 rounded-xl">
                    <Clock className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold text-slate-900 font-mono">
                    {averageLatency > 1000
                      ? `${(averageLatency / 1000).toFixed(1)}s`
                      : `${averageLatency.toFixed(0)}ms`}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    Across all logged endpoints
                  </div>
                </div>
              </div>
            </div>

            {/* Recharts Bar Chart: Documents by Type */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="w-4 h-4 text-brand-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Document Corpus Distribution by Type
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400 font-medium">
                  Total {stats.total_documents} indexed PDF documents
                </span>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={docTypeData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="label"
                      stroke="#64748b"
                      fontSize={12}
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={12}
                      allowDecimals={false}
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                    />
                    <Tooltip
                      formatter={(val) => [`${val} documents`, 'Count']}
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        color: '#f8fafc',
                        borderRadius: '0.75rem',
                        border: 'none',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" fill="#0284c7" radius={[6, 6, 0, 0]} barSize={48} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Endpoint average latency breakdown chips */}
              <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-400 font-medium">Endpoint Latency:</span>
                {endpointLatencies.map(([endpoint, lat]) => (
                  <span
                    key={endpoint}
                    className="px-2.5 py-1 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 font-mono text-[11px]"
                  >
                    <span className="text-slate-500">{endpoint}:</span>{' '}
                    <span className="font-semibold text-slate-800">
                      {lat > 1000 ? `${(lat / 1000).toFixed(2)}s` : `${lat.toFixed(0)}ms`}
                    </span>
                  </span>
                ))}
                <span className="ml-auto inline-flex items-center space-x-1 text-[11px] text-emerald-700 font-medium bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{stats.total_pii_masked} Total PII Redacted</span>
                </span>
              </div>
            </div>

            {/* Audit Log Table (Metadata only, Never show document text) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-brand-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Recent Privacy & Audit Log Feed
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400 font-medium">
                  Metadata only • Zero raw document text or PII recorded
                </span>
              </div>

              {auditLogs.length > 0 ? (
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Timestamp</th>
                        <th className="px-4 py-3">Endpoint</th>
                        <th className="px-4 py-3">PII Masked</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3 text-right">Latency</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {auditLogs.map((row) => {
                        const isSuccess = row.status === 'success';
                        const dateStr = row.timestamp
                          ? new Date(row.timestamp).toLocaleString()
                          : '—';
                        return (
                          <tr key={row.id} className="hover:bg-slate-50/70 transition-colors">
                            <td className="px-4 py-3 text-slate-600 whitespace-nowrap font-mono text-[11px]">
                              {dateStr}
                            </td>
                            <td className="px-4 py-3 font-semibold text-slate-800 font-mono">
                              {row.endpoint}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold ${
                                  row.pii_items_masked > 0
                                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                    : 'text-slate-500'
                                }`}
                              >
                                {row.pii_items_masked > 0 ? (
                                  <>
                                    <ShieldCheck className="w-3 h-3 text-emerald-600" />
                                    <span>{row.pii_items_masked} masked</span>
                                  </>
                                ) : (
                                  <span>0</span>
                                )}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                  isSuccess
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                    : 'bg-rose-50 text-rose-700 border-rose-200'
                                }`}
                              >
                                {row.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-slate-800 font-medium">
                              {row.latency_ms > 1000
                                ? `${(row.latency_ms / 1000).toFixed(2)}s`
                                : `${row.latency_ms.toFixed(1)}ms`}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic p-4 text-center">
                  No recent audit log rows found in database.
                </p>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
