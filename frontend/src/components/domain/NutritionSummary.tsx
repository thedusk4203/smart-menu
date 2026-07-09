import { AlertTriangle, Flame, Activity, Beef, Droplet, Wheat, Scale } from "lucide-react";
import { StatCard } from "../ui";
import { formatKcal, formatGram, formatNumber } from "../../lib/format";
import type { NutritionTarget } from "../../types";

function bmiLabel(bmi: number): string {
  if (bmi < 18.5) return "Thiếu cân";
  if (bmi < 23) return "Bình thường";
  if (bmi < 25) return "Thừa cân";
  return "Béo phì";
}

export function NutritionSummary({ target }: { target: NutritionTarget }) {
  return (
    <div className="space-y-4">
      {!target.is_feasible && (
        <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Mục tiêu dinh dưỡng hiện tại khó khả thi. Hãy điều chỉnh cân nặng mục tiêu hoặc mức vận động.</span>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <StatCard label="BMR" value={formatKcal(target.bmr)} icon={Flame} tone="accent" sub="Trao đổi cơ bản" compact />
        <StatCard label="TDEE" value={formatKcal(target.tdee)} icon={Activity} tone="sky" sub="Tiêu hao/ngày" compact />
        <StatCard
          label="Calo mục tiêu"
          value={formatKcal(target.target_calories)}
          icon={Flame}
          tone="brand"
          sub="Theo mục tiêu"
          compact
        />
        <StatCard
          label="BMI"
          value={formatNumber(target.bmi, 1)}
          icon={Scale}
          tone="indigo"
          sub={bmiLabel(target.bmi)}
          compact
        />
      </div>

      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Đạm" value={formatGram(target.daily_protein_g)} icon={Beef} tone="rose" compact />
        <StatCard label="Chất béo" value={formatGram(target.daily_fat_g)} icon={Droplet} tone="amber" compact />
        <StatCard label="Tinh bột" value={formatGram(target.daily_carb_g)} icon={Wheat} tone="brand" compact />
      </div>

      {target.warnings.length > 0 && (
        <ul className="space-y-2">
          {target.warnings.map((w) => (
            <li
              key={w.code}
              className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{w.message}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
