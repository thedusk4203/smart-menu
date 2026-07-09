import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, Flame, Beef, Droplet, Wheat, Wallet, ChefHat, Utensils } from "lucide-react";
import { mealApi } from "../../api/mealApi";
import {
  PageHeader, Card, Badge, StatCard, Button, FullPageSpinner, EmptyState,
} from "../../components/ui";
import { MEAL_TYPE_LABELS, MEAL_TYPE_STYLES, COOKING_METHOD_LABELS } from "../../lib/labels";
import { formatKcal, formatGram, formatVND, formatNumber } from "../../lib/format";
import { ApiError } from "../../lib/apiClient";
import type { MealDetail as MealDetailType } from "../../types";

export function MealDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [meal, setMeal] = useState<MealDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const mealId = Number(id);
    if (!mealId) {
      setNotFound(true);
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const data = await mealApi.get(mealId);
        setMeal(data);
      } catch (err) {
        setNotFound(true);
        toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <FullPageSpinner />;

  if (notFound || !meal) {
    return (
      <div>
        <PageHeader title="Chi tiết món ăn" />
        <EmptyState
          icon={ChefHat}
          title="Không tìm thấy món ăn"
          description="Món ăn có thể đã bị xoá hoặc không tồn tại."
          action={
            <Button variant="secondary" onClick={() => navigate("/meals")}>
              <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-5">
        <Button variant="ghost" size="sm" onClick={() => navigate("/meals")}>
          <ArrowLeft className="h-4 w-4" /> Danh sách món ăn
        </Button>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <h1 className="text-2xl font-bold text-gray-900">{meal.name}</h1>
        <Badge className={MEAL_TYPE_STYLES[meal.meal_type]}>{MEAL_TYPE_LABELS[meal.meal_type]}</Badge>
        {meal.cooking_method && (
          <Badge className="bg-sand-200 text-gray-700">{COOKING_METHOD_LABELS[meal.cooking_method]}</Badge>
        )}
        <Badge className="bg-sky-100 text-sky-700">{meal.servings} khẩu phần</Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Calo" value={formatKcal(meal.total_calories)} icon={Flame} tone="amber" />
        <StatCard label="Đạm" value={formatGram(meal.total_protein_g)} icon={Beef} tone="rose" />
        <StatCard label="Tinh bột" value={formatGram(meal.total_carbs_g)} icon={Wheat} tone="brand" />
        <StatCard label="Chất béo" value={formatGram(meal.total_fat_g)} icon={Droplet} tone="accent" />
        <StatCard label="Chi phí" value={formatVND(meal.estimated_cost)} icon={Wallet} tone="sky" />
      </div>

      {meal.tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {meal.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-sand-100 px-2.5 py-0.5 text-xs text-gray-600">
              #{tag}
            </span>
          ))}
        </div>
      )}

      {meal.components && meal.components.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {meal.components.map((component) => (
            <span key={component} className="rounded-lg bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700">
              {component}
            </span>
          ))}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          {meal.description && (
            <Card title="Mô tả">
              <p className="text-sm leading-relaxed text-gray-600">{meal.description}</p>
            </Card>
          )}
          {meal.instructions && (
            <Card title="Cách làm" icon={<Utensils className="h-5 w-5" />}>
              <p className="whitespace-pre-line text-sm leading-relaxed text-gray-600">{meal.instructions}</p>
            </Card>
          )}
        </div>

        <Card title="Nguyên liệu" icon={<ChefHat className="h-5 w-5" />} bodyClassName="p-0">
          {meal.ingredients.length === 0 ? (
            <p className="p-5 text-sm text-gray-500">Chưa có nguyên liệu.</p>
          ) : (
            <ul className="divide-y divide-sand-100">
              {meal.ingredients.map((ing, idx) => (
                <li key={`${ing.ingredient_id}-${idx}`} className="flex items-center justify-between px-5 py-3">
                  <span className="text-sm font-medium text-gray-800">
                    {ing.name ?? `Nguyên liệu #${ing.ingredient_id}`}
                  </span>
                  <span className="text-sm text-gray-500">
                    {formatNumber(ing.quantity, 1)} {ing.unit}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
