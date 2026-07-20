import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import toast from "react-hot-toast";
import {
  PanelLeft,
  Plus,
  Send,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { aiApi } from "../../api/aiApi";
import { ConversationRail } from "./assistant/ConversationRail";
import { MAX_CONVERSATIONS, MAX_TURNS } from "./assistant/constants";
import { MessageBubble, TurnMessages } from "./assistant/TurnMessages";
import type {
  ChatStreamEvent,
  ConversationDetail,
  ConversationSummary,
} from "../../api/aiApi";
import { ApiError } from "../../lib/apiClient";
import { ConfirmDialog, PageHeader } from "../../components/ui";

const SAMPLE_QUESTIONS = [
  "Gợi ý món ăn giàu đạm, ít calo?",
  "Làm sao để ăn đủ chất khi giảm cân?",
  "Thực đơn 1500 kcal cho một ngày?",
  "Nên ăn bao nhiêu tinh bột mỗi ngày?",
];

const errorMessage = (error: unknown) =>
  error instanceof ApiError ? error.message : "Có lỗi xảy ra. Vui lòng thử lại.";

type ActiveStream = {
  mode: "chat" | "retry";
  question: string;
  conversationId: number | null;
  turnId: number | null;
  content: string;
};

export function Assistant() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [input, setInput] = useState("");
  const [activeStream, setActiveStream] = useState<ActiveStream | null>(null);
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [conversationLoading, setConversationLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<number | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const historyButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const closeDrawerRef = useRef<HTMLButtonElement>(null);
  const streamAbortRef = useRef<AbortController | null>(null);
  const pendingDeltaRef = useRef("");
  const deltaFrameRef = useRef<number | null>(null);
  const stickToBottomRef = useRef(true);

  const lastTurn = conversation?.turns.at(-1) ?? null;
  const turnCount = conversation?.turn_count ?? 0;
  const atTurnLimit = turnCount >= MAX_TURNS;
  const unresolvedLastTurn = lastTurn?.status === "failed" || lastTurn?.status === "pending";
  const sending = activeStream?.mode === "chat";
  const retrying = activeStream?.mode === "retry";
  const streaming = activeStream !== null;
  const composerDisabled = enabled === false || streaming || atTurnLimit || unresolvedLastTurn;

  const refreshList = async () => {
    const list = await aiApi.listConversations();
    setConversations(list);
    return list;
  };

  const openConversation = async (id: number) => {
    setSelectedId(id);
    setConversationLoading(true);
    try {
      setConversation(await aiApi.getConversation(id));
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setConversationLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const initialize = async () => {
      const [statusResult, conversationsResult] = await Promise.allSettled([
        aiApi.status(),
        aiApi.listConversations(),
      ]);
      if (cancelled) return;
      if (statusResult.status === "fulfilled") {
        setEnabled(statusResult.value.enabled);
      } else {
        setEnabled(false);
      }
      if (conversationsResult.status === "fulfilled") {
        const list = conversationsResult.value;
        setConversations(list);
        if (list[0]) await openConversation(list[0].id);
      } else {
        toast.error("Không tải được lịch sử hội thoại.");
      }
      if (!cancelled) setHistoryLoading(false);
    };
    initialize();
    return () => {
      cancelled = true;
    };
  }, []);

  const flushStreamingDelta = () => {
    if (deltaFrameRef.current !== null) {
      cancelAnimationFrame(deltaFrameRef.current);
      deltaFrameRef.current = null;
    }
    const content = pendingDeltaRef.current;
    pendingDeltaRef.current = "";
    if (!content) return;
    setActiveStream((current) => current ? { ...current, content: current.content + content } : current);
  };

  const appendStreamingDelta = (content: string) => {
    pendingDeltaRef.current += content;
    if (deltaFrameRef.current !== null) return;
    deltaFrameRef.current = requestAnimationFrame(() => {
      deltaFrameRef.current = null;
      flushStreamingDelta();
    });
  };

  useEffect(() => () => {
    streamAbortRef.current?.abort();
    if (deltaFrameRef.current !== null) cancelAnimationFrame(deltaFrameRef.current);
  }, []);

  useEffect(() => {
    const container = messagesRef.current;
    if (container && stickToBottomRef.current) container.scrollTop = container.scrollHeight;
  }, [conversation, activeStream?.content]);

  useEffect(() => {
    if (!historyOpen) return;
    closeDrawerRef.current?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setHistoryOpen(false);
        historyButtonRef.current?.focus();
        return;
      }
      if (event.key !== "Tab" || !drawerRef.current) return;
      const focusable = Array.from(
        drawerRef.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [historyOpen]);

  const selectConversation = async (id: number) => {
    if (streaming) return;
    setHistoryOpen(false);
    await openConversation(id);
  };

  const startNewConversation = () => {
    if (streaming || conversations.length >= MAX_CONVERSATIONS) return;
    setSelectedId(null);
    setConversation(null);
    setInput("");
    setHistoryOpen(false);
  };

  const deleteConversation = async (id: number) => {
    if (streaming) return;
    setConfirmingDeleteId(null);
    setDeletingId(id);
    try {
      await aiApi.deleteConversation(id);
      const list = await refreshList();
      toast.success("Đã xóa cuộc trò chuyện.");
      if (selectedId === id) {
        if (list[0]) await openConversation(list[0].id);
        else startNewConversation();
      }
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setDeletingId(null);
    }
  };

  const send = async (text: string) => {
    const content = text.trim();
    if (!content || composerDisabled) return;
    setInput("");
    const controller = new AbortController();
    let streamedConversationId = selectedId;
    streamAbortRef.current = controller;
    stickToBottomRef.current = true;
    setActiveStream({
      mode: "chat",
      question: content,
      conversationId: selectedId,
      turnId: null,
      content: "",
    });
    try {
      const response = await aiApi.chatStream(
        content,
        selectedId ?? undefined,
        (event: ChatStreamEvent) => {
          if (event.event === "start") {
            streamedConversationId = event.data.conversation_id;
            setSelectedId(event.data.conversation_id);
            setActiveStream((current) => current ? {
              ...current,
              conversationId: event.data.conversation_id,
              turnId: event.data.turn.id,
            } : current);
            void refreshList();
          } else if (event.event === "delta") {
            appendStreamingDelta(event.data.content);
          }
        },
        controller.signal,
      );
      flushStreamingDelta();
      setSelectedId(response.conversation_id);
      const [, detail] = await Promise.all([
        refreshList(),
        aiApi.getConversation(response.conversation_id),
      ]);
      setConversation(detail);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      toast.error(errorMessage(error));
      try {
        const list = await refreshList();
        const fallbackId = streamedConversationId ?? list[0]?.id;
        if (fallbackId) {
          setSelectedId(fallbackId);
          setConversation(await aiApi.getConversation(fallbackId));
        }
      } catch {
        // Giữ nguyên lỗi chính; user vẫn có thể reload trang.
      }
    } finally {
      pendingDeltaRef.current = "";
      if (streamAbortRef.current === controller) streamAbortRef.current = null;
      setActiveStream(null);
    }
  };

  const retryLatest = async () => {
    if (!selectedId || !lastTurn || retrying || sending) return;
    const controller = new AbortController();
    streamAbortRef.current = controller;
    stickToBottomRef.current = true;
    setActiveStream({
      mode: "retry",
      question: lastTurn.user_content,
      conversationId: selectedId,
      turnId: lastTurn.id,
      content: "",
    });
    try {
      const response = await aiApi.retryTurnStream(
        selectedId,
        lastTurn.id,
        (event: ChatStreamEvent) => {
          if (event.event === "start") {
            setActiveStream((current) => current ? {
              ...current,
              conversationId: event.data.conversation_id,
              turnId: event.data.turn.id,
            } : current);
          } else if (event.event === "delta") {
            appendStreamingDelta(event.data.content);
          }
        },
        controller.signal,
      );
      flushStreamingDelta();
      const [, detail] = await Promise.all([
        refreshList(),
        aiApi.getConversation(response.conversation_id),
      ]);
      setConversation(detail);
      toast.success("Menuto đã tạo câu trả lời mới.");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      toast.error(errorMessage(error));
      try {
        setConversation(await aiApi.getConversation(selectedId));
      } catch {
        // Toast phía trên đã giải thích lỗi retry.
      }
    } finally {
      pendingDeltaRef.current = "";
      if (streamAbortRef.current === controller) streamAbortRef.current = null;
      setActiveStream(null);
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    send(input);
  };

  const retryTurnId = lastTurn?.id;
  const renderedTurns = useMemo(() => conversation?.turns ?? [], [conversation]);

  return (
    <div>
      <PageHeader title="Trợ lý Menuto" description="Hỏi đáp về dinh dưỡng và gợi ý món ăn." />

      <div
        className={`mb-4 flex items-start gap-2.5 rounded-2xl border px-4 py-3 text-sm ${
          enabled
            ? "border-brand-200 bg-brand-50 text-brand-800"
            : "border-accent-200 bg-accent-50 text-accent-800"
        }`}
      >
        <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" />
        <span>
          {enabled
            ? "Lịch sử chat được lưu tối đa 30 ngày."
            : "AI chưa được quản trị viên kích hoạt. Lịch sử đã lưu vẫn có thể xem lại."}
        </span>
      </div>

      <div className="flex h-[calc(100vh-13rem)] min-h-[520px] max-h-[780px] overflow-hidden rounded-2xl border border-sand-200 bg-white shadow-sm">
        <aside className="hidden w-72 shrink-0 border-r border-sand-200 lg:block">
          <ConversationRail
            conversations={conversations}
            selectedId={selectedId}
            loading={historyLoading}
            deletingId={deletingId}
            disabled={streaming}
            onSelect={selectConversation}
            onNew={startNewConversation}
            onDelete={setConfirmingDeleteId}
          />
        </aside>

        <section className="flex min-w-0 flex-1 flex-col" aria-label="Nội dung cuộc trò chuyện">
          <div className="flex items-center justify-between gap-3 border-b border-sand-200 px-3 py-2.5 sm:px-4">
            <div className="flex min-w-0 items-center gap-2">
              <button
                ref={historyButtonRef}
                type="button"
                onClick={() => setHistoryOpen(true)}
                className="rounded-lg p-2 text-gray-700 hover:bg-sand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 lg:hidden"
                aria-label="Mở danh sách cuộc trò chuyện"
              >
                <PanelLeft className="h-5 w-5" />
              </button>
              <div className="min-w-0">
                <h2 className="truncate text-sm font-semibold text-gray-800">
                  {conversation?.title || "Cuộc trò chuyện mới"}
                </h2>
                <p className="text-xs text-gray-600">{turnCount}/20 câu hỏi</p>
              </div>
            </div>
            <button
              type="button"
              onClick={startNewConversation}
              disabled={streaming || conversations.length >= MAX_CONVERSATIONS}
              className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-xs font-medium text-brand-700 hover:bg-brand-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed disabled:opacity-50 lg:hidden"
            >
              <Plus className="h-4 w-4" /> Mới
            </button>
          </div>

          <div
            ref={messagesRef}
            onScroll={(event) => {
              const element = event.currentTarget;
              stickToBottomRef.current = element.scrollHeight - element.scrollTop - element.clientHeight < 64;
            }}
            className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4 sm:p-5"
          >
            {conversationLoading ? (
              <div className="space-y-4" aria-label="Đang tải cuộc trò chuyện">
                <div className="ml-auto h-12 w-2/3 animate-pulse rounded-2xl bg-brand-100 motion-reduce:animate-none" />
                <div className="h-20 w-3/4 animate-pulse rounded-2xl bg-sand-200 motion-reduce:animate-none" />
              </div>
            ) : renderedTurns.length === 0 && !activeStream ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                  <Sparkles className="h-7 w-7" />
                </div>
                <h3 className="mt-4 font-semibold text-gray-800">Bắt đầu trò chuyện</h3>
                <p className="mt-1 max-w-md text-sm leading-6 text-gray-600">
                  Đặt câu hỏi về dinh dưỡng, cách nấu hoặc gợi ý món ăn. Cuộc trò chuyện sẽ tự động được lưu.
                </p>
                <div className="mt-4 flex max-w-xl flex-wrap justify-center gap-2">
                  {SAMPLE_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      onClick={() => send(question)}
                      disabled={enabled === false || streaming || conversations.length >= MAX_CONVERSATIONS}
                      className="rounded-full border border-sand-200 bg-white px-3 py-1.5 text-xs text-gray-700 transition-colors hover:border-brand-200 hover:bg-brand-50 hover:text-brand-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              renderedTurns.map((turn) => (
                <TurnMessages
                  key={turn.id}
                  turn={turn}
                  isLatest={turn.id === retryTurnId}
                  retrying={retrying}
                  streaming={activeStream?.mode === "retry" && activeStream.turnId === turn.id}
                  streamingContent={activeStream?.mode === "retry" && activeStream.turnId === turn.id ? activeStream.content : null}
                  onRetry={retryLatest}
                />
              ))
            )}

            {activeStream?.mode === "chat" && (
              <>
                <MessageBubble role="user" content={activeStream.question} />
                <MessageBubble role="assistant" content={activeStream.content} streaming />
              </>
            )}
          </div>

          <div className="border-t border-sand-200 bg-white p-3">
            {atTurnLimit && (
              <p className="mb-2 text-xs font-medium text-accent-700">
                Cuộc hội thoại đã đạt 20 câu. Hãy bắt đầu cuộc mới.
              </p>
            )}
            {lastTurn?.status === "failed" && (
              <p className="mb-2 text-xs font-medium text-red-700">
                Hãy retry câu hỏi gần nhất trước khi tiếp tục.
              </p>
            )}
            {streaming && <p className="sr-only" role="status">Menuto đang trả lời.</p>}
            <form onSubmit={onSubmit} className="flex items-center gap-2">
              <label htmlFor="assistant-message" className="sr-only">Nhập câu hỏi</label>
              <input
                id="assistant-message"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder={enabled === false ? "AI chưa được kích hoạt" : "Nhập câu hỏi của bạn..."}
                disabled={composerDisabled}
                maxLength={4000}
                className="min-w-0 flex-1 rounded-xl border border-sand-300 bg-white px-4 py-2.5 text-sm text-gray-800 placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:cursor-not-allowed disabled:bg-sand-100"
              />
              <button
                type="submit"
                disabled={composerDisabled || !input.trim()}
                className="inline-flex items-center justify-center rounded-xl bg-brand-600 p-2.5 text-white transition-colors hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label="Gửi"
              >
                <Send className="h-5 w-5" />
              </button>
            </form>
          </div>
        </section>
      </div>

      {historyOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => setHistoryOpen(false)}
            aria-label="Đóng danh sách cuộc trò chuyện"
          />
          <div
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Các cuộc trò chuyện"
            className="absolute inset-y-0 left-0 flex w-[min(88vw,22rem)] flex-col bg-white shadow-xl"
          >
            <div className="flex items-center justify-between border-b border-sand-200 px-4 py-3">
              <div>
                <h2 className="font-semibold text-gray-800">Cuộc trò chuyện</h2>
                <p className="text-xs text-gray-600">{conversations.length}/10 cuộc đã lưu</p>
              </div>
              <button
                ref={closeDrawerRef}
                type="button"
                onClick={() => {
                  setHistoryOpen(false);
                  historyButtonRef.current?.focus();
                }}
                className="rounded-lg p-2 text-gray-600 hover:bg-sand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
                aria-label="Đóng"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="min-h-0 flex-1">
              <ConversationRail
                conversations={conversations}
                selectedId={selectedId}
                loading={historyLoading}
                deletingId={deletingId}
                disabled={streaming}
                onSelect={selectConversation}
                onNew={startNewConversation}
                onDelete={setConfirmingDeleteId}
              />
            </div>
          </div>
        </div>
      )}
      <ConfirmDialog
        open={confirmingDeleteId !== null}
        onClose={() => setConfirmingDeleteId(null)}
        onConfirm={() => confirmingDeleteId !== null && deleteConversation(confirmingDeleteId)}
        loading={deletingId === confirmingDeleteId}
        title="Xóa cuộc trò chuyện"
        message={`Xóa cuộc trò chuyện “${conversations.find((item) => item.id === confirmingDeleteId)?.title || "này"}”?`}
        confirmLabel="Xóa"
      />
    </div>
  );
}
