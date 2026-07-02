import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Ruler, Weight, Target, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import { getMyProfile, updateMyProfile } from "../api/profileApi";
import { getToken } from "../api/httpClient";

export default function Profile() {
  const navigate = useNavigate();
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [goal, setGoal] = useState("maintain");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Load hồ sơ khi vào trang
  useEffect(() => {
    if (!getToken()) { navigate("/"); return; }
    setLoading(true);
    getMyProfile()
      .then((p) => {
        setHeightCm(p.height_cm ? String(p.height_cm) : "");
        setWeightKg(p.weight_kg ? String(p.weight_kg) : "");
        setGoal(p.goal ?? "maintain");
      })
      .catch(() => toast.error("Không tải được hồ sơ"))
      .finally(() => setLoading(false));
  }, [navigate]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateMyProfile({
        height_cm: heightCm ? Number(heightCm) : undefined,
        weight_kg: weightKg ? Number(weightKg) : undefined,
        goal,
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

  if (loading) return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 flex items-center justify-center">
      <p className="text-emerald-600 font-semibold">Đang tải hồ sơ...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-50 to-teal-100 flex justify-center items-center p-4">
      <div className="bg-white/90 backdrop-blur-xl p-8 rounded-3xl shadow-xl w-full max-w-lg border border-white">
        <h2 className="text-3xl font-bold text-center text-emerald-700 mb-8">Hồ Sơ Dinh Dưỡng</h2>

        <div className="grid grid-cols-2 gap-6 mb-6">
          <div>
            <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
              <Ruler className="w-4 h-4 mr-1 text-emerald-600" /> Chiều cao (cm)
            </label>
            <input
              type="number"
              placeholder="170"
              value={heightCm}
              onChange={(e) => setHeightCm(e.target.value)}
              className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner"
            />
          </div>
          <div>
            <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
              <Weight className="w-4 h-4 mr-1 text-emerald-600" /> Cân nặng (kg)
            </label>
            <input
              type="number"
              placeholder="65"
              value={weightKg}
              onChange={(e) => setWeightKg(e.target.value)}
              className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner"
            />
          </div>
        </div>

        <div className="mb-6">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <Target className="w-4 h-4 mr-1 text-emerald-600" /> Mục tiêu thể chất
          </label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner text-gray-700 cursor-pointer"
          >
            <option value="maintain">Duy trì cân nặng</option>
            <option value="lose_weight">Giảm cân an toàn</option>
            <option value="gain_muscle">Tăng cơ / Tăng cân</option>
          </select>
        </div>

        <div className="mb-8">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <AlertCircle className="w-4 h-4 mr-1 text-orange-500" /> Thực phẩm dị ứng / Không ăn
          </label>
          <textarea
            placeholder="Ví dụ: Dị ứng đậu phộng, không ăn hành... (tính năng sắp ra mắt)"
            disabled
            className="w-full bg-gray-100 border-none p-3.5 rounded-xl h-24 resize-none text-gray-400 cursor-not-allowed"
          />
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-bold py-4 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {saving ? "Đang lưu..." : "Cập Nhật Hồ Sơ"}
        </button>
      </div>
    </div>
  );
}