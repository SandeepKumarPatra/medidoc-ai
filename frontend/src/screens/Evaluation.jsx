import React, { useState, useEffect, useCallback } from 'react';
import { getEvalResults } from '../api/client';
import {
  Award,
  Zap,
  Clock,
  ShieldAlert,
  RefreshCw,
  Loader2,
  AlertCircle,
  HelpCircle,
  CheckCircle2,
  BarChart2,
  TrendingUp,
  FileCheck2,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';

function formatModeName(mode) {
  switch (mode) {
    case 'hybrid':
      return 'hybrid (Default)';
    case 'parent_child':
      return 'parent_child';
    case 'hybrid_rerank':
      return 'hybrid_rerank (BGE)';
    case 'hybrid_rerank_bge':
      return 'hybrid_rerank (BGE)';
    case 'hybrid_rerank_minilm':
      return 'hybrid_rerank (MiniLM)';
    case 'naive':
      return 'naive (Child only)';
    default:
      return mode;
  }
}

export default function Evaluation() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchResults = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const res = await getEvalResults();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load evaluation benchmark results.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  const runs = data?.runs || [];

  // Chart data for MRR
  const mrrChartData = runs.map((r) => ({
    mode: r.mode,
    name: formatModeName(r.mode),
    mrr: Number((r.overall?.mrr || 0).toFixed(4)),
    isDefault: r.mode === 'hybrid',
  }));

  // Chart data for Latency
  const latencyChartData = runs.map((r) => ({
    mode: r.mode,
    name: formatModeName(r.mode),
    latency: Number((r.overall?.avg_latency_ms || 0).toFixed(1)),
    isDefault: r.mode === 'hybrid',
  }));

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-8 py-5 shrink-0 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Retrieval Evaluation & Ablation</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Empirical multi-mode benchmark metrics, Mean Reciprocal Rank (MRR), and recall on compound queries.
            </p>
          </div>

          <button
            onClick={() => fetchResults(true)}
            disabled={loading || refreshing}
            className="inline-flex items-center space-x-2 px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm transition-all disabled:opacity-50 cursor-pointer self-start md:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-brand-600' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Benchmark'}</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-8 max-w-6xl w-full mx-auto space-y-6">
        {/* Loading Spinner */}
        {loading && (
          <div className="bg-white rounded-2xl border border-brand-200 shadow-sm p-12 flex flex-col items-center justify-center space-y-4 text-center">
            <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-800">Loading Benchmark Ablation Data...</p>
              <p className="text-xs text-slate-500">Retrieving evaluation runs and computing category breakdowns.</p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-start space-x-3 text-rose-800">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-900">Evaluation Query Failed</h4>
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Ablation Table Section */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Award className="w-4 h-4 text-brand-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Retrieval Mode Ablation Table ({runs.length} Modes)
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400 font-medium">
                  Benchmarked over curated clinical SOP query dataset
                </span>
              </div>

              {runs.length > 0 ? (
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Retrieval Mode</th>
                        <th className="px-4 py-3 text-right">Hit@1</th>
                        <th className="px-4 py-3 text-right">Hit@5</th>
                        <th className="px-4 py-3 text-right">MRR</th>
                        <th className="px-4 py-3 text-right">Retrieval Latency</th>
                        <th className="px-4 py-3 text-right">Compound Both-Hit@5</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {runs.map((run) => {
                        const isHybrid = run.mode === 'hybrid';
                        const bothHit =
                          run.compound?.compound_both_hit_at_5 ??
                          run.overall?.compound_both_hit_at_5;
                        const hit1 = run.overall?.hit_at_1 ?? 0;
                        const hit5 = run.overall?.hit_at_5 ?? 0;
                        const mrr = run.overall?.mrr ?? 0;
                        const latency = run.overall?.avg_latency_ms ?? 0;

                        return (
                          <tr
                            key={run.run_id}
                            className={`transition-colors ${
                              isHybrid ? 'bg-brand-50/40 font-medium' : 'hover:bg-slate-50/70'
                            }`}
                          >
                            <td className="px-4 py-3 whitespace-nowrap">
                              <div className="flex items-center space-x-2">
                                <span className="font-bold text-slate-800">
                                  {formatModeName(run.mode)}
                                </span>
                                {isHybrid && (
                                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-100 text-brand-800 border border-brand-200">
                                    Default
                                  </span>
                                )}
                              </div>
                              {run.notes && (
                                <div className="text-[10px] text-slate-400 font-normal">
                                  {run.notes}
                                </div>
                              )}
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-slate-700">
                              {(hit1 * 100).toFixed(1)}%
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-slate-700">
                              {(hit5 * 100).toFixed(1)}%
                            </td>
                            <td className="px-4 py-3 text-right font-mono font-semibold text-slate-900">
                              {mrr.toFixed(3)}
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-slate-700">
                              {latency > 1000
                                ? `${(latency / 1000).toFixed(2)}s`
                                : `${latency.toFixed(1)}ms`}
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-slate-700">
                              {bothHit !== null && bothHit !== undefined
                                ? `${(bothHit * 100).toFixed(1)}%`
                                : '—'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-8 text-center bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-500 space-y-2">
                  <p className="font-semibold text-slate-700">No evaluation runs recorded in database.</p>
                  <p>Execute evaluation via CLI: <code className="bg-slate-200 px-1.5 py-0.5 rounded font-mono">python -m backend.app.eval.run</code></p>
                </div>
              )}

              {/* Required honest note under the table */}
              <div className="p-3.5 bg-slate-100/80 rounded-xl border border-slate-200 text-xs text-slate-600 leading-relaxed flex items-start space-x-2">
                <ShieldAlert className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p>
                  <strong>Honest finding:</strong> Hybrid is the default; reranking helps compound questions but is much slower. Extraction test is a smoke test on synthetic reports.
                </p>
              </div>
            </div>

            {/* Recharts Bar Charts: MRR per Mode & Latency per Mode */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart 1: MRR per Mode */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-brand-600" />
                    <h3 className="text-sm font-bold text-slate-900">Mean Reciprocal Rank (MRR) per Mode</h3>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">Scale 0.0 - 1.0</span>
                </div>

                <div className="h-64 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={mrrChartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                      <XAxis
                        dataKey="name"
                        stroke="#64748b"
                        fontSize={10}
                        angle={-15}
                        textAnchor="end"
                        tickLine={false}
                        interval={0}
                      />
                      <YAxis
                        stroke="#64748b"
                        fontSize={11}
                        domain={[0, 1]}
                        tickLine={false}
                        axisLine={{ stroke: '#e2e8f0' }}
                      />
                      <Tooltip
                        formatter={(val) => [val, 'MRR']}
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          color: '#f8fafc',
                          borderRadius: '0.75rem',
                          border: 'none',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="mrr" radius={[6, 6, 0, 0]}>
                        {mrrChartData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={entry.isDefault ? '#0284c7' : '#94a3b8'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Chart 2: Latency per Mode */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-brand-600" />
                    <h3 className="text-sm font-bold text-slate-900">Average Retrieval Latency per Mode</h3>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">Milliseconds (ms)</span>
                </div>

                <div className="h-64 w-full pt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={latencyChartData} margin={{ top: 10, right: 10, left: 10, bottom: 25 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                      <XAxis
                        dataKey="name"
                        stroke="#64748b"
                        fontSize={10}
                        angle={-15}
                        textAnchor="end"
                        tickLine={false}
                        interval={0}
                      />
                      <YAxis
                        stroke="#64748b"
                        fontSize={11}
                        tickLine={false}
                        axisLine={{ stroke: '#e2e8f0' }}
                      />
                      <Tooltip
                        formatter={(val) => [`${val} ms`, 'Avg Latency']}
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          color: '#f8fafc',
                          borderRadius: '0.75rem',
                          border: 'none',
                          fontSize: '12px',
                        }}
                      />
                      <Bar dataKey="latency" radius={[6, 6, 0, 0]}>
                        {latencyChartData.map((entry, index) => (
                          <Cell
                            key={`cell-lat-${index}`}
                            fill={entry.isDefault ? '#0ea5e9' : '#64748b'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Optional Answers Summary Card */}
            {(data.answers || data.answers_hybrid) && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Grounded Answer Synthesis Evaluation
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
                  {data.answers && (
                    <>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Citation Inclusion (Rerank)</div>
                        <div className="text-lg font-bold text-slate-900 mt-1">
                          {(data.answers.citation_inclusion_rate * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Key Term Overlap</div>
                        <div className="text-lg font-bold text-slate-900 mt-1">
                          {(data.answers.key_term_overlap_rate * 100).toFixed(1)}%
                        </div>
                      </div>
                    </>
                  )}

                  {data.answers_hybrid && (
                    <>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Citation Inclusion (Hybrid)</div>
                        <div className="text-lg font-bold text-slate-900 mt-1">
                          {(data.answers_hybrid.citation_inclusion_rate * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <div className="text-slate-500 font-medium">Wrong 'Not Found' Refusals</div>
                        <div className="text-lg font-bold text-slate-900 mt-1">
                          {data.answers_hybrid.wrong_not_found_count} (
                          {(data.answers_hybrid.wrong_not_found_rate * 100).toFixed(1)}%)
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Optional Unanswerable Question Guardrails Card */}
            {data.unanswerable && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center space-x-2">
                  <HelpCircle className="w-4 h-4 text-purple-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Unanswerable Inquiry Refusal Guardrails
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-3 bg-purple-50 rounded-xl border border-purple-200">
                    <div className="text-purple-700 font-medium">Correct Refusal Rate</div>
                    <div className="text-lg font-bold text-purple-900 mt-1">
                      {(data.unanswerable.correctly_not_found_rate * 100).toFixed(1)}%
                    </div>
                    <div className="text-[11px] text-purple-600 mt-0.5">
                      {data.unanswerable.correctly_not_found_count} of {data.unanswerable.total_evaluated} questions
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-slate-500 font-medium">Hallucinated / Wrong Answers</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">
                      {data.unanswerable.wrongly_produced_count} (
                      {(data.unanswerable.wrongly_produced_rate * 100).toFixed(1)}%)
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-slate-500 font-medium">Avg Generation Latency</div>
                    <div className="text-lg font-bold text-slate-900 mt-1 font-mono">
                      {data.unanswerable.avg_generation_ms.toFixed(0)} ms
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Optional Extraction Summary Card if present */}
            {data.extraction && (
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
                <div className="flex items-center space-x-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Clinical Structured Extraction Smoke Test
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 text-xs">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-slate-500 font-medium">Scored Reports</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">
                      {data.extraction.total_reports}
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-slate-500 font-medium">Overall Field Accuracy</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">
                      {(data.extraction.overall_field_accuracy * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-slate-500 font-medium">Validation Precision</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">
                      {(data.extraction.validation_precision * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-slate-500 font-medium">Validation F1 Score</div>
                    <div className="text-lg font-bold text-slate-900 mt-1">
                      {(data.extraction.validation_f1 * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
