import React, { useState } from 'react';
import { askQuestion } from '../api/client';
import {
  Send,
  Loader2,
  Clock,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Layers,
  FileCheck2,
} from 'lucide-react';

const SAMPLE_QUESTIONS = [
  'What are the mandatory hand hygiene protocols and WHO 5 moments?',
  'What is the escalation procedure when a surgical sponge count is discrepant?',
  'What personal protective equipment is required for contact isolation rooms?',
];

export default function PolicyQA() {
  const [question, setQuestion] = useState('');
  const [mode, setMode] = useState('hybrid');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const data = await askQuestion({
        question: question.trim(),
        mode,
        top_k: Number(topK),
      });
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to complete question answering request.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Timings calculation: retrieval ms = total minus generation
  const totalMs = result?.timings?.total_ms ?? 0;
  const genMs = result?.timings?.generation_ms ?? 0;
  const retrievalMs = Math.max(0, totalMs - genMs);

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-8 py-5 shrink-0 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-100 text-brand-800 border border-brand-200">
                Phase 5a
              </span>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Policy Q&A Workspace</h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Evidence-based hospital policy retrieval with deterministic citations and latency breakdown.
            </p>
          </div>

          {/* Mode Selector and Top-K controls */}
          <div className="flex items-center space-x-3 bg-slate-100 p-1.5 rounded-xl border border-slate-200">
            <div className="flex items-center space-x-1.5 px-2">
              <Layers className="w-4 h-4 text-slate-500" />
              <label htmlFor="mode-select" className="text-xs font-semibold text-slate-700">
                Mode:
              </label>
              <select
                id="mode-select"
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                disabled={loading}
                className="bg-white border border-slate-300 text-slate-800 text-xs font-medium rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-brand-500 focus:outline-none disabled:opacity-50"
              >
                <option value="hybrid">hybrid (Dense + Sparse RRF)</option>
                <option value="parent_child">parent_child (Dense Expanded)</option>
                <option value="hybrid_rerank">hybrid_rerank (Cross-Encoder)</option>
                <option value="naive">naive (Child Chunks Only)</option>
              </select>
            </div>

            <div className="h-4 w-px bg-slate-300" />

            <div className="flex items-center space-x-1.5 px-2">
              <label htmlFor="topk-input" className="text-xs font-semibold text-slate-700">
                top_k:
              </label>
              <input
                id="topk-input"
                type="number"
                min={1}
                max={20}
                value={topK}
                onChange={(e) => setTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
                disabled={loading}
                className="w-14 bg-white border border-slate-300 text-slate-800 text-xs font-medium rounded-lg px-2 py-1.5 text-center focus:ring-2 focus:ring-brand-500 focus:outline-none disabled:opacity-50"
              />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-8 max-w-5xl w-full mx-auto space-y-6">
        {/* Question Input Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="relative">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about hospital SOPs, clinical protocols, or operating procedures..."
                rows={3}
                disabled={loading}
                className="w-full text-sm text-slate-800 placeholder-slate-400 bg-slate-50/60 border border-slate-300 rounded-xl p-3.5 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 focus:outline-none resize-none transition-all disabled:opacity-60"
              />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-[11px] text-slate-400">
                Press <kbd className="px-1.5 py-0.5 bg-slate-100 rounded border border-slate-300 font-mono text-[10px]">Enter</kbd> to submit, <kbd className="px-1.5 py-0.5 bg-slate-100 rounded border border-slate-300 font-mono text-[10px]">Shift+Enter</kbd> for newline
              </span>

              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Retrieving & Answering...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Ask Policy Question</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Quick benchmark sample question chips */}
          <div className="pt-2 border-t border-slate-100 flex items-center space-x-2 text-xs text-slate-500">
            <Sparkles className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span className="font-medium shrink-0">Sample queries:</span>
            <div className="flex flex-wrap gap-1.5">
              {SAMPLE_QUESTIONS.map((sq, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setQuestion(sq)}
                  disabled={loading}
                  className="text-left text-[11px] bg-slate-100 hover:bg-brand-50 hover:text-brand-700 hover:border-brand-200 border border-slate-200 text-slate-700 px-2.5 py-1 rounded-lg transition-colors truncate max-w-xs"
                >
                  {sq}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Loading Spinner */}
        {loading && (
          <div className="bg-white rounded-2xl border border-brand-200 shadow-sm p-10 flex flex-col items-center justify-center space-y-4 text-center animate-pulse">
            <div className="p-3 bg-brand-50 rounded-2xl">
              <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
            </div>
            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-800">
                Retrieving grounded passages via {mode} mode...
              </p>
              <p className="text-xs text-slate-500">
                Executing dense pgvector search, reciprocal rank fusion, and synthesizing clinical citations.
              </p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-start space-x-3 text-rose-800">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-900">Query Failed</h4>
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {/* Q&A Results Display */}
        {result && !loading && (
          <div className="space-y-6">
            {/* Answer Card */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="bg-slate-50/80 px-6 py-3.5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Synthesized Clinical Answer
                  </span>
                </div>

                {/* Timings row: Retrieval ms and Generation ms */}
                <div className="flex items-center space-x-3 text-xs">
                  <div
                    className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-600"
                    title="Time spent on dense/sparse search, RRF fusion, and deduplication"
                  >
                    <Clock className="w-3.5 h-3.5 text-brand-500" />
                    <span className="font-medium">Retrieval:</span>
                    <span className="font-bold text-slate-800 font-mono">{retrievalMs.toFixed(1)} ms</span>
                  </div>

                  <div
                    className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-600"
                    title="Time spent on LLM generation"
                  >
                    <Clock className="w-3.5 h-3.5 text-indigo-500" />
                    <span className="font-medium">Generation:</span>
                    <span className="font-bold text-slate-800 font-mono">{genMs.toFixed(1)} ms</span>
                  </div>

                  <div
                    className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-100 text-slate-600 font-mono text-[11px]"
                    title="Total round-trip API processing latency"
                  >
                    <span>Total:</span>
                    <span className="font-bold text-slate-900">{totalMs.toFixed(1)} ms</span>
                  </div>
                </div>
              </div>

              {/* Answer Text */}
              <div className="p-6">
                <div className="prose prose-slate max-w-none text-sm leading-relaxed whitespace-pre-wrap text-slate-800">
                  {result.answer}
                </div>

                {result.dropped_citations && result.dropped_citations.length > 0 && (
                  <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
                    <span className="font-semibold">Note:</span> Dropped invalid hallucinated citation tags:{' '}
                    <code className="font-mono">{result.dropped_citations.join(', ')}</code>
                  </div>
                )}
              </div>
            </div>

            {/* Sources List (Strict: Never displays raw document text) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <BookOpen className="w-4 h-4 text-brand-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Retrieved Grounded Sources ({result.sources?.length || 0})
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400 font-medium">
                  Page ranges & Section headings (Raw document text suppressed for privacy)
                </span>
              </div>

              {result.sources && result.sources.length > 0 ? (
                <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
                  {result.sources.map((src, idx) => {
                    // Check if this source was specifically cited in citations list
                    const isCited = result.citations?.some(
                      (c) => c.document === src.document && c.pages === src.pages
                    );

                    return (
                      <div
                        key={idx}
                        className={`p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs transition-colors ${
                          isCited ? 'bg-brand-50/40' : 'bg-white hover:bg-slate-50'
                        }`}
                      >
                        <div className="space-y-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-slate-800 truncate" title={src.document}>
                              {src.document}
                            </span>
                            <span className="px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[11px]">
                              {src.pages}
                            </span>
                            {isCited && (
                              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                                <FileCheck2 className="w-3 h-3" />
                                <span>Cited in Answer</span>
                              </span>
                            )}
                          </div>

                          <div className="text-slate-600 flex items-center space-x-2">
                            <span className="text-slate-400 font-medium">Section:</span>
                            <span className="font-medium text-slate-700">
                              {src.section_title || 'General / Unnamed Section'}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0">
                          <span className="text-[11px] text-slate-400">Score:</span>
                          <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-slate-100 rounded text-slate-800">
                            {typeof src.score === 'number' ? src.score.toFixed(4) : src.score}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No sources were returned for this inquiry.</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
