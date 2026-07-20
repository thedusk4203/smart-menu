import { History, Plus, Trash2 } from "lucide-react";
import type { ConversationSummary } from "../../../api/aiApi";
import { Spinner } from "../../../components/ui";
import { MAX_CONVERSATIONS } from "./constants";

const formatConversationTime = (value: string) =>
  new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));


interface ConversationRailProps {
  conversations: ConversationSummary[];
  selectedId: number | null;
  loading: boolean;
  deletingId: number | null;
  disabled: boolean;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
}

export function ConversationRail({
  conversations,
  selectedId,
  loading,
  deletingId,
  disabled,
  onSelect,
  onNew,
  onDelete,
}: ConversationRailProps) {
  const atLimit = conversations.length >= MAX_CONVERSATIONS;

  return (
    <div className="flex h-full min-h-0 flex-col bg-sand-50">
      <div className="border-b border-sand-200 p-3">
        <button
          type="button"
          onClick={onNew}
          disabled={atLimit || disabled}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Plus className="h-4 w-4" /> Cuộc trò chuyện mới
        </button>
        {atLimit && (
          <p className="mt-2 text-xs leading-5 text-gray-600">
            Đã đủ 10 cuộc. Hãy xóa một cuộc trước khi tạo mới.
          </p>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2" aria-label="Danh sách cuộc trò chuyện">
        {loading ? (
          <div className="space-y-2 p-1" aria-label="Đang tải lịch sử">
            {[1, 2, 3].map((item) => (
              <div key={item} className="h-20 animate-pulse rounded-xl bg-sand-200 motion-reduce:animate-none" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="px-3 py-10 text-center">
            <History className="mx-auto h-7 w-7 text-gray-500" />
            <p className="mt-3 text-sm font-medium text-gray-700">Chưa có lịch sử</p>
            <p className="mt-1 text-xs leading-5 text-gray-600">
              Cuộc trò chuyện sẽ tự lưu sau câu hỏi đầu tiên.
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((conversation) => {
              const selected = conversation.id === selectedId;
              return (
                <div
                  key={conversation.id}
                  className={`group flex items-start gap-1 rounded-xl border p-1 transition-colors ${
                    selected
                      ? "border-brand-200 bg-brand-50"
                      : "border-transparent hover:border-sand-200 hover:bg-white"
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(conversation.id)}
                    disabled={disabled}
                    className="min-w-0 flex-1 rounded-lg px-2 py-2 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
                    aria-current={selected ? "true" : undefined}
                  >
                    <span className="block truncate text-sm font-medium text-gray-800">
                      {conversation.title}
                    </span>
                    <span className="mt-1 block truncate text-xs text-gray-600">
                      {conversation.last_message_preview || "Chưa có câu trả lời"}
                    </span>
                    <span className="mt-1.5 flex items-center gap-2 text-[11px] text-gray-600">
                      <span>{conversation.turn_count}/20 câu</span>
                      <span aria-hidden="true">·</span>
                      <span>{formatConversationTime(conversation.updated_at)}</span>
                    </span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(conversation.id)}
                    disabled={disabled || deletingId === conversation.id}
                    aria-label={`Xóa cuộc trò chuyện ${conversation.title}`}
                    className="mt-1 rounded-lg p-2 text-red-700 opacity-60 transition hover:bg-red-50 hover:text-red-800 focus:opacity-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400 group-hover:opacity-100 disabled:cursor-wait"
                  >
                    {deletingId === conversation.id ? (
                      <Spinner className="h-4 w-4" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
