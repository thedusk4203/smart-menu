// Ham dinh dang hien thi.

export const formatVND = (v: number | null | undefined): string => {
  if (v === null || v === undefined) return "—";
  return new Intl.NumberFormat("vi-VN").format(Math.round(v)) + "đ";
};

/** Chuyển chuỗi người dùng nhập thành số chuẩn để lưu state/payload API. */
export const parseMoneyInput = (value: string, maxFractionDigits = 0): string => {
  const source = value.replace(/[^\d.,]/g, "");
  if (!/\d/.test(source)) return "";

  let integerPart = source;
  let fractionPart = "";
  const lastComma = source.lastIndexOf(",");
  if (maxFractionDigits > 0 && lastComma >= 0) {
    integerPart = source.slice(0, lastComma).replace(/\D/g, "");
    fractionPart = source.slice(lastComma + 1).replace(/\D/g, "").slice(0, maxFractionDigits);
    if (!fractionPart && source.endsWith(",")) {
      const integer = (integerPart.replace(/^0+(?=\d)/, "") || "0");
      return `${integer}.`;
    }
  } else if (maxFractionDigits > 0 && /^\d+\.\d{1,4}$/.test(source) && !/^\d{1,3}(?:\.\d{3})+$/.test(source)) {
    // Chấp nhận số thập phân kiểu 12.5 khi dán từ nguồn dùng dấu chấm.
    [integerPart, fractionPart] = source.split(".");
    fractionPart = fractionPart.slice(0, maxFractionDigits);
  } else {
    integerPart = source.replace(/\D/g, "");
  }

  const integer = (integerPart.replace(/^0+(?=\d)/, "") || "0");
  return fractionPart ? `${integer}.${fractionPart}` : integer;
};

/** Hiển thị chuỗi số chuẩn theo quy ước Việt Nam nhưng không thêm ký hiệu tiền. */
export const formatMoneyInput = (value: string, maxFractionDigits = 0): string => {
  if (!value) return "";
  const [rawInteger, rawFraction = ""] = value.split(".");
  const integer = (rawInteger || "0").replace(/^0+(?=\d)/, "") || "0";
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const fraction = maxFractionDigits > 0 ? rawFraction.slice(0, maxFractionDigits) : "";
  if (maxFractionDigits > 0 && value.endsWith(".")) return `${grouped},`;
  return fraction ? `${grouped},${fraction}` : grouped;
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

export const defaultMealPlanName = (date = new Date()): string => {
  const parts = new Intl.DateTimeFormat("vi-VN", {
    timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit",
    day: "2-digit", month: "2-digit", year: "numeric", hour12: false,
  }).formatToParts(date).reduce<Record<string, string>>((result, part) => ({ ...result, [part.type]: part.value }), {});
  return `Thực đơn ${parts.hour}:${parts.minute} ${parts.day}/${parts.month}/${parts.year}`;
};

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
