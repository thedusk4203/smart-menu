import { Button } from "./Button";
import { Modal } from "./Modal";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  onClose: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({ open, title, message, confirmLabel = "Xác nhận", cancelLabel = "Hủy", loading, onClose, onConfirm }: ConfirmDialogProps) {
  return <Modal open={open} onClose={onClose} title={title} size="sm" footer={<><Button variant="ghost" onClick={onClose} disabled={loading}>{cancelLabel}</Button><Button variant="danger" onClick={onConfirm} loading={loading}>{confirmLabel}</Button></>}><p className="text-sm leading-6 text-gray-700">{message}</p></Modal>;
}
