import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  Activity, AlertTriangle, Bot, Copy, KeyRound, MessageSquareText, Plus,
  Power, RotateCcw, Save, TestTube2, Trash2,
} from "lucide-react";
import toast from "react-hot-toast";
import { adminApi } from "../../api/adminApi";
import { ApiError } from "../../lib/apiClient";
import {
  Badge, Button, Card, ConfirmDialog, Modal, PageHeader, SelectField,
  Textarea, TextField,
} from "../../components/ui";
import type {
  AIRequestLog, AISystemPrompt, AISystemPromptFeature, LLMProvider,
  LLMProviderType, LLMProviderWrite,
} from "../../types/admin";

const PRESETS: Record<LLMProviderType, string> = {
  openai: "https://api.openai.com/v1",
  deepseek: "https://api.deepseek.com/v1",
  lmstudio: "http://localhost:1234/v1",
  google: "https://generativelanguage.googleapis.com/v1beta/openai",
  custom: "",
};
const EMPTY: LLMProviderWrite = {
  name: "", provider_type: "openai", base_url: PRESETS.openai,
  model: "", api_key: "", timeout_seconds: 60,
};
const PROMPT_OPTIONS: Array<{
  value: AISystemPromptFeature;
  label: string;
  description: string;
  contractSensitive: boolean;
}> = [
  {
    value: "chat",
    label: "Trò chuyện Menuto",
    description: "Điều khiển giọng điệu, phạm vi hỗ trợ và nguyên tắc trả lời trong hội thoại.",
    contractSensitive: false,
  },
  {
    value: "parse_menu",
    label: "Đọc yêu cầu thực đơn",
    description: "Trích xuất số ngày, số bữa, ngân sách và thẻ ưu tiên thành dữ liệu có cấu trúc.",
    contractSensitive: true,
  },
  {
    value: "explain_plan",
    label: "Giải thích thực đơn",
    description: "Tạo phân tích có căn cứ từ số liệu planner đã kiểm tra.",
    contractSensitive: true,
  },
  {
    value: "suggest_swap",
    label: "Gợi ý đổi món",
    description: "Xếp hạng món thay thế từ shortlist và trả về đúng cấu trúc yêu cầu.",
    contractSensitive: true,
  },
];

const emptyPromptDrafts = (): Record<AISystemPromptFeature, string> => ({
  chat: "",
  parse_menu: "",
  explain_plan: "",
  suggest_swap: "",
});

