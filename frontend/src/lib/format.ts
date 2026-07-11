// Ham dinh dang hien thi.

export const formatVND = (v: number | null | undefined): string => {
  if (v === null || v === undefined) return "—";
  return new Intl.NumberFormat("vi-VN").format(Math.round(v)) + "đ";
};

export const formatNumber = (v: number | null | undefined, digits = 0): string => {
  if (v === null || v === undefined) return "—";
  return new Intl.NumberFormat("vi-VN", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  }).format(v);
};

export const formatKcal = (v: number | null | undefined): string =>
  v === null || v === undefined ? "—" : `${formatNumber(v)} kcal`;

export const formatGram = (v: number | null | undefined): string =>
  v === null || v === undefined ? "—" : `${formatNumber(v, 1)}g`;

export const todayISO = (): string => new Date().toISOString().slice(0, 10);

export const formatDate = (iso: string | null | undefined): string => {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
};

export const formatDateRange = (start: string | null, end: string | null): string => {
  if (!start) return "—";
  if (!end || end === start) return formatDate(start);
  return `${formatDate(start)} – ${formatDate(end)}`;
};
