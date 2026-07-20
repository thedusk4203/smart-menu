import { clearToken, getToken } from "./auth";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export class ApiError extends Error {
  status: number;
  code: string;
  userMessage: string;
  technicalMessage: string;
  details: Record<string, unknown>;
  fields: Record<string, string>;
  retryable: boolean;

  constructor(
    status: number,
    message: string,
    options: {
      code?: string;
      technicalMessage?: string;
      details?: Record<string, unknown>;
      fields?: Record<string, string>;
      retryable?: boolean;
    } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = options.code ?? defaultError(status).code;
    this.userMessage = message;
    this.technicalMessage = options.technicalMessage ?? message;
    this.details = options.details ?? {};
    this.fields = options.fields ?? {};
    this.retryable = options.retryable ?? (status === 0 || status >= 500);
  }
}

interface ErrorEnvelope {
  detail?: unknown;
  error?: {
    code?: unknown;
    message?: unknown;
    details?: unknown;
    fields?: unknown;
  };
}

const ERROR_DEFAULTS: Record<number, { code: string; message: string }> = {
  0: { code: "NETWORK_UNAVAILABLE", message: "Smart Menu chưa kết nối được. Kiểm tra mạng rồi thử lại." },
  400: { code: "BAD_REQUEST", message: "Yêu cầu chưa hợp lệ. Hãy kiểm tra rồi thử lại." },
  401: { code: "AUTH_SESSION_EXPIRED", message: "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại để tiếp tục." },
  403: { code: "AUTH_FORBIDDEN", message: "Bạn không có quyền thực hiện thao tác này." },
  404: { code: "RESOURCE_NOT_FOUND", message: "Không tìm thấy dữ liệu được yêu cầu." },
  409: { code: "RESOURCE_CONFLICT", message: "Dữ liệu đã thay đổi. Hãy tải lại rồi thử lại." },
  410: { code: "RESOURCE_GONE", message: "Nội dung này không còn khả dụng." },
  422: { code: "VALIDATION_FAILED", message: "Một số thông tin chưa hợp lệ. Hãy kiểm tra rồi thử lại." },
  500: { code: "INTERNAL_ERROR", message: "Smart Menu chưa thể hoàn tất yêu cầu. Dữ liệu của bạn chưa bị thay đổi." },
  503: { code: "SERVICE_UNAVAILABLE", message: "Dịch vụ đang tạm gián đoạn. Hãy thử lại sau." },
};

function defaultError(status: number): { code: string; message: string } {
  if (ERROR_DEFAULTS[status]) return ERROR_DEFAULTS[status];
  if (status >= 500) return ERROR_DEFAULTS[500];
  return { code: "REQUEST_FAILED", message: "Không thể hoàn tất yêu cầu. Vui lòng thử lại." };
}

function detailText(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item && typeof item === "object" && "msg" in item ? String(item.msg) : "")
      .filter(Boolean)
      .join("; ");
  }
  return "";
}

function stringRecord(value: unknown): Record<string, string> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(
    Object.entries(value).filter((entry): entry is [string, string] => typeof entry[1] === "string"),
  );
}

function objectRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

export function apiErrorFromResponse(status: number, body: unknown): ApiError {
  const fallback = defaultError(status);
  const envelope = body && typeof body === "object" ? body as ErrorEnvelope : {};
  const error = envelope.error && typeof envelope.error === "object" ? envelope.error : {};
  const technicalMessage = detailText(envelope.detail) || fallback.message;
  const message = typeof error.message === "string" && error.message.trim()
    ? error.message
    : fallback.message;
  return new ApiError(status, message, {
    code: typeof error.code === "string" && error.code ? error.code : fallback.code,
    technicalMessage,
    details: objectRecord(error.details),
    fields: stringRecord(error.fields),
  });
}

function networkError(): ApiError {
  return new ApiError(0, ERROR_DEFAULTS[0].message, {
    code: ERROR_DEFAULTS[0].code,
    technicalMessage: "Không kết nối được máy chủ.",
    retryable: true,
  });
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: unknown;
  form?: boolean;
  auth?: boolean;
}

export interface ServerSentEvent {
  event: string;
  data: unknown;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, form = false, auth = true } = options;
  const headers: Record<string, string> = {};

  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (body instanceof FormData) {
      payload = body;
    } else if (form) {
      headers["Content-Type"] = "application/x-www-form-urlencoded";
      payload = new URLSearchParams(body as Record<string, string>).toString();
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload });
  } catch {
    throw networkError();
  }

  if (res.status === 401) {
    clearToken();
    const data = await res.json().catch(() => null);
    throw apiErrorFromResponse(401, data);
  }

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw apiErrorFromResponse(res.status, data);
  }
  return data as T;
}

export async function streamSse(
  path: string,
  body: unknown,
  onEvent: (event: ServerSentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json", Accept: "text/event-stream" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw networkError();
  }

  if (response.status === 401) {
    clearToken();
    const data = await response.json().catch(() => null);
    throw apiErrorFromResponse(401, data);
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw apiErrorFromResponse(response.status, data);
  }
  if (!response.body) throw new ApiError(0, "Máy chủ không mở được luồng trả lời.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");

      let boundary = buffer.indexOf("\n\n");
      while (boundary >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        boundary = buffer.indexOf("\n\n");
        if (!block || block.startsWith(":")) continue;
        const lines = block.split("\n");
        const event = lines.find((line) => line.startsWith("event:"))?.slice(6).trim() || "message";
        const rawData = lines
          .filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart())
          .join("\n");
        if (!rawData) continue;
        try {
          onEvent({ event, data: JSON.parse(rawData) });
        } catch (error) {
          if (error instanceof ApiError) throw error;
          throw new ApiError(0, "Menuto nhận được dữ liệu chưa đúng định dạng. Hãy thử lại.", {
            code: "STREAM_DATA_INVALID",
            technicalMessage: "Máy chủ trả về dữ liệu streaming không hợp lệ.",
          });
        }
      }
      if (done) break;
    }
  } finally {
    reader.releaseLock();
  }
}

export interface DownloadFile {
  blob: Blob;
  filename: string | null;
}

async function requestDownload(path: string): Promise<DownloadFile> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, { headers });
  } catch {
    throw networkError();
  }

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    if (res.status === 401) clearToken();
    throw apiErrorFromResponse(res.status, data);
  }
  const disposition = res.headers.get("Content-Disposition") || "";
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || null;
  return { blob: await res.blob(), filename };
}

export function qs(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.append(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: Omit<RequestOptions, "method" | "body">) =>
    request<T>(path, { method: "POST", body, ...opts }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  publicGet: <T>(path: string) => request<T>(path, { method: "GET", auth: false }),
  publicPatch: <T>(path: string, body: unknown) => request<T>(path, { method: "PATCH", body, auth: false }),
  getBlob: async (path: string) => (await requestDownload(path)).blob,
  getDownload: (path: string) => requestDownload(path),
};
