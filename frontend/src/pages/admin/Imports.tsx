import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle, CheckCircle2, Download, FileSpreadsheet, FileUp, UploadCloud,
} from "lucide-react";
import toast from "react-hot-toast";
import { adminApi } from "../../api/adminApi";
import { AdminEmptyState, AdminErrorState, AdminTableSkeleton } from "../../components/admin/AdminStates";
import { AdminPagination } from "../../components/admin/AdminPagination";
import { Badge, Button, Card, Modal, PageHeader, SelectField } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { formatDate } from "../../lib/format";
import type { ImportConflict, ImportJob, ImportPreview } from "../../types/admin";

const LIMIT = 20;

const MATCH_LABELS: Record<ImportConflict["match_by"], string> = {
  id: "ID",
  code: "mã",
  name: "tên",
};

export function AdminImports() {
  const fileRef = useRef<HTMLInputElement>(null);
  const selectAllRef = useRef<HTMLInputElement>(null);
  const [entityType, setEntityType] = useState<"ingredients" | "dishes">("ingredients");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [committing, setCommitting] = useState(false);
  const [downloadFormat, setDownloadFormat] = useState<"csv" | "xlsx" | null>(null);
  const [replaceRows, setReplaceRows] = useState<number[]>([]);
  const [conflictDialogOpen, setConflictDialogOpen] = useState(false);
  const [items, setItems] = useState<ImportJob[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const conflicts = preview?.conflicts ?? [];
  const selectedCount = conflicts.filter((conflict) => replaceRows.includes(conflict.row)).length;
  const allSelected = conflicts.length > 0 && selectedCount === conflicts.length;

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = selectedCount > 0 && !allSelected;
    }
  }, [allSelected, selectedCount]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const page = await adminApi.importJobs({ limit: LIMIT, offset });
      setItems(page.items);
      setTotal(page.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không thể tải lịch sử import.");
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    void load();
  }, [load]);

  const downloadTemplate = async (format: "csv" | "xlsx") => {
    setDownloadFormat(format);
    try {
      const blob = await adminApi.downloadTemplate(entityType, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `smart-menu-${entityType}-template.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast.success("Đã tải file mẫu.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể tải file mẫu.");
    } finally {
      setDownloadFormat(null);
    }
  };

  const previewFile = async () => {
    if (!file) return;
    setLoadingPreview(true);
    setPreview(null);
    setReplaceRows([]);
    setConflictDialogOpen(false);
    try {
      const result = await adminApi.previewImport(entityType, file);
      setPreview(result);
      if (!result.can_commit) {
        toast.error("File có lỗi; hãy sửa rồi kiểm tra lại.");
      } else if (result.conflicts.length > 0) {
        toast("Chọn các bản ghi được phép thay thế trước khi import.", { icon: "⚠️" });
        setConflictDialogOpen(true);
      } else {
        toast.success("File hợp lệ, sẵn sàng import.");
      }
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể đọc file import.");
    } finally {
      setLoadingPreview(false);
    }
  };

  const commit = async (rowsToReplace: number[] = replaceRows) => {
    if (!preview?.can_commit) return;
    setCommitting(true);
    try {
      const result = await adminApi.commitImport(preview.job_id, rowsToReplace);
      toast.success(`Đã import: thêm ${result.created}, cập nhật ${result.updated}, bỏ qua ${result.skipped}.`);
      setConflictDialogOpen(false);
      setPreview(null);
      setFile(null);
      setReplaceRows([]);
      if (fileRef.current) fileRef.current.value = "";
      await load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể commit import.");
    } finally {
      setCommitting(false);
    }
  };

  const toggleReplaceRow = (row: number) => {
    setReplaceRows((current) => (
      current.includes(row) ? current.filter((item) => item !== row) : [...current, row]
    ));
  };

  const toggleAll = () => {
    setReplaceRows(allSelected ? [] : conflicts.map((conflict) => conflict.row));
  };

  const startCommit = () => {
    if (!preview?.can_commit) return;
    if (conflicts.length > 0) {
      setConflictDialogOpen(true);
      return;
    }
    void commit([]);
  };

  return (
    <div>
      <PageHeader
        title="Import dữ liệu"
        description="Dùng file mẫu để kiểm tra dữ liệu trước, rồi quyết định từng bản ghi trùng trước khi ghi vào hệ thống."
        actions={(
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void downloadTemplate("xlsx")}
              loading={downloadFormat === "xlsx"}
            >
              <Download className="h-4 w-4" /> Tải mẫu XLSX
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => void downloadTemplate("csv")}
              loading={downloadFormat === "csv"}
            >
              CSV
            </Button>
          </div>
        )}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(340px,0.85fr)]">
        <section className="rounded-2xl border border-sand-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
              <UploadCloud className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h2 className="font-semibold text-gray-900">Tạo phiên import</h2>
              <p className="mt-0.5 text-sm text-gray-600">Preview không thay đổi dữ liệu đang dùng.</p>
            </div>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Loại dữ liệu"
              value={entityType}
              options={[
                { value: "ingredients", label: "Nguyên liệu" },
                { value: "dishes", label: "Món ăn (món thành phần)" },
              ]}
              onChange={(event) => {
                setEntityType(event.target.value as "ingredients" | "dishes");
                setPreview(null);
                setReplaceRows([]);
              }}
            />
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700" htmlFor="import-file">
                File CSV hoặc XLSX
              </label>
              <input
                ref={fileRef}
                id="import-file"
                type="file"
                accept=".csv,.xlsx,.xlsm"
                onChange={(event) => {
                  setFile(event.target.files?.[0] || null);
                  setPreview(null);
                  setReplaceRows([]);
                }}
                className="block min-h-11 w-full rounded-xl border border-sand-200 bg-white px-3 py-2 text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-sand-100 file:px-2 file:py-1 file:text-sm file:font-medium file:text-gray-700"
              />
            </div>
          </div>

          <Button className="mt-5" onClick={() => void previewFile()} loading={loadingPreview} disabled={!file}>
            <FileUp className="h-4 w-4" /> Kiểm tra file
          </Button>

          <details className="mt-5 rounded-xl bg-sand-50 px-4 py-3 text-sm text-gray-700">
            <summary className="cursor-pointer font-semibold text-gray-900">Quy tắc file mẫu</summary>
            <div className="mt-3 space-y-2 leading-6">
              <p><strong>id</strong> xác định chính xác bản ghi đang có; để trống khi tạo mới.</p>
              <p><strong>code</strong> là mã riêng, duy nhất. Nếu để trống khi replace, mã hiện có được giữ lại.</p>
              <p>Nếu không có id/code, hệ thống dùng tên chuẩn hóa để phát hiện bản ghi trùng.</p>
              <p>Import nguyên liệu trước, sau đó mới import món ăn để kiểm tra thành phần chính xác.</p>
            </div>
          </details>
        </section>

        <aside className="rounded-2xl border border-sand-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-gray-900">Preview & xác nhận</h2>
          {!preview ? (
            <div className="mt-5 rounded-xl bg-sand-50 p-5 text-center text-sm text-gray-600">
              <FileSpreadsheet className="mx-auto mb-3 h-6 w-6 text-gray-500" aria-hidden="true" />
              Chọn file và kiểm tra để xem dữ liệu hợp lệ, lỗi và bản ghi trùng.
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                <PreviewMetric label="Tổng dòng" value={preview.total_rows} />
                <PreviewMetric label="Hợp lệ" value={preview.valid_rows} className="bg-brand-50 text-brand-900" />
                <PreviewMetric label="Trùng" value={conflicts.length} className="bg-amber-50 text-amber-900" />
                <PreviewMetric label="Lỗi" value={preview.errors.length} className="bg-red-50 text-red-900" />
              </div>

              {preview.errors.length > 0 && (
                <IssueList title="Cần sửa trước khi import" items={preview.errors} tone="error" />
              )}
              {preview.warnings.length > 0 && (
                <IssueList title="Cảnh báo" items={preview.warnings} tone="warning" />
              )}
              {conflicts.length > 0 && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">
                  <div className="flex gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                    <div>
                      <p className="font-semibold">{conflicts.length} bản ghi trùng cần quyết định</p>
                      <p className="mt-1">Mặc định chúng sẽ bị bỏ qua. Chỉ chọn các dòng bạn cho phép thay thế.</p>
                    </div>
                  </div>
                  <Button variant="secondary" size="sm" className="mt-3" onClick={() => setConflictDialogOpen(true)}>
                    Xem danh sách trùng
                  </Button>
                </div>
              )}

              <Button className="w-full" onClick={startCommit} loading={committing} disabled={!preview.can_commit}>
                <CheckCircle2 className="h-4 w-4" />
                {conflicts.length > 0 ? "Chọn thay thế và import" : `Import ${preview.valid_rows} dòng hợp lệ`}
              </Button>
            </div>
          )}
        </aside>
      </div>

      <section className="mt-6">
        <h2 className="mb-3 font-semibold text-gray-900">Lịch sử import</h2>
        <Card bodyClassName="p-0">
          {loading ? <AdminTableSkeleton rows={4} /> : error ? <AdminErrorState message={error} onRetry={load} /> : items.length === 0 ? (
            <AdminEmptyState icon={FileSpreadsheet} title="Chưa có phiên import" description="Các phiên import đã preview hoặc commit sẽ xuất hiện tại đây." />
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-[760px] w-full text-left text-sm">
                <thead className="bg-sand-50 text-xs text-gray-600">
                  <tr className="border-b border-sand-200">
                    <th className="px-5 py-3 font-semibold">File</th>
                    <th className="px-5 py-3 font-semibold">Loại</th>
                    <th className="px-5 py-3 font-semibold">Kết quả</th>
                    <th className="px-5 py-3 font-semibold">Thời gian</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-sand-100">
                  {items.map((item) => <ImportJobRow key={item.id} item={item} />)}
                </tbody>
              </table>
            </div>
          )}
          {!loading && !error && <AdminPagination offset={offset} limit={LIMIT} total={total} onChange={setOffset} />}
        </Card>
      </section>

      <Modal
        open={conflictDialogOpen}
        onClose={() => !committing && setConflictDialogOpen(false)}
        title={`Quyết định ${conflicts.length} bản ghi trùng`}
        size="lg"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setConflictDialogOpen(false)} disabled={committing}>Quay lại</Button>
            <Button onClick={() => void commit(replaceRows)} loading={committing}>
              {selectedCount > 0 ? `Thay thế ${selectedCount} và import` : "Bỏ qua bản ghi trùng và import"}
            </Button>
          </>
        )}
      >
        <p className="text-sm leading-6 text-gray-600">
          Chọn từng dòng được phép thay thế. Những dòng không chọn sẽ được bỏ qua; dữ liệu mới không trùng vẫn được import.
        </p>
        <label className="mt-4 flex min-h-11 items-center gap-3 rounded-xl border border-sand-200 bg-sand-50 px-3 text-sm font-semibold text-gray-900">
          <input
            ref={selectAllRef}
            type="checkbox"
            checked={allSelected}
            onChange={toggleAll}
            className="h-4 w-4 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
          />
          Chọn tất cả để thay thế
        </label>
        <div className="mt-3 divide-y divide-sand-100 overflow-hidden rounded-xl border border-sand-200">
          {conflicts.map((conflict) => {
            const checked = replaceRows.includes(conflict.row);
            return (
              <label key={conflict.row} className="flex cursor-pointer gap-3 px-4 py-3 transition hover:bg-sand-50">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleReplaceRow(conflict.row)}
                  className="mt-1 h-4 w-4 shrink-0 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
                />
                <span className="min-w-0 text-sm">
                  <span className="flex flex-wrap items-center gap-x-2 gap-y-1 font-semibold text-gray-900">
                    <span>Dòng {conflict.row}</span>
                    <Badge className="bg-amber-100 text-amber-900">Trùng theo {MATCH_LABELS[conflict.match_by]}</Badge>
                  </span>
                  <span className="mt-1 block text-gray-700">
                    Hiện có: #{conflict.existing.id} · {conflict.existing.code ?? "Không có mã"} · {conflict.existing.name}
                  </span>
                  <span className="mt-1 block text-gray-600">
                    Trong file: {conflict.incoming.id ? `#${conflict.incoming.id} · ` : ""}{conflict.incoming.code ?? "Không có mã"} · {conflict.incoming.name}
                  </span>
                </span>
              </label>
            );
          })}
        </div>
      </Modal>
    </div>
  );
}

