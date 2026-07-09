import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Sparkles, Send, Wrench, User, Leaf } from "lucide-react";
import { aiApi } from "../../api/aiApi";
import type { ChatMessage } from "../../api/aiApi";
import { PageHeader, Spinner } from "../../components/ui";

const SAMPLE_QUESTIONS = [
  "Gợi ý món ăn giàu đạm, ít calo?",
  "Làm sao để ăn đủ chất khi giảm cân?",
  "Thực đơn 1500 kcal cho một ngày?",
  "Nên ăn bao nhiêu tinh bột mỗi ngày?",
];

const DEV_REPLY = "Xin lỗi, tính năng Trợ lý AI đang được phát triển và sẽ sớm ra mắt.";

export function Assistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text: string) => {
    const content = text.trim();
    if (!content || sending) return;
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInput("");
    setSending(true);
    try {
      const res = await aiApi.chat(content);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      // Backend AI chua bat -> tra loi mem.
      setMessages((prev) => [...prev, { role: "assistant", content: DEV_REPLY }]);
    } finally {
      setSending(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div>
      <PageHeader title="Trợ lý AI" description="Hỏi đáp về dinh dưỡng và gợi ý món ăn." />

      <div className="mb-4 flex items-start gap-2.5 rounded-2xl border border-accent-200 bg-accent-50 px-4 py-3 text-sm text-accent-800">
        <Wrench className="mt-0.5 h-4 w-4 shrink-0" />
        <span>
          Tính năng Trợ lý AI đang trong quá trình phát triển. Giao diện đã sẵn sàng và sẽ hoạt động
          đầy đủ khi backend được kích hoạt.
        </span>
      </div>

      <div className="flex h-[62vh] flex-col rounded-2xl border border-sand-200 bg-white shadow-sm">
        <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-5">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-100 text-brand-600">
                <Sparkles className="h-7 w-7" />
              </div>
              <h3 className="mt-4 font-semibold text-gray-800">Bắt đầu trò chuyện</h3>
              <p className="mt-1 max-w-sm text-sm text-gray-500">
                Đặt câu hỏi về dinh dưỡng, calo hoặc gợi ý món ăn. Thử một trong các câu mẫu:
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {SAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    className="rounded-full border border-sand-200 bg-white px-3 py-1.5 text-xs text-gray-600 transition hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex items-start gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    msg.role === "user" ? "bg-sand-200 text-gray-600" : "bg-brand-100 text-brand-600"
                  }`}
                >
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <Leaf className="h-4 w-4" />}
                </div>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                    msg.role === "user"
                      ? "bg-brand-600 text-white"
                      : "bg-sand-100 text-gray-800"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))
          )}
          {sending && (
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Spinner className="h-4 w-4" /> Đang trả lời...
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-sand-200 p-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Nhập câu hỏi của bạn..."
            className="flex-1 rounded-xl border border-sand-200 bg-white px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="inline-flex items-center justify-center rounded-xl bg-brand-600 p-2.5 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Gửi"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
