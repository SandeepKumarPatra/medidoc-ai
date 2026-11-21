import React, { useState, useRef } from 'react';
import { extractDocument } from '../api/client';
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Loader2,
  AlertCircle,
  Copy,
  Check,
  Pill,
  Stethoscope,
  Calendar,
  User,
  Code2,
  FileSpreadsheet,
} from 'lucide-react';

export default function DocumentExtraction() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [activeTab, setActiveTab] = useState('formatted'); // 'formatted' | 'json'
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      if (!selected.name.toLowerCase().endsWith('.pdf')) {
        setError('Please select a valid PDF clinical document (.pdf).');
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      if (!dropped.name.toLowerCase().endsWith('.pdf')) {
        setError('Please drop a valid PDF clinical document (.pdf).');
        return;
      }
      setFile(dropped);
      setError(null);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!file || loading) return;

    setLoading(true);
    setError(null);

    try {
      const data = await extractDocument(file);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to extract document.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (!result?.extraction) return;
    navigator.clipboard.writeText(JSON.stringify(result.extraction, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const issues = result?.validation_issues || [];
  const extraction = result?.extraction;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-y-auto bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-8 py-5 shrink-0 shadow-sm">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-100 text-brand-800 border border-brand-200">
            Phase 5a
          </span>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Document Extraction Workspace</h2>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          Automated clinical document parsing, PII redaction, structured JSON extraction, and rule validation.
        </p>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 p-8 max-w-5xl w-full mx-auto space-y-6">
        {/* File Upload Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
              file
                ? 'border-brand-500 bg-brand-50/20'
                : 'border-slate-300 hover:border-brand-400 bg-slate-50/50'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />

            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="p-3 bg-white rounded-xl shadow-sm border border-slate-200">
                <UploadCloud className="w-8 h-8 text-brand-600" />
              </div>

              {file ? (
                <div className="space-y-1">
                  <div className="flex items-center justify-center space-x-2">
                    <FileText className="w-4 h-4 text-brand-600" />
                    <span className="text-sm font-bold text-slate-800">{file.name}</span>
                    <span className="text-xs text-slate-400 font-mono">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                  <p className="text-xs text-brand-600 font-medium">Click or drop another file to change</p>
                </div>
              ) : (
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-slate-700">
                    Click to select or drag & drop a clinical PDF
                  </p>
                  <p className="text-xs text-slate-400">
                    Discharge summaries or laboratory reports (.pdf up to 20 MB)
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-[11px] text-slate-400">
              Files are processed in-memory with automatic regex & labelled-field PII redaction.
            </span>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !file}
              className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Extracting Structured Data...</span>
                </>
              ) : (
                <>
                  <FileSpreadsheet className="w-4 h-4" />
                  <span>Run Document Extraction</span>
                </>
              )}
            </button>
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
                Processing clinical document via LLM structured output...
              </p>
              <p className="text-xs text-slate-500">
                Parsing layout, masking PII, schema extraction, and clinical rule validation.
              </p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-start space-x-3 text-rose-800">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-900">Extraction Error</h4>
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          </div>
        )}

        {/* Extraction Results */}
        {result && !loading && (
          <div className="space-y-6">
            {/* Metadata & Performance Overview Banner */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span className="font-semibold">{result.pii_items_masked} PII Items Redacted</span>
                </div>

                <div className="text-xs text-slate-500">
                  <span className="font-medium text-slate-700">Model:</span> {result.llm_model} •{' '}
                  <span className="font-medium text-slate-700">Prompt:</span> {result.prompt_version}
                </div>
              </div>

              {/* Stage Latency chips */}
              <div className="flex items-center space-x-2 text-xs">
                <div className="px-2 py-1 bg-slate-100 rounded text-slate-600 font-mono text-[11px]" title="PDF layout parsing time">
                  Parse: {(result.parse_ms || 0).toFixed(0)}ms
                </div>
                <div className="px-2 py-1 bg-slate-100 rounded text-slate-600 font-mono text-[11px]" title="PII masking time">
                  Mask: {(result.mask_ms || 0).toFixed(0)}ms
                </div>
                <div className="px-2 py-1 bg-slate-100 rounded text-slate-600 font-mono text-[11px]" title="LLM structured generation time">
                  LLM: {(result.llm_ms || 0).toFixed(0)}ms
                </div>
                <div className="flex items-center space-x-1 px-2.5 py-1 bg-brand-50 border border-brand-200 text-brand-900 rounded font-mono font-bold text-[11px]">
                  <Clock className="w-3 h-3 text-brand-600" />
                  <span>Total: {(result.total_ms || result.latency_ms || 0).toFixed(0)}ms</span>
                </div>
              </div>
            </div>

            {/* Validation Issues Table with Severity Badges */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className={`w-4 h-4 ${issues.length > 0 ? 'text-amber-500' : 'text-emerald-500'}`} />
                  <h3 className="text-sm font-bold text-slate-900">
                    Validation Findings ({issues.length} {issues.length === 1 ? 'issue' : 'issues'})
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400 font-medium">
                  SPEC.md Section 6 clinical validation rules
                </span>
              </div>

              {issues.length > 0 ? (
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="px-4 py-3">Severity</th>
                        <th className="px-4 py-3">Field</th>
                        <th className="px-4 py-3">Rule</th>
                        <th className="px-4 py-3">Message</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {issues.map((issue, idx) => {
                        const isError = issue.severity?.toLowerCase() === 'error';
                        return (
                          <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                            <td className="px-4 py-3 whitespace-nowrap">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                  isError
                                    ? 'bg-rose-100 text-rose-800 border-rose-200'
                                    : 'bg-amber-100 text-amber-800 border-amber-200'
                                }`}
                              >
                                {issue.severity || 'warning'}
                              </span>
                            </td>
                            <td className="px-4 py-3 font-mono text-slate-800 font-medium">
                              {issue.field}
                            </td>
                            <td className="px-4 py-3 text-slate-600 font-mono text-[11px]">
                              {issue.rule}
                            </td>
                            <td className="px-4 py-3 text-slate-700 leading-relaxed">
                              {issue.message}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2.5 text-emerald-800 text-xs">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span className="font-semibold">
                    All validation rules passed! No clinical date discrepancies, missing dosages, or out-of-range ages detected.
                  </span>
                </div>
              )}
            </div>

            {/* Extracted JSON Section (Readable formatted view + Raw JSON) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="bg-slate-50 px-6 py-3 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setActiveTab('formatted')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      activeTab === 'formatted'
                        ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                        : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    Readable Summary
                  </button>
                  <button
                    onClick={() => setActiveTab('json')}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      activeTab === 'json'
                        ? 'bg-white text-slate-900 shadow-sm border border-slate-200'
                        : 'text-slate-500 hover:text-slate-900'
                    }`}
                  >
                    Structured JSON
                  </button>
                </div>

                <button
                  onClick={handleCopyJson}
                  className="inline-flex items-center space-x-1.5 text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-700 font-medium">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy JSON</span>
                    </>
                  )}
                </button>
              </div>

              {activeTab === 'formatted' && extraction && (
                <div className="p-6 space-y-6">
                  {/* Patient Info Card */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-brand-100 text-brand-700 rounded-lg">
                        <User className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Patient</div>
                        <div className="text-xs font-bold text-slate-800">{extraction.patient?.name || 'N/A'}</div>
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] uppercase font-bold text-slate-400">Demographics</div>
                      <div className="text-xs font-semibold text-slate-800">
                        {extraction.patient?.age} yrs • Sex: {extraction.patient?.sex}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Admission</div>
                        <div className="text-xs font-mono font-medium text-slate-800">
                          {extraction.admission_date || 'N/A'}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                      <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Discharge</div>
                        <div className="text-xs font-mono font-medium text-slate-800">
                          {extraction.discharge_date || 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Diagnoses */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
                      <Stethoscope className="w-4 h-4 text-brand-600" />
                      <span>Diagnoses ({extraction.diagnosis?.length || 0})</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {extraction.diagnosis && extraction.diagnosis.length > 0 ? (
                        extraction.diagnosis.map((diag, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 rounded-lg bg-brand-50 border border-brand-200 text-brand-900 text-xs font-medium"
                          >
                            {diag}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-rose-600 italic">No diagnoses recorded</span>
                      )}
                    </div>
                  </div>

                  {/* Medications */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-800">
                      <Pill className="w-4 h-4 text-indigo-600" />
                      <span>Medications Prescribed ({extraction.medications?.length || 0})</span>
                    </div>
                    {extraction.medications && extraction.medications.length > 0 ? (
                      <div className="border border-slate-200 rounded-xl overflow-hidden">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold text-[10px] uppercase">
                            <tr>
                              <th className="px-4 py-2.5">Medication</th>
                              <th className="px-4 py-2.5">Dose</th>
                              <th className="px-4 py-2.5">Unit</th>
                              <th className="px-4 py-2.5">Frequency & Route</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {extraction.medications.map((med, idx) => (
                              <tr key={idx} className="hover:bg-slate-50/60">
                                <td className="px-4 py-2.5 font-bold text-slate-800">{med.name}</td>
                                <td className="px-4 py-2.5 font-mono">
                                  {med.dose !== null && med.dose !== undefined ? (
                                    med.dose
                                  ) : (
                                    <span className="text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                                      Missing
                                    </span>
                                  )}
                                </td>
                                <td className="px-4 py-2.5 font-mono">
                                  {med.unit ? (
                                    med.unit
                                  ) : (
                                    <span className="text-rose-600 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                                      Missing
                                    </span>
                                  )}
                                </td>
                                <td className="px-4 py-2.5 text-slate-600">{med.frequency || '—'}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic">No medications listed.</p>
                    )}
                  </div>

                  {/* Summary */}
                  <div className="space-y-1.5">
                    <div className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                      Clinician-Style Summary
                    </div>
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
                      {extraction.summary}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'json' && (
                <div className="p-4 bg-slate-900 text-slate-100 overflow-x-auto text-xs font-mono leading-relaxed max-h-[500px]">
                  <pre>
                    <code>{JSON.stringify(extraction, null, 2)}</code>
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
