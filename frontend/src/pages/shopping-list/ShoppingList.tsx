import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { ShoppingCart, Printer, History } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi } from "../../api/mealPlanApi";
import { mealApi } from "../../api/mealApi";
import { aggregateIngredients } from "../../api/shoppingListApi";
import type { ShoppingItem } from "../../api/shoppingListApi";
import {
  PageHeader, Card, SelectField, Spinner, EmptyState, Badge,
} from "../../components/ui";
import { formatNumber } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { MealPlan } from "../../types";

export function ShoppingList() {
  const { user } = useAuth();
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [selectedId, setSelectedId] = useState("");
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [building, setBuilding] = useState(false);

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const list = await mealPlanApi.list();
        setPlans(list);
      } catch (err) {
        toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
      } finally {
        setLoadingPlans(false);
      }
    })();
  }, [user]);

  const buildList = async (planId: number) => {
    const plan = plans.find((p) => p.id === planId);
    if (!plan) return;
    setBuilding(true);
    setItems([]);
    setChecked({});
    try {
      const planned = plan.plan_data.days.flatMap((d) => d.meals);
      // Phase A: plan mâm cơm (meal_set) chưa gom được qua /api/meals cũ.
      const isMealSetPlan = planned.some(
        (m) => m.candidate_type === "meal_set" || m.meal_set_id != null,
      );
      if (isMealSetPlan) {
        toast("Danh sách đi chợ cho mâm cơm sẽ có ở bản sau (Phase B).", { icon: "🛒" });
        return;
      }
      const mealIds = [
        ...new Set(
          planned.map((m) => m.meal_id).filter((id): id is number => id != null),
        ),
      ];
      const meals = await Promise.all(mealIds.map((mid) => mealApi.get(mid)));
      setItems(aggregateIngredients(meals));
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setBuilding(false);
    }
  };

  const onSelect = (value: string) => {
    setSelectedId(value);
    if (value) buildList(Number(value));
  };

  const toggle = (key: string) => setChecked((c) => ({ ...c, [key]: !c[key] }));

  const doneCount = items.filter((it) => checked[`${it.ingredient_id}__${it.unit}`]).length;

  if (loadingPlans) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="h-7 w-7" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Danh sách đi chợ"
        description="Chọn một thực đơn đã lưu để tự động gom nguyên liệu cần mua."
        actions={
          items.length > 0 ? (
            <button
              onClick={() => window.print()}
              className="no-print inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
            >
              <Printer className="h-4 w-4" /> In danh sách
            </button>
          ) : undefined
        }
      />

      {plans.length === 0 ? (
        <EmptyState
          icon={History}
          title="Chưa có thực đơn đã lưu"
          description="Hãy tạo và lưu thực đơn trước, sau đó quay lại để lập danh sách đi chợ."
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
        <>
          <div className="no-print mb-5 max-w-md">
            <SelectField
              label="Chọn thực đơn"
              value={selectedId}
              onChange={(e) => onSelect(e.target.value)}
              options={plans.map((p) => ({ value: String(p.id), label: p.name }))}
              placeholder="— Chọn một thực đơn —"
            />
          </div>

          {building ? (
            <div className="flex justify-center py-16">
              <Spinner className="h-7 w-7" />
            </div>
          ) : selectedId && items.length === 0 ? (
            <EmptyState
              icon={ShoppingCart}
              title="Không có nguyên liệu"
              description="Thực đơn này chưa có nguyên liệu để gom."
            />
          ) : items.length > 0 ? (
            <Card
              title="Nguyên liệu cần mua"
              icon={<ShoppingCart className="h-5 w-5" />}
              action={
                <Badge className="bg-brand-100 text-brand-700">
                  {doneCount}/{items.length} đã mua
                </Badge>
              }
              bodyClassName="p-0"
            >
              <ul className="divide-y divide-sand-100">
                {items.map((it) => {
                  const key = `${it.ingredient_id}__${it.unit}`;
                  const isChecked = !!checked[key];
                  return (
                    <li key={key} className="flex items-center gap-3 px-5 py-3">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggle(key)}
                        className="h-4 w-4 rounded border-sand-300 text-brand-600 focus:ring-brand-400"
                      />
                      <span
                        className={`flex-1 text-sm font-medium ${
                          isChecked ? "text-gray-400 line-through" : "text-gray-800"
                        }`}
                      >
                        {it.name}
                      </span>
                      <span className="text-sm text-gray-500">
                        {formatNumber(it.quantity, 1)} {it.unit}
                      </span>
                    </li>
                  );
                })}
              </ul>
            </Card>
          ) : (
            <p className="text-sm text-gray-500">Chọn một thực đơn để bắt đầu.</p>
          )}
        </>
      )}
    </div>
  );
}
