import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Beef, ChefHat, Droplet, Flame, Search, Wallet } from "lucide-react";
import { dishApi } from "../../api/dishApi";
import { EmptyState, FeedbackBanner, Pagination, SelectField, Spinner, Badge, PageHeader } from "../../components/ui";
import { FilterBar } from "../../components/domain/FilterBar";
import { toUserFeedback, type UserFeedback } from "../../lib/userFeedback";
import { COOKING_METHOD_LABELS, DISH_TYPE_LABELS, DISH_TYPE_STYLES } from "../../lib/labels";
import { formatGram, formatKcal, formatVND } from "../../lib/format";
import type { DishSummary, DishType } from "../../types";

const LIMIT = 24;
const TYPE_OPTIONS = Object.entries(DISH_TYPE_LABELS)
  .filter(([value]) => value !== "side")
  .map(([value, label]) => ({ value, label }));

export function Meals() {
  const navigate = useNavigate();
  const [items, setItems] = useState<DishSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [dishType, setDishType] = useState<DishType | "">("");
  const [offset, setOffset] = useState(0);
  const [feedback, setFeedback] = useState<UserFeedback | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const list = await dishApi.list({
        search: search.trim() || undefined,
        dish_type: dishType || undefined,
        limit: LIMIT,
        offset,
      });
      setItems(list);
      setFeedback(null);
    } catch (err) {
      setItems([]);
      setFeedback(toUserFeedback(err, "load_catalog"));
    } finally {
      setLoading(false);
    }
  }, [dishType, offset, search]);

  useEffect(() => {
    const timer = window.setTimeout(load, 250);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <div>
      <PageHeader
        title="Món ăn"
        description="Khám phá các món đã có đủ công thức, dinh dưỡng và giá để đưa vào thực đơn."
      />

      {feedback && <FeedbackBanner feedback={feedback} onRetry={load} className="mb-5" />}

      <FilterBar>
        <label className="relative block min-w-0 flex-1">
          <span className="sr-only">Tìm món ăn</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setOffset(0);
            }}
            placeholder="Tìm theo tên món"
            className="min-h-11 w-full rounded-xl border border-sand-200 bg-white px-3 pl-9 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-400"
          />
        </label>
        <SelectField
          value={dishType}
          onChange={(event) => {
            setDishType(event.target.value as DishType | "");
            setOffset(0);
          }}
          options={TYPE_OPTIONS}
          placeholder="Tất cả loại món"
          className="sm:w-48"
        />
      </FilterBar>

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="h-7 w-7" />
        </div>
      ) : feedback ? null : items.length === 0 ? (
        <EmptyState
          icon={ChefHat}
          title={search || dishType ? "Không tìm thấy món phù hợp" : "Chưa có món sẵn sàng"}
          description={search || dishType
            ? "Thử đổi từ khóa hoặc chọn loại món khác."
            : "Món sẽ xuất hiện khi đã có đủ công thức, dinh dưỡng và giá nguyên liệu."}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((dish) => (
            <button
              key={dish.id}
              type="button"
              onClick={() => navigate(`/meals/${dish.id}`)}
              className="group rounded-2xl border border-sand-200 bg-white p-4 text-left shadow-sm transition hover:border-brand-200 hover:shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <Badge className={DISH_TYPE_STYLES[dish.dish_type]}>
                    {DISH_TYPE_LABELS[dish.dish_type]}
                  </Badge>
                  <h3 className="mt-2 font-semibold text-gray-900 transition group-hover:text-brand-700">
                    {dish.name}
                  </h3>
                </div>
                {dish.cooking_method && (
                  <span className="shrink-0 text-xs text-gray-500">
                    {COOKING_METHOD_LABELS[dish.cooking_method]}
                  </span>
                )}
              </div>

              <div className="mt-3 grid grid-cols-2 gap-y-1.5 text-xs text-gray-600">
                <span className="flex items-center gap-1"><Flame className="h-3.5 w-3.5" /> {formatKcal(dish.total_calories)}</span>
                <span className="flex items-center gap-1"><Beef className="h-3.5 w-3.5" /> {formatGram(dish.total_protein_g)}</span>
                <span className="flex items-center gap-1"><Droplet className="h-3.5 w-3.5" /> {formatGram(dish.total_fat_g)}</span>
                <span className="flex items-center gap-1 font-medium text-brand-700"><Wallet className="h-3.5 w-3.5" /> {formatVND(dish.estimated_cost)}</span>
              </div>

              {dish.tags.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {dish.tags.slice(0, 4).map((tag) => (
                    <span key={tag} className="rounded-full bg-sand-100 px-2 py-0.5 text-xs text-gray-600">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {!loading && (
        <div className="mt-4">
          <Pagination offset={offset} limit={LIMIT} count={items.length} onChange={setOffset} />
        </div>
      )}
    </div>
  );
}
