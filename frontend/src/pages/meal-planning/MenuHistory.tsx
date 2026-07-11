import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { History, Trash2, Eye, Wallet, Flame, Calendar, UtensilsCrossed } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi } from "../../api/mealPlanApi";
import {
  PageHeader, Card, Button, Badge, Modal, FullPageSpinner, EmptyState,
} from "../../components/ui";
import { MealPlanView } from "../../components/domain/MealPlanView";
import { formatVND, formatKcal, formatDate } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { MealPlan } from "../../types";

export function MenuHistory() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<MealPlan | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = async () => {
    if (!user) return;
    try {
      const list = await mealPlanApi.list();
      setPlans(list);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleDelete = async (id: number) => {
    if (!window.confirm("Xoá thực đơn này? Hành động không thể hoàn tác.")) return;
    setDeletingId(id);
    try {
      await mealPlanApi.remove(id);
      setPlans((prev) => prev.filter((p) => p.id !== id));
      if (selected?.id === id) setSelected(null);
      toast.success("Đã xoá thực đơn.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <FullPageSpinner />;

  return (
    <div>
      <PageHeader
        title="Lịch sử thực đơn"
        description="Các thực đơn bạn đã lưu."
        actions={
          <Link
            to="/create-menu"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            <UtensilsCrossed className="h-4 w-4" /> Tạo mới
          </Link>
        }
      />

      {plans.length === 0 ? (
        <EmptyState
          icon={History}
          title="Chưa có thực đơn đã lưu"
          description="Tạo và lưu thực đơn để xem lại tại đây bất cứ lúc nào."
          action={
            <Link
              to="/create-menu"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700"
            >
              Tạo thực đơn
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {plans.map((plan) => (
            <Card key={plan.id}>
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-semibold text-gray-800">{plan.name}</h3>
              </div>
              <p className="mt-1 flex items-center gap-1 text-xs text-gray-400">
                <Calendar className="h-3.5 w-3.5" /> {formatDate(plan.start_date)} · {plan.plan_data.days.length} ngày
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Badge className="bg-brand-100 text-brand-700">
                  <Wallet className="h-3.5 w-3.5" /> {formatVND(plan.total_cost)}
                </Badge>
                <Badge className="bg-amber-100 text-amber-700">
                  <Flame className="h-3.5 w-3.5" /> {formatKcal(plan.total_calories)}
                </Badge>
              </div>
              <div className="mt-4 flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => setSelected(plan)} className="flex-1">
                  <Eye className="h-4 w-4" /> Chi tiết
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(plan.id)}
                  loading={deletingId === plan.id}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={!!selected} onClose={() => setSelected(null)} title={selected?.name} size="lg">
        {selected && (
          <MealPlanView
            planData={selected.plan_data}
            totalCost={selected.total_cost}
            totalCalories={selected.total_calories}
            budgetLimit={selected.budget_limit}
          />
        )}
      </Modal>
    </div>
  );
}
