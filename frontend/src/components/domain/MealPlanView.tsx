import { Calendar, Wallet, Flame, AlertTriangle, Sparkles } from "lucide-react";
import { StatCard, Badge } from "../ui";
import { MEAL_TYPE_LABELS, MEAL_TYPE_STYLES, DISH_ROLE_LABELS } from "../../lib/labels";
import { formatVND, formatKcal, formatGram } from "../../lib/format";
import type { PlanData, PlannedMeal } from "../../types";

interface MealPlanViewProps {
  planData: PlanData;
  totalCost?: number;
  totalCalories?: number;
  budgetLimit?: number | null;
  onSwapMeal?: (day: number, meal: PlannedMeal) => void;
}

export function MealPlanView({
  planData,
  totalCost,
  totalCalories,
  budgetLimit,
  onSwapMeal,
}: MealPlanViewProps) {
  const days = planData.days ?? [];
  const numDays = days.length || 1;
  const cost = totalCost ?? days.reduce((s, d) => s + d.day_cost, 0);
  const calories = totalCalories ?? days.reduce((s, d) => s + d.day_calories, 0);
  const overBudget = budgetLimit != null && cost > budgetLimit;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Số ngày" value={days.length} icon={Calendar} tone="brand" />
        <StatCard
          label="Tổng chi phí"
          value={formatVND(cost)}
          icon={Wallet}
          tone={overBudget ? "rose" : "accent"}
          sub={budgetLimit != null ? `Ngân sách: ${formatVND(budgetLimit)}` : "Không giới hạn"}
        />
        <StatCard label="Tổng calo" value={formatKcal(calories)} icon={Flame} tone="amber" />
        <StatCard
          label="Calo TB/ngày"
          value={formatKcal(Math.round(calories / numDays))}
          icon={Flame}
          tone="sky"
        />
      </div>

      {overBudget && (
        <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>Tổng chi phí vượt ngân sách {formatVND(cost - budgetLimit!)}.</span>
        </div>
      )}

      {planData.warnings?.length > 0 && (
        <ul className="space-y-2">
          {planData.warnings.map((w, i) => (
            <li
              key={i}
              className="flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800"
            >
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{w}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {days.map((day) => (
          <div key={day.day} className="rounded-2xl border border-sand-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-sand-200 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-100 text-sm font-bold text-brand-700">
                  {day.day}
                </span>
                <div>
                  <p className="text-sm font-semibold text-gray-800">Ngày {day.day}</p>
                  {day.date && <p className="text-xs text-gray-400">{day.date}</p>}
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-brand-700">{formatVND(day.day_cost)}</p>
                <p className="text-xs text-gray-400">{formatKcal(day.day_calories)}</p>
              </div>
            </div>
            <ul className="divide-y divide-sand-100">
              {day.meals.map((meal, idx) => (
                <li key={`${meal.meal_set_id ?? meal.meal_id ?? idx}-${idx}`} className="px-4 py-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <Badge className={MEAL_TYPE_STYLES[meal.meal_type]}>
                        {MEAL_TYPE_LABELS[meal.meal_type]}
                      </Badge>
                      <p className="mt-1.5 font-medium text-gray-800">{meal.name}</p>
                      {meal.dishes && meal.dishes.length > 0 ? (
                        <ul className="mt-2 space-y-1">
                          {meal.dishes.map((dish) => (
                            <li
                              key={dish.dish_id}
                              className="flex flex-wrap items-baseline gap-x-1.5 text-xs"
                            >
                              {dish.role !== "breakfast" && (
                                <span className="font-medium text-gray-400">
                                  {DISH_ROLE_LABELS[dish.role]}
                                </span>
                              )}
                              <span className="text-gray-700">{dish.name}</span>
                            </li>
                          ))}
                        </ul>
                      ) : meal.components && meal.components.length > 0 ? (
                        <ul className="mt-2 flex flex-wrap gap-1.5">
                          {meal.components.map((component) => (
                            <li
                              key={component}
                              className="rounded-md bg-sand-100 px-2 py-0.5 text-xs text-gray-600"
                            >
                              {component}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </div>
                    {onSwapMeal && meal.candidate_type !== "meal_set" && (
                      <button
                        type="button"
                        onClick={() => onSwapMeal(day.day, meal)}
                        title="Đổi món bằng AI"
                        className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-accent-200 bg-accent-50 px-2 py-1 text-xs font-medium text-accent-700 transition hover:bg-accent-100"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                        Đổi
                      </button>
                    )}
                  </div>
                  <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500">
                    <span>{formatKcal(meal.calories)}</span>
                    <span>Đạm {formatGram(meal.protein_g)}</span>
                    <span>Béo {formatGram(meal.fat_g)}</span>
                    <span>Tinh bột {formatGram(meal.carb_g)}</span>
                    <span className="font-medium text-brand-600">{formatVND(meal.cost)}</span>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
