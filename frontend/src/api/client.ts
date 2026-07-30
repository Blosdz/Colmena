import { getStoredToken } from "../auth/session";
import { env } from "../config/env";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

type RequestOptions = RequestInit & {
  query?: Record<string, string | number | boolean | undefined | null>;
};

// FastAPI's 422 `detail` is an array of {loc, msg, ...} objects, not a string;
// String(detail) on an array yields "[object Object]" and hides the real message.
function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((entry) => {
        if (entry && typeof entry === "object" && "msg" in entry) {
          const loc = Array.isArray((entry as { loc?: unknown[] }).loc)
            ? (entry as { loc: unknown[] }).loc.join(".")
            : null;
          const msg = String((entry as { msg: unknown }).msg);
          return loc ? `${loc}: ${msg}` : msg;
        }
        return String(entry);
      })
      .join(" · ");
  }
  return JSON.stringify(detail);
}

function buildUrl(path: string, query?: RequestOptions["query"]) {
  const url = new URL(path, env.apiBaseUrl);

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null || value === "") {
        return;
      }
      url.searchParams.set(key, String(value));
    });
  }

  return url.toString();
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { query, headers, ...init } = options;
  const token = getStoredToken();
  const response = await fetch(buildUrl(path, query), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? formatErrorDetail((payload as { detail: unknown }).detail)
        : `Error HTTP ${response.status}`;
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export const apiClient = {
  get: <T>(path: string, query?: RequestOptions["query"]) =>
    request<T>(path, { method: "GET", query }),
  post: <T>(path: string, body?: unknown, query?: RequestOptions["query"]) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined, query }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
