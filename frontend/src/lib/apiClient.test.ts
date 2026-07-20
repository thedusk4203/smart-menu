import { beforeEach, describe, expect, it, vi } from "vitest";

import { clearToken, saveToken } from "./auth";
import { api, ApiError, qs, streamSse } from "./apiClient";


const fetchMock = vi.fn<typeof fetch>();


beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  clearToken();
});


describe("api client", () => {
  it("adds the bearer token and parses a JSON response", async () => {
    saveToken("token-123");
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(api.get<{ status: string }>("/api/health")).resolves.toEqual({
      status: "ok",
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/health", {
      method: "GET",
      headers: { Authorization: "Bearer token-123" },
      body: undefined,
    });
  });

  it("clears an expired token and exposes the backend error", async () => {
    saveToken("expired");
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "Phiên đăng nhập đã hết hạn." }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(api.get("/api/users/me")).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "Phiên đăng nhập đã hết hạn.",
    });
    expect(localStorage.getItem("smart_menu_token")).toBeNull();
  });

  it("normalizes validation details and network failures", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: [{ msg: "days không hợp lệ" }] }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(api.post("/api/meal-plans/generate", {})).rejects.toMatchObject({
      status: 422,
      message: "days không hợp lệ",
    });

    fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    await expect(api.get("/api/health")).rejects.toEqual(
      new ApiError(0, "Không kết nối được máy chủ. Kiểm tra backend có đang chạy không."),
    );
  });

  it("handles 204 and unauthenticated public requests", async () => {
    saveToken("private-token");
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }));

    await expect(api.publicPatch("/api/public/items/1", { is_purchased: true })).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledWith("/api/public/items/1", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_purchased: true }),
    });
  });

  it("supports every HTTP wrapper and encoded form bodies", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await api.put("/api/items/1", { name: "Mới" });
    await api.patch("/api/items/1", { active: true });
    await api.del("/api/items/1");
    await api.publicGet("/api/public/items");
    await api.post("/api/auth/login", { username: "a", password: "b" }, { form: true });

    expect(fetchMock).toHaveBeenLastCalledWith("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "username=a&password=b",
    });
  });

  it("uploads FormData without forcing a content type", async () => {
    const form = new FormData();
    form.append("file", new Blob(["data"]), "input.csv");
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ accepted: true }), { status: 200 }),
    );

    await api.post("/api/admin/imports/preview", form);

    expect(fetchMock).toHaveBeenCalledWith("/api/admin/imports/preview", {
      method: "POST",
      headers: {},
      body: form,
    });
  });

  it("downloads blobs and extracts the response filename", async () => {
    saveToken("download-token");
    fetchMock.mockImplementation(async () =>
      new Response("csv-data", {
        status: 200,
        headers: { "Content-Disposition": 'attachment; filename="ingredients.csv"' },
      }),
    );

    const download = await api.getDownload("/api/admin/ingredients/export");
    const blob = await api.getBlob("/api/admin/ingredients/export");

    expect(download.filename).toBe("ingredients.csv");
    expect(await download.blob.text()).toBe("csv-data");
    expect(await blob.text()).toBe("csv-data");
  });

  it("normalizes download failures and clears a rejected token", async () => {
    saveToken("expired-download");
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Không có quyền" }), { status: 401 }),
    );

    await expect(api.getDownload("/api/admin/export")).rejects.toMatchObject({
      status: 401,
      message: "Không có quyền",
    });
    expect(localStorage.getItem("smart_menu_token")).toBeNull();

    fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    await expect(api.getDownload("/api/admin/export")).rejects.toMatchObject({ status: 0 });
  });
});


describe("query strings", () => {
  it("omits empty values and encodes the rest", () => {
    expect(qs({ search: "cá hồi", offset: 0, empty: "", missing: undefined })).toBe(
      "?search=c%C3%A1+h%E1%BB%93i&offset=0",
    );
    expect(qs({ empty: "", missing: null })).toBe("");
  });
});


describe("SSE streaming", () => {
  it("reassembles split chunks and parses named events", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode("event: token\ndata: {\"text\":\"xin"));
        controller.enqueue(encoder.encode(" chào\"}\n\nevent: done\ndata: {\"ok\":true}\n\n"));
        controller.close();
      },
    });
    fetchMock.mockResolvedValue(new Response(stream, { status: 200 }));
    const events: Array<{ event: string; data: unknown }> = [];

    await streamSse("/api/ai/chat/stream", { message: "hello" }, (event) => {
      events.push(event);
    });

    expect(events).toEqual([
      { event: "token", data: { text: "xin chào" } },
      { event: "done", data: { ok: true } },
    ]);
  });

  it("rejects malformed event data", async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode("event: token\ndata: not-json\n\n"));
        controller.close();
      },
    });
    fetchMock.mockResolvedValue(new Response(stream, { status: 200 }));

    await expect(streamSse("/api/ai/chat/stream", {}, vi.fn())).rejects.toMatchObject({
      status: 0,
      message: "Máy chủ trả về dữ liệu streaming không hợp lệ.",
    });
  });

  it("maps auth, HTTP and network failures", async () => {
    saveToken("stream-token");
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Phiên streaming hết hạn" }), { status: 401 }),
    );
    await expect(streamSse("/api/ai/chat/stream", {}, vi.fn())).rejects.toMatchObject({
      status: 401,
      message: "Phiên streaming hết hạn",
    });

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Provider đang tắt" }), { status: 503 }),
    );
    await expect(streamSse("/api/ai/chat/stream", {}, vi.fn())).rejects.toMatchObject({
      status: 503,
      message: "Provider đang tắt",
    });

    fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    await expect(streamSse("/api/ai/chat/stream", {}, vi.fn())).rejects.toMatchObject({
      status: 0,
    });
  });

  it("preserves AbortError and ignores comments or events without data", async () => {
    const abort = new DOMException("aborted", "AbortError");
    fetchMock.mockRejectedValueOnce(abort);
    await expect(streamSse("/api/ai/chat/stream", {}, vi.fn())).rejects.toBe(abort);

    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode(": keep-alive\n\nevent: ping\n\n"));
        controller.close();
      },
    });
    fetchMock.mockResolvedValueOnce(new Response(stream, { status: 200 }));
    const onEvent = vi.fn();
    await streamSse("/api/ai/chat/stream", {}, onEvent);
    expect(onEvent).not.toHaveBeenCalled();
  });
});