export function AISettings() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [logs, setLogs] = useState<AIRequestLog[]>([]);
  const [prompts, setPrompts] = useState<AISystemPrompt[]>([]);
  const [promptDrafts, setPromptDrafts] = useState(emptyPromptDrafts);
  const [selectedPromptFeature, setSelectedPromptFeature] = useState<AISystemPromptFeature>("chat");
  const [pendingPromptFeature, setPendingPromptFeature] = useState<AISystemPromptFeature | null>(null);
  const [promptResetOpen, setPromptResetOpen] = useState(false);
  const [promptBusy, setPromptBusy] = useState<"save" | "reset" | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<number | "save" | "test" | null>(null);
  const [editing, setEditing] = useState<LLMProvider | null>(null);
  const [form, setForm] = useState<LLMProviderWrite>(EMPTY);
  const [open, setOpen] = useState(false);
  const [logDetail, setLogDetail] = useState<AIRequestLog | null>(null);
  const [testFeedback, setTestFeedback] = useState<{ success: boolean; message: string } | null>(null);

  const changeForm = (changes: Partial<LLMProviderWrite>) => {
    setForm(current => ({ ...current, ...changes }));
    setTestFeedback(null);
  };

  const fetchProvidersAndLogs = useCallback(async () => {
    const [providerData, logData] = await Promise.all([
      adminApi.aiProviders(), adminApi.aiLogs({ limit: 20, offset: 0 }),
    ]);
    setProviders(providerData);
    setLogs(logData.items);
  }, []);

  const fetchPrompts = useCallback(async () => {
    const promptData = await adminApi.aiSystemPrompts();
    setPrompts(promptData);
    const drafts = emptyPromptDrafts();
    promptData.forEach(item => { drafts[item.feature] = item.content; });
    setPromptDrafts(drafts);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([fetchProvidersAndLogs(), fetchPrompts()]);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Không thể tải cấu hình AI.");
    } finally { setLoading(false); }
  }, [fetchPrompts, fetchProvidersAndLogs]);
  useEffect(() => { load(); }, [load]);

  const startCreate = () => { setEditing(null); setForm(EMPTY); setTestFeedback(null); setOpen(true); };
  const startEdit = (item: LLMProvider) => {
    setEditing(item);
    setTestFeedback(null);
    setForm({ name: item.name, provider_type: item.provider_type, base_url: item.base_url,
      model: item.model, api_key: "", timeout_seconds: item.timeout_seconds });
    setOpen(true);
  };
  const persistDraft = async () => editing
    ? adminApi.updateAIProvider(editing.id, form)
    : adminApi.createAIProvider(form);
  const save = async (event: FormEvent) => {
    event.preventDefault(); setBusy("save");
    try {
      await persistDraft();
      toast.success(editing ? "Đã cập nhật draft." : "Đã tạo provider draft.");
      setOpen(false); await fetchProvidersAndLogs();
    } catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể lưu provider."); }
    finally { setBusy(null); }
  };
  const testDraft = async () => {
    const formElement = document.getElementById("ai-provider-form") as HTMLFormElement | null;
    if (!formElement?.reportValidity()) return;
    setBusy("test");
    setTestFeedback(null);
    try {
      const draft = await persistDraft();
      const result = await adminApi.testAIProvider(draft.id);
      const success = result.provider.test_status === "success";
      const message = success
        ? `Kết nối thành công · ${result.provider.structured_output_mode ?? "structured output"}`
        : result.provider.last_test_error ?? "Provider không vượt qua kiểm tra.";
      setEditing(result.provider);
      setForm({ name: result.provider.name, provider_type: result.provider.provider_type,
        base_url: result.provider.base_url, model: result.provider.model, api_key: "",
        timeout_seconds: result.provider.timeout_seconds });
      setTestFeedback({ success, message });
      if (success) toast.success("Provider hoạt động và structured output hợp lệ.");
      else toast.error(message);
      await fetchProvidersAndLogs();
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Không thể test provider.";
      setTestFeedback({ success: false, message });
      toast.error(message);
    } finally { setBusy(null); }
  };
  const action = async (id: number, fn: () => Promise<unknown>, success: string) => {
    setBusy(id);
    try { await fn(); toast.success(success); await fetchProvidersAndLogs(); }
    catch (error) { toast.error(error instanceof ApiError ? error.message : "Thao tác thất bại."); }
    finally { setBusy(null); }
  };
  const testProvider = async (item: LLMProvider) => {
    setBusy(item.id);
    try {
      const result = await adminApi.testAIProvider(item.id);
      if (result.provider.test_status === "success") toast.success("Provider hoạt động và structured output hợp lệ.");
      else toast.error(result.provider.last_test_error ?? "Provider không vượt qua kiểm tra.");
      await fetchProvidersAndLogs();
    } catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể test provider."); }
    finally { setBusy(null); }
  };
  const discoverModels = async (item: LLMProvider) => {
    setBusy(item.id);
    try {
      const models = await adminApi.discoverAIModels(item.id);
      if (!models.length) { toast("Provider không trả danh sách model; bạn vẫn có thể nhập model thủ công."); return; }
      const selected = models.includes(item.model) ? item.model : models[0];
      if (selected && !item.is_active) {
        setEditing(item);
        setForm({ name: item.name, provider_type: item.provider_type, base_url: item.base_url,
          model: selected, api_key: "", timeout_seconds: item.timeout_seconds });
        setOpen(true);
        toast(`Đã chọn ${selected}. Bạn có thể đổi model trong form trước khi lưu.`);
      }
    } catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể tải danh sách model."); }
    finally { setBusy(null); }
  };
  const viewLog = async (id: number) => {
    try { setLogDetail(await adminApi.aiLog(id)); }
    catch (error) { toast.error(error instanceof ApiError ? error.message : "Không thể tải log."); }
  };

  const currentPrompt = prompts.find(item => item.feature === selectedPromptFeature);
  const currentPromptOption = PROMPT_OPTIONS.find(item => item.value === selectedPromptFeature)!;
  const currentPromptDraft = promptDrafts[selectedPromptFeature];
  const promptDirty = currentPrompt != null && currentPromptDraft !== currentPrompt.content;

  const requestPromptFeature = (next: AISystemPromptFeature) => {
    if (next === selectedPromptFeature) return;
    if (promptDirty) setPendingPromptFeature(next);
    else setSelectedPromptFeature(next);
  };
  const discardPromptDraftAndSwitch = () => {
    if (!pendingPromptFeature) return;
    if (currentPrompt) {
      setPromptDrafts(current => ({ ...current, [selectedPromptFeature]: currentPrompt.content }));
    }
    setSelectedPromptFeature(pendingPromptFeature);
    setPendingPromptFeature(null);
  };
  const savePrompt = async () => {
    if (!currentPromptDraft.trim()) {
      toast.error("System prompt không được để trống.");
      return;
    }
    setPromptBusy("save");
    try {
      const updated = await adminApi.updateAISystemPrompt(selectedPromptFeature, currentPromptDraft);
      setPrompts(current => current.map(item => item.feature === updated.feature ? updated : item));
      setPromptDrafts(current => ({ ...current, [updated.feature]: updated.content }));
      toast.success("Đã lưu system prompt. Nội dung mới áp dụng từ request kế tiếp.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Không thể lưu system prompt.");
    } finally { setPromptBusy(null); }
  };
  const resetPrompt = async () => {
    setPromptResetOpen(false);
    setPromptBusy("reset");
    try {
      const reset = await adminApi.resetAISystemPrompt(selectedPromptFeature);
      setPrompts(current => current.map(item => item.feature === reset.feature ? reset : item));
      setPromptDrafts(current => ({ ...current, [reset.feature]: reset.content }));
      toast.success("Đã khôi phục system prompt mặc định.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Không thể khôi phục system prompt.");
    } finally { setPromptBusy(null); }
  };

  return <div>
    <PageHeader title="AI & LLM Provider" description="Cấu hình, kiểm tra và theo dõi provider dùng cho các tính năng AI."
      actions={<Button onClick={startCreate}><Plus className="h-4 w-4" /> Thêm provider</Button>} />
    <div className="mb-6 grid gap-4 lg:grid-cols-2">
      {providers.map((item) => <Card key={item.id} title={<span className="flex items-center gap-2">{item.name}
        {item.is_active && <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs text-brand-700">Đang dùng</span>}</span>}
        icon={<Bot className="h-5 w-5" />}>
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div><dt className="text-gray-500">Provider</dt><dd className="font-medium">{item.provider_type}</dd></div>
          <div><dt className="text-gray-500">Model</dt><dd className="font-medium break-all">{item.model}</dd></div>
          <div><dt className="text-gray-500">API key</dt><dd>{item.masked_api_key ?? "Không có"}</dd></div>
          <div><dt className="text-gray-500">Kiểm tra</dt><dd className={item.test_status === "success" ? "text-brand-700" : item.test_status === "failed" ? "text-red-600" : "text-gray-500"}>{item.test_status}</dd></div>
        </dl>
        {item.last_test_error && <p className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-700">{item.last_test_error}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          {!item.is_active && <Button size="sm" variant="secondary" onClick={() => startEdit(item)}>Sửa</Button>}
          <Button size="sm" variant="secondary" loading={busy === item.id} onClick={() => testProvider(item)}><TestTube2 className="h-4 w-4" /> Test</Button>
          <Button size="sm" variant="secondary" disabled={item.is_active} onClick={() => discoverModels(item)}>Models</Button>
          {!item.is_active && item.test_status === "success" && item.tested_version === item.config_version && <Button size="sm" loading={busy === item.id} onClick={() => action(item.id, () => adminApi.activateAIProvider(item.id), "Đã kích hoạt provider.")}><Power className="h-4 w-4" /> Kích hoạt</Button>}
          {item.is_active && <Button size="sm" variant="secondary" loading={busy === item.id} onClick={() => action(item.id, () => adminApi.deactivateAIProvider(item.id), "Đã tắt AI.")}>Tắt</Button>}
          <Button size="sm" variant="ghost" onClick={() => action(item.id, () => adminApi.cloneAIProvider(item.id), "Đã tạo bản sao draft.")}><Copy className="h-4 w-4" /> Clone</Button>
          {!item.is_active && <Button size="sm" variant="ghost" onClick={() => action(item.id, () => adminApi.deleteAIProvider(item.id), "Đã xóa provider.")}><Trash2 className="h-4 w-4" /></Button>}
        </div>
      </Card>)}
      {!loading && providers.length === 0 && <Card><div className="py-10 text-center text-sm text-gray-500"><KeyRound className="mx-auto mb-3 h-8 w-8" />Chưa có provider do admin quản lý.</div></Card>}
    </div>

    <Card className="mb-6" title="System prompt AI" icon={<MessageSquareText className="h-5 w-5" />}
      action={currentPrompt && <Badge className={currentPrompt.is_custom ? "bg-brand-100 text-brand-800" : "bg-sand-100 text-gray-700"}>{currentPrompt.is_custom ? "Đã tùy chỉnh" : "Mặc định"}</Badge>}>
      <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-sm text-amber-900">
        <div className="flex items-start gap-2.5">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <p>Prompt là cấu hình toàn cục và có hiệu lực từ request kế tiếp. Không nhập API key hoặc dữ liệu cá nhân vào nội dung này.</p>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(220px,0.34fr)_minmax(0,1fr)]">
        <div>
          <SelectField label="Tính năng" value={selectedPromptFeature}
            options={PROMPT_OPTIONS.map(({ value, label }) => ({ value, label }))}
            onChange={event => requestPromptFeature(event.target.value as AISystemPromptFeature)} />
          <p className="mt-2 text-sm leading-6 text-gray-600">{currentPromptOption.description}</p>
          {currentPromptOption.contractSensitive && <p className="mt-3 rounded-xl bg-sand-50 p-3 text-xs leading-5 text-gray-700">Tính năng này phụ thuộc structured output. Hãy giữ nguyên yêu cầu về schema, field và giới hạn dữ liệu.</p>}
          <p className="mt-3 text-xs text-gray-500">
            {currentPrompt?.updated_at
              ? `Cập nhật ${new Date(currentPrompt.updated_at).toLocaleString("vi-VN")}`
              : "Đang dùng nội dung mặc định trong code."}
          </p>
        </div>
        <div>
          <Textarea label="Nội dung system prompt" rows={15} value={currentPromptDraft}
            maxLength={20_000} spellCheck={false} disabled={!currentPrompt || promptBusy !== null}
            onChange={event => setPromptDrafts(current => ({ ...current, [selectedPromptFeature]: event.target.value }))}
            hint={`${new Intl.NumberFormat("vi-VN").format(currentPromptDraft.length)} / 20.000 ký tự`} />
          <div className="mt-3 flex flex-wrap items-center justify-end gap-2">
            <Button variant="secondary" disabled={!currentPrompt?.is_custom || promptBusy !== null}
              onClick={() => setPromptResetOpen(true)}>
              <RotateCcw className="h-4 w-4" /> Khôi phục mặc định
            </Button>
            <Button loading={promptBusy === "save"}
              disabled={!promptDirty || !currentPromptDraft.trim() || promptBusy !== null}
              onClick={savePrompt}>
              <Save className="h-4 w-4" /> Lưu và áp dụng
            </Button>
          </div>
        </div>
      </div>
    </Card>

    <Card title="Nhật ký AI — lưu 30 ngày" icon={<Activity className="h-5 w-5" />} action={<Button size="sm" variant="secondary" onClick={() => action(0, () => adminApi.purgeAILogs(new Date(Date.now() - 30 * 86400000).toISOString()), "Đã dọn log quá hạn.")}>Dọn log quá hạn</Button>}>
      <div className="overflow-x-auto"><table className="min-w-[720px] w-full text-left text-sm"><thead><tr className="border-b border-sand-200 text-gray-500"><th className="pb-2">Thời gian</th><th>Feature</th><th>Model</th><th>Trạng thái</th><th>Latency</th><th /></tr></thead>
        <tbody>{logs.map(log => <tr key={log.id} className="border-b border-sand-100"><td className="py-3">{new Date(log.created_at).toLocaleString("vi-VN")}</td><td>{log.feature}</td><td>{log.model}</td><td>{log.status === "success" ? <span className="text-brand-700">Thành công</span> : <span className="text-red-600">Lỗi</span>}</td><td>{log.latency_ms} ms</td><td><button className="text-brand-700 hover:underline" onClick={() => viewLog(log.id)}>Chi tiết</button></td></tr>)}</tbody></table></div>
    </Card>

    <Modal open={open} onClose={() => setOpen(false)} title={editing ? "Sửa provider draft" : "Thêm LLM provider"}
      footer={<><Button variant="secondary" onClick={() => setOpen(false)}>Hủy</Button><Button type="button" variant="secondary" loading={busy === "test"} disabled={busy !== null && busy !== "test"} onClick={testDraft}><TestTube2 className="h-4 w-4" /> Test kết nối</Button>{testFeedback?.success ? <Button type="button" onClick={() => setOpen(false)}>Xong</Button> : <Button type="submit" form="ai-provider-form" loading={busy === "save"} disabled={busy !== null && busy !== "save"}>Lưu draft</Button>}</>}>
      <form id="ai-provider-form" onSubmit={save} className="space-y-4">
        <TextField label="Tên hiển thị" required value={form.name} onChange={event => changeForm({ name: event.target.value })} />
        <SelectField label="Provider" value={form.provider_type} options={[{value:"openai",label:"OpenAI"},{value:"deepseek",label:"DeepSeek"},{value:"lmstudio",label:"LM Studio"},{value:"google",label:"Google Gemini"},{value:"custom",label:"Custom OpenAI-compatible"}]}
          onChange={event => { const provider_type = event.target.value as LLMProviderType; changeForm({ provider_type, base_url: PRESETS[provider_type] || form.base_url }); }} />
        <TextField label="Base URL" required value={form.base_url} onChange={event => changeForm({ base_url: event.target.value })} />
        <TextField label="Model" required value={form.model} onChange={event => changeForm({ model: event.target.value })} />
        <TextField label="API key" type="password" value={form.api_key ?? ""} onChange={event => changeForm({ api_key: event.target.value })} hint={editing?.has_api_key ? "Để trống để giữ key hiện tại." : "LM Studio local có thể để trống."} />
        <TextField label="Timeout (giây)" type="number" min={1} max={300} value={form.timeout_seconds} onChange={event => changeForm({ timeout_seconds: Number(event.target.value) })} />
        {testFeedback && <div role="status" className={`rounded-xl border px-3.5 py-3 text-sm ${testFeedback.success ? "border-brand-200 bg-brand-50 text-brand-800" : "border-red-200 bg-red-50 text-red-700"}`}>
          <p className="font-medium">{testFeedback.success ? "Kết nối thành công" : "Kiểm tra thất bại"}</p>
          <p className="mt-1 break-words text-xs">{testFeedback.message}</p>
        </div>}
      </form>
    </Modal>
    <Modal open={!!logDetail} onClose={() => setLogDetail(null)} title={`AI log #${logDetail?.id ?? ""}`} size="lg">
      {logDetail && <div className="space-y-4 text-sm"><div className="flex gap-4"><span>{logDetail.feature}</span><span>{logDetail.model}</span><span>{logDetail.latency_ms} ms</span></div><div><p className="mb-1 font-semibold">Request</p><pre className="max-h-64 overflow-auto rounded-xl bg-gray-950 p-3 text-xs text-gray-100">{JSON.stringify(logDetail.request_data, null, 2)}</pre></div><div><p className="mb-1 font-semibold">Response</p><pre className="max-h-64 overflow-auto rounded-xl bg-gray-950 p-3 text-xs text-gray-100">{JSON.stringify(logDetail.response_data, null, 2)}</pre></div></div>}
    </Modal>
    <ConfirmDialog open={pendingPromptFeature !== null} onClose={() => setPendingPromptFeature(null)}
      onConfirm={discardPromptDraftAndSwitch} title="Bỏ thay đổi chưa lưu?"
      message="Nội dung prompt đang chỉnh chưa được lưu. Nếu chuyển tính năng, các thay đổi này sẽ bị bỏ."
      confirmLabel="Bỏ thay đổi" />
    <ConfirmDialog open={promptResetOpen} onClose={() => setPromptResetOpen(false)}
      onConfirm={resetPrompt} loading={promptBusy === "reset"} title="Khôi phục system prompt mặc định"
      message={`Bỏ nội dung tùy chỉnh của “${currentPromptOption.label}” và dùng lại prompt mặc định trong code?`}
      confirmLabel="Khôi phục mặc định" />
  </div>;
}
