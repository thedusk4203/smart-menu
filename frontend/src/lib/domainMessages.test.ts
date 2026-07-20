import { describe, expect, it } from "vitest";

import { isUserVisiblePlanNotice } from "./domainMessages";


describe("plan notice visibility", () => {
  it.each([
    "SOLVER_TIMEOUT_BEST_EFFORT",
    "BUDGET_SEARCH_TIMEOUT_RECOVERED",
    "PANTRY_ASSUMED_AVAILABLE",
  ])("hides internal informational notice %s", (code) => {
    expect(isUserVisiblePlanNotice({ code })).toBe(false);
  });

  it("hides legacy text but keeps actionable warnings", () => {
    expect(isUserVisiblePlanNotice("Đã trả nghiệm hợp lệ tốt nhất từ các pha hoàn tất.")).toBe(false);
    expect(isUserVisiblePlanNotice("Nguyên liệu pantry được giả định có sẵn và không tính vào ngân sách.")).toBe(false);
    expect(isUserVisiblePlanNotice({ code: "MISSING_STORAGE_RULE_SAME_DAY_ONLY" })).toBe(true);
    expect(isUserVisiblePlanNotice({ code: "BUDGET_BELOW_MINIMUM" })).toBe(true);
  });
});
