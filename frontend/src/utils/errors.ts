/**
 * Error normalization and logging utilities for the AI Video Studio frontend.
 * Guarantees human-readable error messages and prevents '[object Object]' rendering.
 */

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    // Maintain proper prototype chain for instanceof checks
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Format a single FastAPI validation error entry into human-readable text.
 * Example input: { loc: ["body", "topic"], msg: "Field required", type: "missing" }
 * Example output: "Topic is required."
 */
function formatValidationItem(item: any): string {
  if (!item || typeof item !== 'object') {
    return String(item || '');
  }

  // Extract field name from loc array, ignoring standard wrappers like "body", "query", "path"
  let field = '';
  if (Array.isArray(item.loc)) {
    const relevantLocs = item.loc.filter(
      (part: any) => part !== 'body' && part !== 'query' && part !== 'path' && part !== 'header'
    );
    if (relevantLocs.length > 0) {
      field = relevantLocs.join('.');
    }
  }

  // Humanize field name (e.g., "visual_style" -> "Visual Style" or "topic" -> "Topic")
  const humanFieldName = field
    ? field
        .split(/[._]/)
        .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ')
    : '';

  const rawMsg = item.msg || item.message || '';
  const msgLower = rawMsg.toLowerCase();

  if (item.type === 'missing' || msgLower === 'field required') {
    return humanFieldName ? `${humanFieldName} is required.` : 'A required field is missing.';
  }

  if (humanFieldName && rawMsg) {
    return `${humanFieldName}: ${rawMsg}`;
  }

  return rawMsg || 'Invalid field value.';
}

/**
 * Safely converts any error, exception, or API response into a clean, human-readable string.
 * Completely eliminates '[object Object]'.
 */
export function normalizeApiError(
  error: unknown,
  fallbackMessage: string = 'An unexpected error occurred.'
): string {
  if (error === null || error === undefined) {
    return fallbackMessage;
  }

  // 1. Plain String
  if (typeof error === 'string') {
    const trimmed = error.trim();
    if (!trimmed || trimmed === '[object Object]') {
      return fallbackMessage;
    }

    // If the string contains serialized JSON, recursively parse and format it
    if (
      (trimmed.startsWith('{') && trimmed.endsWith('}')) ||
      (trimmed.startsWith('[') && trimmed.endsWith(']'))
    ) {
      try {
        const parsed = JSON.parse(trimmed);
        return normalizeApiError(parsed, fallbackMessage);
      } catch {
        return trimmed;
      }
    }
    return trimmed;
  }

  // 2. Error instance
  if (error instanceof Error) {
    const errObj = error as any;
    // Check if error has structured data attached (e.g. from ApiError)
    if (errObj.data !== undefined) {
      const normalizedData = normalizeApiError(errObj.data, '');
      if (normalizedData && normalizedData !== '[object Object]') {
        return normalizedData;
      }
    }
    if (errObj.detail !== undefined) {
      const normalizedDetail = normalizeApiError(errObj.detail, '');
      if (normalizedDetail && normalizedDetail !== '[object Object]') {
        return normalizedDetail;
      }
    }

    const msg = error.message ? error.message.trim() : '';
    if (msg && msg !== '[object Object]') {
      return normalizeApiError(msg, fallbackMessage);
    }
    return fallbackMessage;
  }

  // 3. Array of errors
  if (Array.isArray(error)) {
    if (error.length === 0) return fallbackMessage;
    const formattedItems = error
      .map((item) => {
        if (item && typeof item === 'object' && ('loc' in item || 'msg' in item)) {
          return formatValidationItem(item);
        }
        return normalizeApiError(item, '');
      })
      .filter((s) => Boolean(s && s !== '[object Object]'));

    return formattedItems.length > 0 ? formattedItems.join('\n') : fallbackMessage;
  }

  // 4. Object
  if (typeof error === 'object') {
    const obj = error as Record<string, any>;

    // FastAPI { "detail": ... }
    if ('detail' in obj) {
      const detail = obj.detail;

      if (typeof detail === 'string') {
        return detail.trim() || fallbackMessage;
      }

      if (Array.isArray(detail)) {
        const validationLines = detail
          .map((item) => formatValidationItem(item))
          .filter((s) => Boolean(s && s !== '[object Object]'));

        if (validationLines.length > 0) {
          return validationLines.join('\n');
        }
      }

      if (detail && typeof detail === 'object') {
        return normalizeApiError(detail, fallbackMessage);
      }
    }

    // Standard fields: message, error, msg, description
    if (typeof obj.message === 'string' && obj.message && obj.message !== '[object Object]') {
      return obj.message.trim();
    }
    if (typeof obj.error === 'string' && obj.error && obj.error !== '[object Object]') {
      return obj.error.trim();
    }
    if (obj.error && typeof obj.error === 'object') {
      return normalizeApiError(obj.error, fallbackMessage);
    }
    if (typeof obj.msg === 'string' && obj.msg && obj.msg !== '[object Object]') {
      return obj.msg.trim();
    }
    if (typeof obj.description === 'string' && obj.description) {
      return obj.description.trim();
    }

    // Check for nested errors array (e.g. { errors: [...] })
    if (Array.isArray(obj.errors)) {
      return normalizeApiError(obj.errors, fallbackMessage);
    }

    // Fallback: safely stringify structured unknown object
    try {
      const json = JSON.stringify(obj, null, 2);
      if (json && json !== '{}' && json !== '[]') {
        return json;
      }
    } catch {
      // Circular reference or serialization failure
    }
  }

  return fallbackMessage;
}

