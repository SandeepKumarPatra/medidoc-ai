/**
 * API client for MediDoc AI backend services.
 * Implements a strict 60s timeout and structured error handling for network, 422, and timeout issues.
 */

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
const DEFAULT_TIMEOUT_MS = 60000;

export class ApiError extends Error {
  constructor(message, status = null, details = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

/**
 * Format FastAPI 422 validation errors into human-readable strings.
 */
function formatValidationErrors(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((err) => {
        const field = Array.isArray(err.loc) ? err.loc.filter((p) => p !== 'body').join('.') : 'field';
        return `${field ? field + ': ' : ''}${err.msg || 'Invalid value'}`;
      })
      .join('; ');
  }
  if (typeof detail === 'string') {
    return detail;
  }
  return 'Invalid request parameters provided.';
}

/**
 * Standardized fetch wrapper with 60s timeout and clear error classification.
 */
async function fetchWithTimeout(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(id);

    if (!response.ok) {
      let errorBody = null;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = null;
      }

      if (response.status === 422) {
        const detailMsg = formatValidationErrors(errorBody?.detail);
        throw new ApiError(`Validation Error (422): ${detailMsg}`, 422, errorBody);
      }

      const detailMsg = errorBody?.detail
        ? typeof errorBody.detail === 'string'
          ? errorBody.detail
          : JSON.stringify(errorBody.detail)
        : `Request failed with status ${response.status} (${response.statusText})`;

      throw new ApiError(detailMsg, response.status, errorBody);
    }

    return await response.json();
  } catch (err) {
    clearTimeout(id);

    if (err.name === 'AbortError') {
      throw new ApiError(
        `Request timed out after ${timeoutMs / 1000}s. The backend took too long to complete.`,
        408
      );
    }

    if (err instanceof ApiError) {
      throw err;
    }

    // Network errors (Failed to fetch, connection refused, DNS errors)
    throw new ApiError(
      `Network error: Unable to connect to backend at ${API_BASE_URL}. Ensure the FastAPI server is running and CORS is configured.`,
      0,
      err
    );
  }
}

/**
 * Check backend operational health.
 * GET /health
 */
export async function getHealth() {
  return fetchWithTimeout(`${API_BASE_URL}/health`, { method: 'GET' }, 10000);
}

/**
 * Query hospital policy documentation.
 * POST /ask
 * @param {Object} params
 * @param {string} params.question
 * @param {'naive' | 'parent_child' | 'hybrid' | 'hybrid_rerank'} [params.mode='hybrid']
 * @param {number} [params.top_k=5]
 */
export async function askQuestion({ question, mode = 'hybrid', top_k = 5 }) {
  return fetchWithTimeout(`${API_BASE_URL}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: question.trim(),
      mode,
      top_k: Number(top_k),
      debug: false,
    }),
  });
}

/**
 * Upload and extract structured clinical data and validation issues from a PDF.
 * POST /extract
 * @param {File} pdfFile
 */
export async function extractDocument(pdfFile) {
  const formData = new FormData();
  formData.append('file', pdfFile);

  return fetchWithTimeout(`${API_BASE_URL}/extract`, {
    method: 'POST',
    body: formData,
  });
}

/**
 * Fetch aggregated statistics across documents, extractions, validation, and audit logs.
 * GET /stats/overview
 */
export async function getStatsOverview() {
  return fetchWithTimeout(`${API_BASE_URL}/stats/overview`, { method: 'GET' });
}

/**
 * Fetch recent audit log entries and historical usage trends.
 * GET /stats/audit
 * @param {number} [limit=10]
 * @param {string|null} [endpoint=null]
 */
export async function getStatsAudit(limit = 10, endpoint = null) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (endpoint) {
    params.append('endpoint', endpoint);
  }
  return fetchWithTimeout(`${API_BASE_URL}/stats/audit?${params.toString()}`, { method: 'GET' });
}

/**
 * Fetch latest retrieval evaluation results and ablation metrics across modes.
 * GET /eval/results
 */
export async function getEvalResults() {
  return fetchWithTimeout(`${API_BASE_URL}/eval/results`, { method: 'GET' });
}

