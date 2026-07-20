import { clearToken, getToken } from "./auth";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
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
    throw new ApiError(0, "Không kết nối được máy chủ. Kiểm tra backend có đang chạy không.");
  }

  if (res.status === 401) {
    clearToken();
    const data = await res.json().catch(() => null);
    throw new ApiError(401, data?.detail ?? "Phiên đăng nhập đã hết hạn.");
  }

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join("; ")
          : `Lỗi ${res.status}`;
    throw new ApiError(res.status, message);
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
    throw new ApiError(0, "Không kết nối được máy chủ. Kiểm tra backend có đang chạy không.");
  }

  if (response.status === 401) {
    clearToken();
    const data = await response.json().catch(() => null);
    throw new ApiError(401, data?.detail ?? "Phiên đăng nhập đã hết hạn.");
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    const detail = data?.detail;
    throw new ApiError(
      response.status,
      typeof detail === "string" ? detail : `Lỗi ${response.status}`,
    );
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
          throw new ApiError(0, "Máy chủ trả về dữ liệu streaming không hợp lệ.");
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
    throw new ApiError(0, "Không kết nối được máy chủ. Kiểm tra backend có đang chạy không.");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    if (res.status === 401) clearToken();
    throw new ApiError(res.status, typeof data?.detail === "string" ? data.detail : `Lỗi ${res.status}`);
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