/**
 * Strips sensitive credentials (API keys, OAuth tokens, passwords) before logging.
 */
export function sanitizePayload(payload: any): any {
  if (!payload || typeof payload !== 'object') {
    return payload;
  }

  if (Array.isArray(payload)) {
    return payload.map(sanitizePayload);
  }

  const SENSITIVE_KEYWORDS = [
    'password',
    'token',
    'access_token',
    'refresh_token',
    'secret',
    'client_secret',
    'api_key',
    'apikey',
    'encrypted_access_token',
    'encrypted_refresh_token',
    'authorization',
    'x-api-key',
    'cookie',
  ];

  const sanitized: Record<string, any> = {};
  for (const [key, value] of Object.entries(payload)) {
    const isSensitive = SENSITIVE_KEYWORDS.some((kw) => key.toLowerCase().includes(kw));

    if (isSensitive) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizePayload(value);
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
}

/**
 * Development logger following project specifications.
 */
export function logApiInteraction(
  stage: 'REQUEST' | 'RESPONSE' | 'ERROR',
  info: {
    method?: string;
    endpoint?: string;
    payload?: any;
    status?: number;
    error?: any;
  }
) {
  // Always active in development
  const isDev = import.meta.env?.DEV ?? true;
  if (!isDev) return;

  switch (stage) {
    case 'REQUEST':
      console.groupCollapsed(`[API REQUEST] ${info.method || 'GET'} ${info.endpoint}`);
      console.log('REQUEST:\n' + `${info.method || 'GET'} ${info.endpoint}`);
      if (info.payload !== undefined) {
        console.log('PAYLOAD:\n', sanitizePayload(info.payload));
      }
      console.groupEnd();
      break;

    case 'RESPONSE':
      console.groupCollapsed(`[API RESPONSE] HTTP ${info.status} ${info.method || 'GET'} ${info.endpoint}`);
      console.log(`RESPONSE:\nHTTP ${info.status}`);
      console.groupEnd();
      break;

    case 'ERROR':
      console.group(`[API ERROR] HTTP ${info.status || 'ERR'} ${info.method || 'GET'} ${info.endpoint}`);
      console.log(`RESPONSE:\nHTTP ${info.status || 'FAILED'}`);
      console.error('ERROR:\n' + normalizeApiError(info.error));
      console.groupEnd();
      break;
  }
}
