import { formatVND } from "./format";

export interface StructuredNotice {
  code: string;
  message?: string;
  details?: Record<string, number | string>;
}

const HIDDEN_USER_NOTICE_CODES = new Set([
  "SOLVER_TIMEOUT_BEST_EFFORT",
  "BUDGET_SEARCH_TIMEOUT_RECOVERED",
  "PANTRY_ASSUMED_AVAILABLE",
]);

const HIDDEN_LEGACY_NOTICE_PATTERNS = [
  /trả nghiệm hợp lệ tốt nhất/i,
  /khôi phục nghiệm.+chi phí mua thực tế/i,
  /pantry được giả định có sẵn/i,
  /phương án hợp lệ tốt nhất.+thời gian cho phép/i,
  /nguyên liệu cơ bản.+đã có sẵn trong bếp/i,
];

export function isUserVisiblePlanNotice(notice: string | StructuredNotice): boolean {
  if (typeof notice === "string") {
    return !HIDDEN_LEGACY_NOTICE_PATTERNS.some((pattern) => pattern.test(notice));
  }
  return !HIDDEN_USER_NOTICE_CODES.has(notice.code);
}

function numberDetail(notice: StructuredNotice, key: string): number | null {
  const value = notice.details?.[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function planNoticeText(notice: string | StructuredNotice): string {
  if (typeof notice === "string") {
    return "Thực đơn có một lưu ý cần kiểm tra trước khi lưu.";
  }
  const currentBudget = numberDetail(notice, "current_budget");
  const minimumBudget = numberDetail(notice, "minimum_required_budget")
    ?? numberDetail(notice, "minimum_feasible_purchase_cost");
  const budgetGap = numberDetail(notice, "budget_gap");
  switch (notice.code) {
    case "BUDGET_BELOW_MINIMUM":
    case "BUDGET_PURCHASE_BLOCK_CONFLICT":
      return minimumBudget != null
        ? `Ngân sách hiện tại${currentBudget != null ? ` là ${formatVND(currentBudget)}` : ""} chưa đủ. Cần ít nhất khoảng ${formatVND(minimumBudget)}${budgetGap != null ? `, còn thiếu ${formatVND(budgetGap)}` : ""}.`
        : "Ngân sách hiện tại chưa đủ cho số ngày và số bữa đã chọn.";
    case "MISSING_BREAKFAST":
      return "Kho món ăn hiện chưa có đủ món sáng với giá và dinh dưỡng hoàn chỉnh.";
    case "MISSING_STAPLE":
      return "Kho món ăn hiện chưa có đủ món tinh bột để ghép thực đơn.";
    case "MISSING_SAVORY":
      return "Kho món ăn hiện chưa có đủ món mặn để ghép thực đơn.";
    case "MISSING_SIDE":
      return "Kho món ăn hiện chưa có đủ món rau hoặc canh để ghép thực đơn.";
    case "MISSING_PURCHASE_RULE":
      return "Một số nguyên liệu chưa có giá hoặc quy cách mua hoàn chỉnh. Smart Menu chưa thể tính đúng chi phí.";
    case "CALORIE_TARGET_UNATTAINABLE":
      return "Mức năng lượng mục tiêu nằm ngoài khoảng mà các món hiện có có thể đáp ứng.";
    case "PROTEIN_TARGET_UNATTAINABLE":
      return "Mục tiêu đạm nằm ngoài khoảng mà các món hiện có có thể đáp ứng.";
    case "FAT_TARGET_UNATTAINABLE":
      return "Mục tiêu chất béo nằm ngoài khoảng mà các món hiện có có thể đáp ứng.";
    case "CARB_TARGET_UNATTAINABLE":
      return "Mục tiêu tinh bột nằm ngoài khoảng mà các món hiện có có thể đáp ứng.";
    case "LIMITED_STAPLE_VARIETY":
      return "Số món tinh bột hiện còn ít nên thực đơn có thể lặp lại nhiều hơn.";
    case "BUDGET_NEAR_MINIMUM":
      return minimumBudget != null
        ? `Ngân sách đang gần mức tối thiểu ${formatVND(minimumBudget)}, nên số phương án phù hợp sẽ ít hơn.`
        : "Ngân sách đang gần mức tối thiểu nên số phương án phù hợp sẽ ít hơn.";
    case "DIVERSITY_RELAXED_FOR_FEASIBILITY":
      return "Smart Menu đã cho phép lặp một số món để giữ ngân sách và dinh dưỡng.";
    case "SOLVER_SEARCH_TIMEOUT":
      return "Smart Menu chưa tìm được phương án phù hợp trong thời gian cho phép. Hãy thử lại hoặc giảm số ngày.";
    case "SOLVER_TIMEOUT_BEST_EFFORT":
      return "Smart Menu đã trả phương án hợp lệ tốt nhất tìm được trong thời gian cho phép.";
    case "BUDGET_SEARCH_TIMEOUT_RECOVERED":
      return "Chi phí mua đã được kiểm tra lại và vẫn nằm trong ngân sách đã chọn.";
    case "NUTRITION_STORAGE_CONFLICT":
      return "Chưa thể đồng thời đáp ứng mục tiêu dinh dưỡng và thời hạn bảo quản. Hãy giảm số ngày hoặc điều chỉnh hồ sơ.";
    case "MISSING_STORAGE_RULE_SAME_DAY_ONLY":
      return "Một số nguyên liệu chưa có thời hạn bảo quản nên được xếp mua và dùng trong cùng ngày.";
    case "PANTRY_ASSUMED_AVAILABLE":
      return "Một số nguyên liệu cơ bản được xem là đã có sẵn trong bếp và chưa được tính vào chi phí mua.";
    case "HARD_CONSTRAINT":
      return "Một điều kiện bắt buộc chưa thể được đáp ứng. Hãy điều chỉnh lựa chọn rồi thử lại.";
    default:
      return "Thực đơn có một lưu ý cần kiểm tra trước khi lưu.";
  }
}
