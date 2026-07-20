import { AlertTriangle, Calendar, Flame, RefreshCw, Target, Wallet } from "lucide-react";
import { Badge, StatCard } from "../ui";
import { DISH_TYPE_LABELS, MEAL_TYPE_LABELS, MEAL_TYPE_STYLES } from "../../lib/labels";
import { formatGram, formatKcal, formatVND } from "../../lib/format";
import { isUserVisiblePlanNotice, planNoticeText } from "../../lib/domainMessages";
import type { DishType, MealType, PlanData, PlanDish } from "../../types";

interface MealPlanViewProps {
  planData: PlanData;
  totalCost?: number;
  totalCalories?: number;
  budgetLimit?: number | null;
  onSwap?: (day: number, mealType: MealType, dish: PlanDish) => void;
}

function warningText(warning: PlanData["warnings"][number]) {
  return typeof warning === "string" ? warning : planNoticeText(warning);
}

export function MealPlanView({ planData, totalCost, totalCalories, budgetLimit, onSwap }: MealPlanViewProps) {
  const days = planData.days ?? [];
  const numDays = days.length || 1;
  const cost = totalCost ?? days.reduce((sum, day) => sum + day.day_cost, 0);
  const calories = totalCalories ?? days.reduce((sum, day) => sum + day.day_calories, 0);
  const averageCalories = calories / numDays;
  const target = planData.nutrition_target;
  const overBudget = budgetLimit != null && cost > budgetLimit;
  const costSummary = planData.cost_summary;
  const visibleWarnings = (planData.warnings ?? []).filter(isUserVisiblePlanNotice);

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Số ngày" value={days.length} icon={Calendar} tone="brand" />
        <StatCard label="Cần chi để mua" value={formatVND(cost)} icon={Wallet} tone={overBudget ? "rose" : "accent"} sub={budgetLimit != null ? `Ngân sách: ${formatVND(budgetLimit)}` : "Không giới hạn"} />
        <StatCard label="Tổng calo" value={formatKcal(calories)} icon={Flame} tone="amber" />
        <StatCard label="Calo TB/ngày" value={formatKcal(Math.round(averageCalories))} icon={Target} tone="sky" />
      </div>

      {target && (
        <section className="overflow-hidden rounded-2xl border border-brand-200 bg-white shadow-sm" aria-label="Mục tiêu dinh dưỡng">
          <div className="flex items-center justify-between gap-3 bg-brand-700 px-4 py-3 text-white">
            <div className="flex items-center gap-2"><Target className="h-4 w-4" /><h2 className="text-sm font-semibold">La bàn dinh dưỡng mỗi ngày</h2></div>
            <span className="text-xs text-brand-100">Sau điều chỉnh tận dụng phần dư</span>
          </div>
          <div className="grid grid-cols-2 divide-x divide-y divide-sand-100 sm:grid-cols-4 sm:divide-y-0">
            {[
              ["Calo", averageCalories, target.calories, "kcal"],
              ["Đạm", days.reduce((sum, day) => sum + day.meals.reduce((inner, meal) => inner + meal.protein_g, 0), 0) / numDays, target.protein_g, "g"],
              ["Béo", days.reduce((sum, day) => sum + day.meals.reduce((inner, meal) => inner + meal.fat_g, 0), 0) / numDays, target.fat_g, "g"],
              ["Tinh bột", days.reduce((sum, day) => sum + day.meals.reduce((inner, meal) => inner + meal.carb_g, 0), 0) / numDays, target.carb_g, "g"],
            ].map(([label, actual, expected, unit]) => {
              const difference = Number(actual) - Number(expected);
              return <div key={String(label)} className="px-4 py-3"><p className="text-xs font-medium text-gray-500">{label}</p><p className="mt-1 font-semibold tabular-nums text-gray-900">{Math.round(Number(actual))}{unit}</p><p className={`text-xs ${Math.abs(difference) / Math.max(Number(expected), 1) > 0.2 ? "text-amber-700" : "text-brand-700"}`}>Mục tiêu {Math.round(Number(expected))}{unit} · {difference >= 0 ? "+" : ""}{Math.round(difference)}</p></div>;
            })}
          </div>
        </section>
      )}

      {costSummary && (
        <section className="grid gap-3 rounded-2xl border border-sand-200 bg-white p-4 shadow-sm sm:grid-cols-3" aria-label="Chi tiết mua và tận dụng">
          <div><p className="text-xs text-gray-500">Giá trị sẽ dùng</p><p className="mt-1 font-semibold text-gray-900">{formatVND(costSummary.consumption_value)}</p></div>
          <div><p className="text-xs text-gray-500">Còn lại cuối kỳ</p><p className="mt-1 font-semibold text-sky-800">{formatVND(costSummary.ending_carryover_value)}</p></div>
          <div><p className="text-xs text-gray-500">Dự kiến hết hạn</p><p className="mt-1 font-semibold text-amber-800">{formatVND(costSummary.expired_waste_value)}</p></div>
        </section>
      )}

      {(planData.adjustments?.length ?? 0) > 0 && (
        <section className="rounded-2xl border border-brand-200 bg-brand-50 p-4">
          <h2 className="text-sm font-semibold text-brand-900">Phần dư được thêm vào món sau</h2>
          <ul className="mt-2 space-y-1.5 text-sm text-brand-800">
            {planData.adjustments?.map((item) => <li key={`${item.day}-${item.slot}-${item.dish_id}-${item.ingredient_id}`}>Ngày {item.day}: tăng {item.extra_quantity}{item.unit} · {Math.round(item.nutrition_delta.calories)} kcal</li>)}
          </ul>
        </section>
      )}

      {(overBudget || visibleWarnings.length > 0) && (
        <ul className="space-y-2">
          {overBudget && <li className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><span>Tổng chi phí vượt ngân sách {formatVND(cost - budgetLimit!)}.</span></li>}
          {visibleWarnings.map((warning, index) => <li key={typeof warning === "string" ? `${warning}-${index}` : `${warning.code}-${index}`} className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" /><span>{warningText(warning)}</span></li>)}
        </ul>
      )}

      {planData.metrics && <p className="text-xs text-gray-500">Chênh lệch năng lượng trung bình {planData.metrics.average_calorie_deviation_pct}% · Mức thiếu đạm {planData.metrics.protein_shortage_pct}%</p>}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {days.map((day) => (
          <section key={day.day} className="rounded-2xl border border-sand-200 bg-white shadow-sm">
            <header className="flex items-center justify-between border-b border-sand-200 px-4 py-3">
              <div className="flex items-center gap-2"><span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-sm font-bold text-brand-700">{day.day}</span><div><p className="text-sm font-semibold text-gray-800">Ngày {day.day}</p>{day.date && <p className="text-xs text-gray-400">{day.date}</p>}</div></div>
              <div className="text-right"><p className="text-sm font-semibold text-brand-700">{formatVND(day.day_cost)}</p><p className="text-xs text-gray-400">{formatKcal(day.day_calories)}</p></div>
            </header>
            <ul className="divide-y divide-sand-100">
              {day.meals.map((meal, index) => (
                <li key={`${day.day}-${meal.meal_type}-${index}`} className="px-4 py-3">
                  <Badge className={MEAL_TYPE_STYLES[meal.meal_type]}>{MEAL_TYPE_LABELS[meal.meal_type]}</Badge>
                  <p className="mt-1.5 font-medium text-gray-800">{meal.name}</p>
                  {meal.dishes?.length ? <ul className="mt-2 space-y-1.5">{meal.dishes.map((dish) => {
                    const dishType = dish.dish_type as DishType | undefined;
                    return <li key={dish.dish_id} className="flex items-center gap-2 text-xs"><span className="min-w-16 font-medium text-gray-400">{dishType ? DISH_TYPE_LABELS[dishType] : "Món"}</span><span className="flex-1 text-gray-700">{dish.name}</span>{onSwap && <button type="button" onClick={() => onSwap(day.day, meal.meal_type, dish)} className="rounded-lg p-1 text-brand-600 hover:bg-brand-50" aria-label={`Đổi ${dish.name}`}><RefreshCw className="h-3.5 w-3.5" /></button>}</li>;
                  })}</ul> : meal.components?.length ? <div className="mt-2 flex flex-wrap gap-1.5">{meal.components.map((component) => <span key={component} className="rounded-md bg-sand-100 px-2 py-0.5 text-xs text-gray-600">{component}</span>)}</div> : null}
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500"><span>{formatKcal(meal.calories)}</span><span>Đạm {formatGram(meal.protein_g)}</span><span>Béo {formatGram(meal.fat_g)}</span><span>Tinh bột {formatGram(meal.carb_g)}</span><span className="font-medium text-brand-600">{formatVND(meal.cost)}</span></div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
