import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import toast from "react-hot-toast";
import { ArrowLeft, Beef, ChefHat, Droplet, Flame, Utensils, Wallet, Wheat } from "lucide-react";
import { dishApi } from "../../api/dishApi";
import { Badge, Button, Card, EmptyState, FullPageSpinner, PageHeader, StatCard } from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { COOKING_METHOD_LABELS, DISH_TYPE_LABELS, DISH_TYPE_STYLES } from "../../lib/labels";
import { formatGram, formatKcal, formatNumber, formatVND } from "../../lib/format";
import type { DishDetail } from "../../types";

export function MealDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dish, setDish] = useState<DishDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const dishId = Number(id);
    if (!dishId) {
      setNotFound(true);
      setLoading(false);
      return;
    }

    (async () => {
      try {
        setDish(await dishApi.get(dishId));
      } catch (err) {
        setNotFound(true);
        toast.error(err instanceof ApiError ? err.message : "Không thể tải món ăn.");
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <FullPageSpinner />;

  if (notFound || !dish) {
    return (
      <div>
        <PageHeader title="Chi tiết món ăn" />
        <EmptyState
          icon={ChefHat}
          title="Không tìm thấy món ăn"
          description="Món có thể đã bị ẩn hoặc chưa đủ dữ liệu để sử dụng."
          action={(
            <Button variant="secondary" onClick={() => navigate("/meals")}>
              <ArrowLeft className="h-4 w-4" /> Quay lại danh sách
            </Button>
          )}
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
        <h1 className="text-2xl font-bold text-gray-900">{dish.name}</h1>
        <Badge className={DISH_TYPE_STYLES[dish.dish_type]}>{DISH_TYPE_LABELS[dish.dish_type]}</Badge>
        {dish.cooking_method && (
          <Badge className="bg-sand-200 text-gray-700">{COOKING_METHOD_LABELS[dish.cooking_method]}</Badge>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Calo" value={formatKcal(dish.total_calories)} icon={Flame} tone="amber" />
        <StatCard label="Đạm" value={formatGram(dish.total_protein_g)} icon={Beef} tone="rose" />
        <StatCard label="Tinh bột" value={formatGram(dish.total_carbs_g)} icon={Wheat} tone="brand" />
        <StatCard label="Chất béo" value={formatGram(dish.total_fat_g)} icon={Droplet} tone="accent" />
        <StatCard label="Chi phí ước tính" value={formatVND(dish.estimated_cost)} icon={Wallet} tone="sky" />
      </div>

      {dish.tags.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {dish.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-sand-100 px-2.5 py-0.5 text-xs text-gray-600">
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          {dish.description && (
            <Card title="Mô tả">
              <p className="text-sm leading-relaxed text-gray-600">{dish.description}</p>
            </Card>
          )}
          {dish.instructions && (
            <Card title="Cách làm" icon={<Utensils className="h-5 w-5" />}>
              <p className="whitespace-pre-line text-sm leading-relaxed text-gray-600">{dish.instructions}</p>
            </Card>
          )}
        </div>

        <Card title="Nguyên liệu" icon={<ChefHat className="h-5 w-5" />} bodyClassName="p-0">
          <ul className="divide-y divide-sand-100">
            {dish.ingredients.map((ingredient) => (
              <li key={ingredient.ingredient_id} className="flex items-center justify-between gap-4 px-5 py-3">
                <span className="text-sm font-medium text-gray-800">{ingredient.name}</span>
                <span className="shrink-0 text-right text-sm text-gray-600">
                  <span>{formatNumber(ingredient.quantity, 1)} {ingredient.unit}</span>
                  <span className="ml-2 text-xs text-gray-500">{formatVND(ingredient.estimated_cost)}</span>
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