function PreviewMetric({ label, value, className = "" }: { label: string; value: number; className?: string }) {
  return (
    <div className={`rounded-xl bg-sand-50 p-3 ${className}`}>
      <p className="text-xs text-current/75">{label}</p>
      <p className="mt-1 font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function IssueList({ title, items, tone }: {
  title: string;
  items: Array<{ row: number; message: string }>;
  tone: "error" | "warning";
}) {
  const toneClass = tone === "error" ? "border-red-200 bg-red-50 text-red-900" : "border-amber-200 bg-amber-50 text-amber-900";
  return (
    <div className={`rounded-xl border p-3 text-sm ${toneClass}`}>
      <p className="font-semibold">{title}</p>
      <ul className="mt-2 max-h-28 space-y-1 overflow-y-auto">
        {items.map((item, index) => <li key={`${item.row}-${index}`}>Dòng {item.row}: {item.message}</li>)}
      </ul>
    </div>
  );
}

function ImportJobRow({ item }: { item: ImportJob }) {
  const statusClass = item.status === "committed"
    ? "bg-brand-50 text-brand-800"
    : item.status === "invalid"
      ? "bg-red-50 text-red-800"
      : "bg-amber-50 text-amber-800";
  const statusLabel = item.status === "committed" ? "Đã commit" : item.status === "invalid" ? "Có lỗi" : "Đã kiểm tra";
  return (
    <tr>
      <td className="px-5 py-3.5 font-medium text-gray-900">{item.filename}</td>
      <td className="px-5 py-3.5 text-gray-600">{item.entity_type === "ingredients" ? "Nguyên liệu" : "Món ăn (món thành phần)"}</td>
      <td className="px-5 py-3.5">
        <Badge className={statusClass}>{statusLabel}</Badge>
        <p className="mt-1 text-xs text-gray-600">{item.valid_rows}/{item.total_rows} hợp lệ · {item.error_count} lỗi</p>
      </td>
      <td className="px-5 py-3.5 text-gray-600">{formatDate(item.created_at)}</td>
    </tr>
  );
}
