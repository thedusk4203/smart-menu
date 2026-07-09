import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { UtensilsCrossed, RefreshCw, Save, ArrowLeft } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi, isInfeasible } from "../../api/mealPlanApi";
import { aiApi } from "../../api/aiApi";
import { PageHeader, Button, EmptyState, TextField } from "../../components/ui";
import { MealPlanView } from "../../components/domain/MealPlanView";
import { ApiError } from "../../lib/apiClient";
import { todayISO } from "../../lib/format";
import type { GeneratedMealPlan, GenerateParams, PlannedMeal } from "../../types";

interface ResultState {
  plan?: GeneratedMealPlan;
  params?: GenerateParams;
}

export function MenuResult() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as ResultState | null) ?? {};

  const [plan, setPlan] = useState<GeneratedMealPlan | null>(state.plan ?? null);
  const [name, setName] = useState(state.plan?.name ?? "Thực đơn của tôi");
  const [regenerating, setRegenerating] = useState(false);
  const [saving, setSaving] = useState(false);

  if (!plan) {
    return (
      <div>
        <PageHeader title="Kết quả thực đơn" />
        <EmptyState
          icon={UtensilsCrossed}
          title="Chưa có thực đơn để hiển thị"
          description="Hãy tạo một thực đơn mới để xem kết quả tại đây."
          action={
            <Link
              to="/create-menu"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700"
            >
              Tạo thực đơn
            </Link>
          }
        />
      </div>
    );
  }

  const regenerate = async () => {
    if (!user) return;
    setRegenerating(true);
    try {
      const seed = Math.floor(Math.random() * 1e9);
      const result = await mealPlanApi.generate({ ...state.params, seed });
      if (isInfeasible(result)) {
        toast.error(result.reasons[0] ?? "Không thể tạo thực đơn khác.");
        return;
      }
      setPlan(result);
      setName(result.name);
      toast.success("Đã tạo thực đơn mới.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setRegenerating(false);
    }
  };

  const save = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await mealPlanApi.save({
        name: name.trim() || "Thực đơn của tôi",
        start_date: todayISO(),
        budget_limit: plan.budget_limit,
        days: plan.plan_data.days.map((d) => ({
          day: d.day,
          meals: d.meals.map((m) => ({
            slot: m.meal_type,
            meal_set_id: m.meal_set_id as number,
          })),
        })),
      });
      toast.success("Đã lưu thực đơn.");
      navigate("/history");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setSaving(false);
    }
  };

  const handleSwap = async (_day: number, meal: PlannedMeal) => {
    // Phase A: candidate là meal_set -> chưa hỗ trợ swap; tránh gửi meal_id=null.
    if (meal.candidate_type === "meal_set" || meal.meal_id == null) {
      toast("Đổi món cho mâm cơm đang được phát triển.", { icon: "🛠️" });
      return;
    }
    try {
      await aiApi.suggestSwap({ meal_id: meal.meal_id, meal_type: meal.meal_type });
      toast.success("Đã nhận gợi ý đổi món.");
    } catch {
      toast("Tính năng đổi món bằng AI đang được phát triển.", { icon: "🛠️" });
    }
  };

  return (
    <div>
      <PageHeader
        title="Kết quả thực đơn"
        description="Xem lại thực đơn được đề xuất, tạo lại phương án khác hoặc lưu để dùng sau."
        actions={
          <Button variant="ghost" size="sm" onClick={() => navigate("/create-menu")}>
            <ArrowLeft className="h-4 w-4" /> Tạo mới
          </Button>
        }
      />

      <div className="mb-5 flex flex-col gap-3 rounded-2xl border border-sand-200 bg-white p-4 shadow-sm sm:flex-row sm:items-end">
        <TextField
          label="Tên thực đơn"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1"
          placeholder="Đặt tên cho thực đơn..."
        />
        <div className="flex gap-2">
          <Button variant="secondary" onClick={regenerate} loading={regenerating}>
            <RefreshCw className="h-4 w-4" /> Tạo lại
          </Button>
          <Button onClick={save} loading={saving}>
            <Save className="h-4 w-4" /> Lưu thực đơn
          </Button>
        </div>
      </div>

      <MealPlanView
        planData={plan.plan_data}
        totalCost={plan.total_cost}
        totalCalories={plan.total_calories}
        budgetLimit={plan.budget_limit}
        onSwapMeal={handleSwap}
      />
    </div>
  );
}
