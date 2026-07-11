import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { UtensilsCrossed, RefreshCw, Save, ArrowLeft, Sparkles } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi, isInfeasible } from "../../api/mealPlanApi";
import { aiApi } from "../../api/aiApi";
import type { SwapSuggestion } from "../../api/aiApi";
import { PageHeader, Button, Card, EmptyState, TextField, Textarea, Modal } from "../../components/ui";
import { MealPlanView } from "../../components/domain/MealPlanView";
import { ApiError } from "../../lib/apiClient";
import { defaultMealPlanName, todayISO } from "../../lib/format";
import type { GeneratedMealPlan, GenerateParams, MealType, PlanDish } from "../../types";

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
  const [name, setName] = useState(() => state.plan?.name && state.plan.name !== "Thực đơn tuần" ? state.plan.name : defaultMealPlanName());
  const [regenerating, setRegenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [explaining, setExplaining] = useState(false);
  const [explanation, setExplanation] = useState("");
  const [swapping, setSwapping] = useState(false);
  const [swapSuggestions, setSwapSuggestions] = useState<SwapSuggestion[]>([]);
  const [swapTarget, setSwapTarget] = useState<{ day: number; mealType: MealType; dish: PlanDish } | null>(null);
  const [swapNote, setSwapNote] = useState("Món tương tự, phù hợp ngân sách");

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
      const result = await mealPlanApi.generate({
        ...state.params,
        seed,
        previous_plan_signature: plan.plan_data.plan_signature,
      });
      if (isInfeasible(result)) {
        toast.error(result.reasons[0]?.message ?? "Không thể tạo thực đơn khác.");
        return;
      }
      setPlan(result);
      setName(defaultMealPlanName());
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
        name: name.trim() || defaultMealPlanName(),
        start_date: todayISO(),
        budget_limit: plan.budget_limit,
        days: plan.plan_data.days.map((d) => ({
          day: d.day,
          meals: d.meals.map((m) => ({
            slot: m.meal_type,
            dish_ids: m.dishes?.map((dish) => dish.dish_id) ?? [],
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

  const explain = async () => {
    setExplaining(true);
    try { const result = await aiApi.explainPlan({ plan_data: plan.plan_data, total_cost: plan.total_cost, total_calories: plan.total_calories, budget_limit: plan.budget_limit }); setExplanation(result.reply); }
    catch (err) { toast.error(err instanceof ApiError ? err.message : "AI đang tạm không khả dụng."); }
    finally { setExplaining(false); }
  };

  const requestSwap = async (day: number, mealType: MealType, dish: PlanDish) => {
    setSwapTarget({ day, mealType, dish });
    setSwapNote("Món tương tự, phù hợp ngân sách");
  };

  const submitSwap = async () => {
    if (!swapTarget) return;
    const { day, mealType, dish } = swapTarget;
    setSwapping(true); setSwapSuggestions([]);
    try {
      const result = await aiApi.suggestSwap({ day, meal_type: mealType, target_dish_id: dish.dish_id, plan, note: swapNote.trim() });
      setSwapSuggestions(result);
      if (!result.length) toast("Không có món thay thế nào giữ được toàn bộ ràng buộc.");
      setSwapTarget(null);
    } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể tìm món thay thế."); }
    finally { setSwapping(false); }
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
          <Button variant="secondary" onClick={explain} loading={explaining}><Sparkles className="h-4 w-4" /> AI giải thích</Button>
        </div>
      </div>

      {explanation && <Card title="AI giải thích thực đơn" icon={<Sparkles className="h-5 w-5" />} className="mb-5"><p className="whitespace-pre-wrap text-sm leading-6 text-gray-700">{explanation}</p><p className="mt-3 text-xs text-gray-500">Nội dung mang tính tham khảo và được lưu tối đa 30 ngày.</p></Card>}
      {(swapping || swapSuggestions.length > 0) && <Card title="Phương án đổi món đã kiểm tra" className="mb-5"><div className="space-y-2">{swapping ? <p className="text-sm text-gray-500">Đang xếp hạng và kiểm tra toàn bộ thực đơn...</p> : swapSuggestions.map(item => <button key={item.dish_id} onClick={() => { setPlan(item.plan); setSwapSuggestions([]); toast.success(`Đã đổi sang ${item.name}.`); }} className="block w-full rounded-xl border border-sand-200 p-3 text-left hover:border-brand-300 hover:bg-brand-50"><span className="font-medium text-gray-800">{item.name}</span><span className="mt-1 block text-sm text-gray-500">{item.reason}</span><span className="mt-1 block text-xs font-medium text-brand-700">Chọn phương án này</span></button>)}</div></Card>}

      <MealPlanView
        planData={plan.plan_data}
        totalCost={plan.total_cost}
        totalCalories={plan.total_calories}
        budgetLimit={plan.budget_limit}
        onSwap={requestSwap}
      />
      <Modal open={!!swapTarget} onClose={() => !swapping && setSwapTarget(null)} title={swapTarget ? `Đổi “${swapTarget.dish.name}”` : "Đổi món"} size="sm" footer={<><Button variant="ghost" onClick={() => setSwapTarget(null)} disabled={swapping}>Hủy</Button><Button onClick={submitSwap} loading={swapping}>Tìm món thay thế</Button></>}>
        <Textarea label="Bạn muốn đổi theo hướng nào?" value={swapNote} onChange={(e) => setSwapNote(e.target.value)} rows={3} />
      </Modal>
    </div>
  );
}
