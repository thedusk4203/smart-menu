import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { User, Ruler, Weight, Target, Activity, Utensils, Wallet, Calendar, AlertCircle, Plus, X } from "lucide-react";
import toast from "react-hot-toast";
import { getMyProfile, updateMyProfile, getMyExclusions, addMyExclusion, removeMyExclusion } from "../api/profileApi";
import type { Exclusion } from "../api/profileApi";
import { getIngredients } from "../api/ingredientApi";
import type { Ingredient } from "../api/ingredientApi";
import { getToken } from "../api/httpClient";

export default function Profile() {
  const navigate = useNavigate();
  // Các trường hồ sơ
  const [fullName, setFullName] = useState("");
  const [gender, setGender] = useState("");
  const [age, setAge] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [activityLevel, setActivityLevel] = useState("moderate");
  const [goal, setGoal] = useState("maintain");
  const [mealsPerDay, setMealsPerDay] = useState("3");
  const [dailyBudget, setDailyBudget] = useState("");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Dị ứng / loại trừ
  const [exclusions, setExclusions] = useState<Exclusion[]>([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [selectedIng, setSelectedIng] = useState("");
  const [selectedReason, setSelectedReason] = useState<"allergy" | "dislike">("allergy");

  useEffect(() => {
    if (!getToken()) { navigate("/"); return; }
    setLoading(true);
    Promise.all([getMyProfile(), getMyExclusions(), getIngredients({ limit: 100 })])
      .then(([p, exc, ings]) => {
        setFullName(p.full_name ?? "");
        setGender(p.gender ?? "");
        setAge(p.age ? String(p.age) : "");
        setHeightCm(p.height_cm ? String(p.height_cm) : "");
        setWeightKg(p.weight_kg ? String(p.weight_kg) : "");
        setActivityLevel(p.activity_level ?? "moderate");
        setGoal(p.goal ?? "maintain");
        setMealsPerDay(p.meals_per_day ? String(p.meals_per_day) : "3");
        setDailyBudget(p.daily_budget ? String(p.daily_budget) : "");
        setExclusions(exc);
        setIngredients(ings);
      })
      .catch(() => toast.error("Không tải được hồ sơ"))
      .finally(() => setLoading(false));
  }, [navigate]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateMyProfile({
        full_name: fullName || undefined,
        gender: gender || undefined,
        age: age ? Number(age) : undefined,
        height_cm: heightCm ? Number(heightCm) : undefined,
        weight_kg: weightKg ? Number(weightKg) : undefined,
        activity_level: activityLevel || undefined,
        goal,
        meals_per_day: mealsPerDay ? Number(mealsPerDay) : undefined,
        daily_budget: dailyBudget ? Number(dailyBudget) : undefined,
      });
      toast.success("Đã lưu hồ sơ thành công! 🌿", {
        style: { borderRadius: "12px", background: "#10b981", color: "#fff", fontWeight: "bold" },
      });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Lưu thất bại");
    } finally {
      setSaving(false);
    }
  };

  const handleAddExclusion = async () => {
    if (!selectedIng) { toast.error("Vui lòng chọn nguyên liệu"); return; }
    const ingId = Number(selectedIng);
    if (exclusions.some((e) => e.ingredient_id === ingId)) {
      toast.error("Nguyên liệu này đã có trong danh sách"); return;
    }
    try {
      const newExc = await addMyExclusion(ingId, selectedReason);
      setExclusions((prev) => [...prev, newExc]);
      setSelectedIng("");
      toast.success("Đã thêm");
    } catch { toast.error("Thêm thất bại"); }
  };

  const handleRemoveExclusion = async (ingredientId: number) => {
    try {
      await removeMyExclusion(ingredientId);
      setExclusions((prev) => prev.filter((e) => e.ingredient_id !== ingredientId));
      toast.success("Đã bỏ");
    } catch { toast.error("Xoá thất bại"); }
  };

  const ingName = (id: number) => ingredients.find((i) => i.id === id)?.name ?? `#${id}`;

  const inputClass = "w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner";
  const labelClass = "flex items-center text-gray-700 text-sm font-bold mb-2";

  if (loading) return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 flex items-center justify-center">
      <p className="text-emerald-600 font-semibold">Đang tải hồ sơ...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 flex justify-center items-start py-10 px-4">
      <div className="bg-white/90 backdrop-blur-xl p-8 rounded-3xl shadow-xl w-full max-w-2xl border border-white">
        <h2 className="text-3xl font-bold text-center text-emerald-700 mb-2">Hồ Sơ Dinh Dưỡng</h2>
        <p className="text-center text-gray-500 mb-8">Thông tin của bạn giúp hệ thống lập thực đơn phù hợp hơn</p>

        {/* Họ tên */}
        <div className="mb-6">
          <label className={labelClass}><User className="w-4 h-4 mr-1 text-emerald-600" /> Họ và tên</label>
          <input type="text" placeholder="Nguyễn Văn A" value={fullName}
            onChange={(e) => setFullName(e.target.value)} className={inputClass} />
        </div>

        {/* Giới tính + Tuổi */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <label className={labelClass}><User className="w-4 h-4 mr-1 text-emerald-600" /> Giới tính</label>
            <select value={gender} onChange={(e) => setGender(e.target.value)} className={`${inputClass} cursor-pointer`}>
              <option value="">-- Chọn --</option>
              <option value="male">Nam</option>
              <option value="female">Nữ</option>
            </select>
          </div>
          <div>
            <label className={labelClass}><Calendar className="w-4 h-4 mr-1 text-emerald-600" /> Tuổi</label>
            <input type="number" placeholder="22" value={age}
              onChange={(e) => setAge(e.target.value)} className={inputClass} />
          </div>
        </div>

        {/* Chiều cao + Cân nặng */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <label className={labelClass}><Ruler className="w-4 h-4 mr-1 text-emerald-600" /> Chiều cao (cm)</label>
            <input type="number" placeholder="170" value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}><Weight className="w-4 h-4 mr-1 text-emerald-600" /> Cân nặng (kg)</label>
            <input type="number" placeholder="65" value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)} className={inputClass} />
          </div>
        </div>

        {/* Mức vận động + Mục tiêu */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <label className={labelClass}><Activity className="w-4 h-4 mr-1 text-emerald-600" /> Mức vận động</label>
            <select value={activityLevel} onChange={(e) => setActivityLevel(e.target.value)} className={`${inputClass} cursor-pointer`}>
              <option value="sedentary">Ít vận động</option>
              <option value="light">Vận động nhẹ</option>
              <option value="moderate">Vận động vừa</option>
              <option value="active">Vận động nhiều</option>
            </select>
          </div>
          <div>
            <label className={labelClass}><Target className="w-4 h-4 mr-1 text-emerald-600" /> Mục tiêu</label>
            <select value={goal} onChange={(e) => setGoal(e.target.value)} className={`${inputClass} cursor-pointer`}>
              <option value="maintain">Duy trì cân nặng</option>
              <option value="lose_weight">Giảm cân</option>
              <option value="gain_muscle">Tăng cơ</option>
              <option value="gain_weight">Tăng cân</option>
            </select>
          </div>
        </div>

        {/* Số bữa + Ngân sách */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <div>
            <label className={labelClass}><Utensils className="w-4 h-4 mr-1 text-emerald-600" /> Số bữa/ngày</label>
            <select value={mealsPerDay} onChange={(e) => setMealsPerDay(e.target.value)} className={`${inputClass} cursor-pointer`}>
              <option value="1">1 bữa</option>
              <option value="2">2 bữa</option>
              <option value="3">3 bữa</option>
              <option value="4">4 bữa</option>
              <option value="5">5 bữa</option>
            </select>
          </div>
          <div>
            <label className={labelClass}><Wallet className="w-4 h-4 mr-1 text-emerald-600" /> Ngân sách/ngày (đ)</label>
            <input type="number" placeholder="80000" value={dailyBudget}
              onChange={(e) => setDailyBudget(e.target.value)} className={inputClass} />
          </div>
        </div>

        <button onClick={handleSave} disabled={saving}
          className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold py-4 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300 disabled:opacity-60 cursor-pointer mb-8">
          {saving ? "Đang lưu..." : "Cập Nhật Hồ Sơ"}
        </button>

        {/* ── Nguyên liệu dị ứng / không ăn ── */}
        <div className="border-t border-gray-100 pt-6">
          <label className={labelClass}><AlertCircle className="w-4 h-4 mr-1 text-orange-500" /> Thực phẩm dị ứng / Không ăn</label>

          <div className="flex flex-col sm:flex-row gap-2 mb-4">
            <select value={selectedIng} onChange={(e) => setSelectedIng(e.target.value)}
              className="flex-1 bg-gray-50 border-none p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-orange-200 text-gray-700 cursor-pointer">
              <option value="">-- Chọn nguyên liệu --</option>
              {ingredients.map((ing) => <option key={ing.id} value={ing.id}>{ing.name}</option>)}
            </select>
            <select value={selectedReason} onChange={(e) => setSelectedReason(e.target.value as "allergy" | "dislike")}
              className="bg-gray-50 border-none p-3 rounded-xl focus:outline-none focus:ring-4 focus:ring-orange-200 text-gray-700 cursor-pointer">
              <option value="allergy">Dị ứng</option>
              <option value="dislike">Không thích</option>
            </select>
            <button onClick={handleAddExclusion}
              className="bg-orange-500 hover:bg-orange-600 text-white font-bold px-4 py-3 rounded-xl flex items-center justify-center gap-1 transition-colors cursor-pointer">
              <Plus className="w-5 h-5" /> Thêm
            </button>
          </div>

          {exclusions.length === 0 ? (
            <p className="text-sm text-gray-400 italic">Chưa có nguyên liệu nào bị loại trừ.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {exclusions.map((exc) => (
                <span key={exc.id}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${
                    exc.reason === "allergy" ? "bg-red-100 text-red-700" : "bg-yellow-100 text-yellow-700"
                  }`}>
                  {ingName(exc.ingredient_id)}
                  <span className="text-xs opacity-70">({exc.reason === "allergy" ? "dị ứng" : "không thích"})</span>
                  <button onClick={() => handleRemoveExclusion(exc.ingredient_id)}
                    className="hover:bg-black/10 rounded-full p-0.5 cursor-pointer">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}