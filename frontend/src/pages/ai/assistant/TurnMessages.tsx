import { ExternalLink, Leaf, RefreshCw, ShieldCheck, User } from "lucide-react";
import type { ReactNode } from "react";
import type { ConversationTurn } from "../../../api/aiApi";
import { ChatMarkdown } from "../../../components/domain/ChatMarkdown";
import { Spinner } from "../../../components/ui";


export function TurnMessages({
  turn,
  isLatest,
  retrying,
  streaming,
  streamingContent,
  onRetry,
}: {
  turn: ConversationTurn;
  isLatest: boolean;
  retrying: boolean;
  streaming: boolean;
  streamingContent: string | null;
  onRetry: () => void;
}) {
  const content = streaming && streamingContent ? streamingContent : turn.assistant_content;
  return (
    <>
      <MessageBubble role="user" content={turn.user_content} />
      {content && (
        <MessageBubble
          role="assistant"
          content={content}
          streaming={streaming}
          action={
            isLatest && !streaming && turn.status !== "failed" ? (
              <button
                type="button"
                onClick={onRetry}
                disabled={retrying || turn.status === "pending"}
                className="mt-2 inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-brand-800 hover:bg-brand-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 disabled:cursor-wait disabled:opacity-60"
                aria-label="Tạo lại câu trả lời cho câu hỏi gần nhất"
              >
                {retrying ? <Spinner className="h-3.5 w-3.5" /> : <RefreshCw className="h-3.5 w-3.5" />}
                Thử lại
              </button>
            ) : undefined
          }
        />
      )}
      {!streaming && turn.status === "completed" && (turn.personalization_used || turn.citations.length > 0) && (
        <div className="ml-10 max-w-[78%] space-y-2 text-xs text-gray-600">
          {turn.personalization_used && (
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-1 text-brand-800">
              <ShieldCheck className="h-3.5 w-3.5" /> Đã dùng hồ sơ của bạn ở chế độ chỉ đọc
            </span>
          )}
          {turn.citations.length > 0 && (
            <div className="rounded-xl border border-sand-200 bg-white px-3 py-2">
              <p className="mb-1 font-semibold text-gray-700">Nguồn tham khảo</p>
              <ul className="space-y-1">
                {turn.citations.map((citation) => (
                  <li key={citation.url}>
                    <a className="inline-flex items-start gap-1 text-brand-700 hover:underline" href={citation.url} target="_blank" rel="noreferrer">
                      {citation.title}<ExternalLink className="mt-0.5 h-3 w-3 shrink-0" />
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      {streaming && !content && (
        <MessageBubble role="assistant" content="" streaming />
      )}
      {streaming && !streamingContent && turn.assistant_content && (
        <div className="ml-10 flex items-center gap-2 text-sm text-gray-600" role="status">
          <Spinner className="h-4 w-4" /> Menuto đang tạo lại câu trả lời...
        </div>
      )}
      {turn.status === "failed" && (
        <div className="ml-10 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
          <p>{turn.assistant_content ? "Menuto chưa thể tạo lại câu trả lời; nội dung cũ được giữ lại." : "Menuto chưa trả lời được câu hỏi này."}</p>
          {isLatest && (
            <button
              type="button"
              onClick={onRetry}
              disabled={retrying}
              className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-white px-2.5 py-1.5 text-xs font-medium text-red-800 shadow-sm hover:bg-red-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:cursor-wait disabled:opacity-60"
            >
              {retrying ? <Spinner className="h-3.5 w-3.5" /> : <RefreshCw className="h-3.5 w-3.5" />}
              Thử lại câu hỏi
            </button>
          )}
        </div>
      )}
      {turn.status === "pending" && !streaming && (
        <div className="flex items-center gap-2 text-sm text-gray-600" role="status">
          <Spinner className="h-4 w-4" /> Menuto đang trả lời...
        </div>
      )}
    </>
  );
}

export function MessageBubble({
  role,
  content,
  action,
  streaming = false,
}: {
  role: "user" | "assistant";
  content: string;
  action?: ReactNode;
  streaming?: boolean;
}) {
  const isUser = role === "user";
  return (
    <div className={`flex items-start gap-2.5 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-sand-200 text-gray-700" : "bg-brand-100 text-brand-700"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Leaf className="h-4 w-4" />}
      </div>
      <div
        className={`min-w-0 max-w-[84%] rounded-2xl px-4 py-2.5 text-sm leading-6 sm:max-w-[78%] ${
          isUser ? "bg-brand-600 text-white" : "bg-sand-100 text-gray-800"
        }`}
      >
        {content ? (
          isUser ? (
            <p className="whitespace-pre-wrap break-words">{content}</p>
          ) : (
            <ChatMarkdown content={content} streaming={streaming} />
          )
        ) : streaming ? (
          <span className="inline-flex items-center gap-2 text-gray-600" role="status">
            <Spinner className="h-4 w-4" /> Menuto đang trả lời...
          </span>
        ) : null}
        {streaming && content && <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded-full bg-brand-500 align-[-2px] motion-reduce:animate-none" aria-hidden="true" />}
        {action}
      </div>
    </div>
  );
}
