import { useState } from "react";
import { Download, FileSpreadsheet } from "lucide-react";
import toast from "react-hot-toast";
import { adminApi } from "../../api/adminApi";
import { ApiError } from "../../lib/apiClient";
import { Button, Modal } from "../ui";

type EntityType = "ingredients" | "dishes";
type Scope = "filtered" | "all";

interface AdminExportDialogProps {
  entityType: EntityType;
  filteredParams: Record<string, unknown>;
  filteredTotal: number;
}

export function AdminExportDialog({ entityType, filteredParams, filteredTotal }: AdminExportDialogProps) {
  const [open, setOpen] = useState(false);
  const [scope, setScope] = useState<Scope>("filtered");
  const [downloading, setDownloading] = useState<"csv" | "xlsx" | null>(null);
  const entityLabel = entityType === "ingredients" ? "nguyên liệu" : "món ăn (món thành phần)";

  const download = async (format: "csv" | "xlsx") => {
    setDownloading(format);
    try {
      const params = scope === "filtered" ? filteredParams : {};
      const result = entityType === "ingredients"
        ? await adminApi.exportIngredients(format, params)
        : await adminApi.exportDishes(format, params);
      const url = URL.createObjectURL(result.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = result.filename || `smart-menu-${entityType}-export.${format}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setOpen(false);
      toast.success("Đã tải file export.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể export dữ liệu.");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <>
      <Button variant="secondary" onClick={() => setOpen(true)}>
        <Download className="h-4 w-4" /> Export dữ liệu
      </Button>
      <Modal
        open={open}
        onClose={() => !downloading && setOpen(false)}
        title={`Export ${entityLabel}`}
        size="sm"
        footer={(
          <>
            <Button variant="ghost" onClick={() => setOpen(false)} disabled={!!downloading}>Hủy</Button>
            <Button variant="secondary" onClick={() => void download("csv")} loading={downloading === "csv"} disabled={!!downloading && downloading !== "csv"}>CSV</Button>
            <Button onClick={() => void download("xlsx")} loading={downloading === "xlsx"} disabled={!!downloading && downloading !== "xlsx"}>
              <FileSpreadsheet className="h-4 w-4" /> Tải XLSX
            </Button>
          </>
        )}
      >
        <p className="text-sm leading-6 text-gray-600">File dùng đúng cấu trúc import để bạn có thể chỉnh sửa rồi import lại.</p>
        <fieldset className="mt-4 space-y-2">
          <legend className="text-sm font-semibold text-gray-900">Phạm vi dữ liệu</legend>
          <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-sand-200 px-3 text-sm text-gray-800">
            <input type="radio" name={`export-scope-${entityType}`} checked={scope === "filtered"} onChange={() => setScope("filtered")} className="h-4 w-4 border-sand-300 text-brand-600 focus:ring-brand-400" />
            Theo bộ lọc hiện tại ({filteredTotal} kết quả)
          </label>
          <label className="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl border border-sand-200 px-3 text-sm text-gray-800">
            <input type="radio" name={`export-scope-${entityType}`} checked={scope === "all"} onChange={() => setScope("all")} className="h-4 w-4 border-sand-300 text-brand-600 focus:ring-brand-400" />
            Toàn bộ dữ liệu
          </label>
        </fieldset>
      </Modal>
    </>
  );
}
