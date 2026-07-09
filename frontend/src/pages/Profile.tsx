import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import toast from "react-hot-toast";
import { Save, Trash2, Ban, Flame } from "lucide-react";
import { profileApi } from "../api/profileApi";
import { ingredientApi } from "../api/ingredientApi";
import { nutritionApi } from "../api/nutritionApi";
import {
  PageHeader, Card, Button, TextField, NumberField, SelectField, FullPageSpinner, Badge, Spinner,
} from "../components/ui";
import { NutritionSummary } from "../components/domain/NutritionSummary";
import { IngredientPicker } from "../components/domain/IngredientPicker";
import {
  GENDER_LABELS, ACTIVITY_LABELS, GOAL_LABELS, EXCLUSION_REASON_LABELS,
} from "../lib/labels";
import { ApiError } from "../lib/apiClient";
import type {
  ActivityLevel, Exclusion, ExclusionReason, FitnessGoal, Gender, NutritionTarget, Profile as ProfileType,
} from "../types";

const toOptions = (labels: Record<string, string>) =>
  Object.entries(labels).map(([value, label]) => ({ value, label }));

export function Profile() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [fullName, setFullName] = useState("");
  const [gender, setGender] = useState<Gender | "">("");
  const [age, setAge] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [activity, setActivity] = useState<ActivityLevel>("moderate");
  const [goal, setGoal] = useState<FitnessGoal>("maintain");
  const [mealsPerDay, setMealsPerDay] = useState("3");
  const [budget, setBudget] = useState("");

  const [target, setTarget] = useState<NutritionTarget | null>(null);
  const [targetLoading, setTargetLoading] = useState(false);

  const [exclusions, setExclusions] = useState<Exclusion[]>([]);
  const [names, setNames] = useState<Record<number, string>>({});
  const [reason, setReason] = useState<ExclusionReason>("dislike");

  const applyProfile = (p: ProfileType) => {
    setFullName(p.full_name ?? "");
    setGender(p.gender ?? "");
    setAge(p.age != null ? String(p.age) : "");
    setHeight(p.height_cm != null ? String(p.height_cm) : "");
    setWeight(p.weight_kg != null ? String(p.weight_kg) : "");
    setActivity(p.activity_level);
    setGoal(p.goal);
    setMealsPerDay(String(p.meals_per_day ?? 3));
    setBudget(p.daily_budget != null ? String(p.daily_budget) : "");
  };

  const loadExclusions = async () => {
    try {
      const list = await profileApi.listMyExclusions();
      setExclusions(list);
      const entries = await Promise.all(
        list.map(async (ex) => {
          try {
            const ing = await ingredientApi.get(ex.ingredient_id);
            return [ex.ingredient_id, ing.name] as const;
          } catch {
            return [ex.ingredient_id, `Nguyên liệu #${ex.ingredient_id}`] as const;
          }
        })
      );
      setNames(Object.fromEntries(entries));
    } catch {
      // Bo qua neu chua co loai tru.
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const p = await profileApi.getMyProfile();
        applyProfile(p);
      } catch (err) {
        toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
      } finally {
        setLoading(false);
      }
      await loadExclusions();
    })();
  }, []);

  // Preview dinh duong — debounce 500ms.
  useEffect(() => {
    const g = gender;
    const a = Number(age);
    const h = Number(height);
    const w = Number(weight);
    if (!g || !a || !h || !w) {
      setTarget(null);
      return;
    }
    setTargetLoading(true);
    const t = setTimeout(async () => {
      try {
        const res = await nutritionApi.calculateTarget({
          gender: g,
          age: a,
          height_cm: h,
          weight_kg: w,
          activity_level: activity,
          fitness_goal: goal,
        });
        setTarget(res);
      } catch {
        setTarget(null);
      } finally {
        setTargetLoading(false);
      }
    }, 500);
    return () => clearTimeout(t);
  }, [gender, age, height, weight, activity, goal]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await profileApi.updateMyProfile({
        full_name: fullName || null,
        gender: gender || null,
        age: age ? Number(age) : null,
        height_cm: height ? Number(height) : null,
        weight_kg: weight ? Number(weight) : null,
        activity_level: activity,
        goal,
        meals_per_day: Number(mealsPerDay),
        daily_budget: budget ? Number(budget) : null,
      });
      applyProfile(updated);
      toast.success("Đã lưu hồ sơ.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    } finally {
      setSaving(false);
    }
  };

  const addExclusion = async (ingredientId: number, ingredientName: string) => {
    if (exclusions.some((ex) => ex.ingredient_id === ingredientId)) {
      toast("Nguyên liệu này đã có trong danh sách loại trừ.");
      return;
    }
    try {
      const ex = await profileApi.addMyExclusion(ingredientId, reason);
      setExclusions((prev) => [...prev, ex]);
      setNames((prev) => ({ ...prev, [ingredientId]: ingredientName }));
      toast.success("Đã thêm loại trừ.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  const removeExclusion = async (ingredientId: number) => {
    try {
      await profileApi.removeMyExclusion(ingredientId);
      setExclusions((prev) => prev.filter((ex) => ex.ingredient_id !== ingredientId));
      toast.success("Đã xoá loại trừ.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Có lỗi xảy ra");
    }
  };

  if (loading) return <FullPageSpinner />;

  return (
    <div>
      <PageHeader title="Hồ sơ cá nhân" description="Cập nhật thông tin để nhận thực đơn & dinh dưỡng phù hợp." />

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Card title="Thông tin cơ thể & mục tiêu">
            <form onSubmit={handleSave} className="space-y-4">
              <TextField
                label="Họ và tên"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nguyễn Văn A"
              />
              <div className="grid grid-cols-2 gap-4">
                <SelectField
                  label="Giới tính"
                  value={gender}
                  onChange={(e) => setGender(e.target.value as Gender)}
                  options={toOptions(GENDER_LABELS)}
                  placeholder="Chọn..."
                />
                <NumberField
                  label="Tuổi"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  min={1}
                  max={120}
                  suffix="tuổi"
                />
                <NumberField
                  label="Chiều cao"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  min={100}
                  max={250}
                  suffix="cm"
                />
                <NumberField
                  label="Cân nặng"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  min={20}
                  max={300}
                  suffix="kg"
                />
                <SelectField
                  label="Mức vận động"
                  value={activity}
                  onChange={(e) => setActivity(e.target.value as ActivityLevel)}
                  options={toOptions(ACTIVITY_LABELS)}
                />
                <SelectField
                  label="Mục tiêu"
                  value={goal}
                  onChange={(e) => setGoal(e.target.value as FitnessGoal)}
                  options={toOptions(GOAL_LABELS)}
                />
                <SelectField
                  label="Số bữa / ngày"
                  value={mealsPerDay}
                  onChange={(e) => setMealsPerDay(e.target.value)}
                  options={[
                    { value: "2", label: "2 bữa (trưa + tối)" },
                    { value: "3", label: "3 bữa (sáng + trưa + tối)" },
                  ]}
                />
                <NumberField
                  label="Ngân sách / ngày"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  min={0}
                  suffix="đ"
                  hint="Để trống nếu không giới hạn"
                />
              </div>
              <div className="flex justify-end pt-1">
                <Button type="submit" loading={saving}>
                  <Save className="h-4 w-4" /> Lưu hồ sơ
                </Button>
              </div>
            </form>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-2">
          <Card title="Nhu cầu dinh dưỡng" icon={<Flame className="h-5 w-5" />}>
            {targetLoading ? (
              <div className="flex items-center gap-2 py-6 text-sm text-gray-500">
                <Spinner className="h-5 w-5" /> Đang tính toán...
              </div>
            ) : target ? (
              <NutritionSummary target={target} />
            ) : (
              <p className="py-6 text-center text-sm text-gray-500">
                Nhập đủ giới tính, tuổi, chiều cao, cân nặng để xem nhu cầu dinh dưỡng.
              </p>
            )}
          </Card>

          <Card title="Nguyên liệu loại trừ" icon={<Ban className="h-5 w-5" />}>
            <div className="space-y-3">
              <SelectField
                label="Lý do loại trừ"
                value={reason}
                onChange={(e) => setReason(e.target.value as ExclusionReason)}
                options={toOptions(EXCLUSION_REASON_LABELS)}
              />
              <IngredientPicker
                label="Thêm nguyên liệu"
                placeholder="Tìm và chọn nguyên liệu cần loại trừ..."
                onSelect={(ing) => addExclusion(ing.id, ing.name)}
              />
              {exclusions.length === 0 ? (
                <p className="pt-1 text-sm text-gray-500">Chưa loại trừ nguyên liệu nào.</p>
              ) : (
                <ul className="space-y-2 pt-1">
                  {exclusions.map((ex) => (
                    <li
                      key={ex.ingredient_id}
                      className="flex items-center justify-between gap-2 rounded-xl border border-sand-200 px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-800">
                          {names[ex.ingredient_id] ?? `Nguyên liệu #${ex.ingredient_id}`}
                        </span>
                        <Badge className="bg-rose-100 text-rose-700">
                          {EXCLUSION_REASON_LABELS[ex.reason]}
                        </Badge>
                      </div>
                      <button
                        onClick={() => removeExclusion(ex.ingredient_id)}
                        className="rounded-lg p-1.5 text-gray-400 transition hover:bg-red-50 hover:text-red-600"
                        aria-label="Xoá"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
