import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Wallet, Sparkles, ChefHat, Loader2, AlertTriangle } from "lucide-react";

import {
  generateMealPlan,
  isInfeasible,
  type GenerateParams,
} from "../api/mealPlanApi";

// Tách "Yêu cầu đặc biệt" (text tự do) thành danh sách tag ưu tiên. Đây là
// ràng buộc MỀM ở backend (chỉ cộng điểm), nên tách thô theo dấu phẩy/xuống dòng
// là an toàn — chưa cần AI parse. Ví dụ: "món luộc, ít dầu" -> ["món luộc","ít dầu"].
function parsePreferredTags(text: string): string[] {
  return text
    .split(/[,\n]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function CreateMenu() {
  const navigate = useNavigate();

  const [budget, setBudget] = useState("");
  const [special, setSpecial] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reasons, setReasons] = useState<string[]>([]); // lý do bất khả thi

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setReasons([]);

    // Ngân sách rỗng -> undefined = dùng ngân sách trong hồ sơ (hoặc không giới hạn).
    const parsedBudget = budget.trim() ? Number(budget) : undefined;
    const params: GenerateParams = {
      budget_limit:
        parsedBudget !== undefined && !Number.isNaN(parsedBudget)
          ? parsedBudget
          : undefined,
      preferred_tags: parsePreferredTags(special),
    };

    try {
      const result = await generateMealPlan(params);
      if (isInfeasible(result)) {
        // Không thể lập thực đơn -> hiện lý do rõ ràng (FR-PLAN-03/HC).
        setReasons(result.reasons);
        return;
      }
      // Thành công: chuyển sang trang kết quả, mang theo thực đơn + tham số
      // (để trang đó có thể "tạo lại" với cùng ràng buộc, seed khác).
      navigate("/menu-result", { state: { plan: result, params } });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Có lỗi xảy ra, thử lại sau.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-emerald-100 to-teal-50 flex flex-col items-center justify-center p-4">
      <div className="bg-white/90 backdrop-blur-xl p-8 rounded-3xl shadow-2xl w-full max-w-md text-center border border-white">
        <div className="flex justify-center mb-4">
          <div className="bg-emerald-100 p-4 rounded-full text-emerald-600">
            <ChefHat className="w-10 h-10" />
          </div>
        </div>

        <h1 className="text-3xl font-bold text-emerald-700 mb-2">Smart Menu AI</h1>
        <p className="text-gray-500 mb-8 text-sm">Lên thực đơn 7 ngày siêu tốc chuẩn dinh dưỡng</p>

        <div className="text-left mb-5">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <Wallet className="w-4 h-4 mr-1 text-emerald-600" /> Ngân sách đi chợ (VNĐ)
          </label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            placeholder="Ví dụ: 700000 (để trống = dùng hồ sơ)"
            className="w-full bg-gray-50 border-none p-3.5 rounded-xl focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner text-gray-800"
          />
        </div>

        <div className="text-left mb-6">
          <label className="flex items-center text-gray-700 text-sm font-bold mb-2">
            <Sparkles className="w-4 h-4 mr-1 text-orange-500" /> Yêu cầu đặc biệt
          </label>
          <textarea
            value={special}
            onChange={(e) => setSpecial(e.target.value)}
            placeholder="Ví dụ: món luộc, ít dầu, thanh mát... (phân tách bằng dấu phẩy)"
            className="w-full bg-gray-50 border-none p-3.5 rounded-xl h-28 focus:outline-none focus:ring-4 focus:ring-emerald-200 transition-all shadow-inner resize-none text-gray-800"
          ></textarea>
        </div>

        {/* Báo lỗi kỹ thuật (mạng/hồ sơ thiếu...) */}
        {error && (
          <div className="text-left mb-4 bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-xl flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Không thể lập thực đơn — liệt kê lý do + gợi ý điều chỉnh */}
        {reasons.length > 0 && (
          <div className="text-left mb-4 bg-amber-50 border border-amber-200 text-amber-800 text-sm p-3 rounded-xl">
            <p className="font-bold flex items-center gap-1 mb-1">
              <AlertTriangle className="w-4 h-4" /> Chưa thể lập thực đơn:
            </p>
            <ul className="list-disc pl-5 space-y-1">
              {reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}

        <button
          onClick={handleGenerate}
          disabled={loading}
          className="w-full group bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl shadow-lg transform hover:-translate-y-1 active:scale-95 transition-all duration-300 flex items-center justify-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" /> Đang lập thực đơn...
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5 mr-2 group-hover:animate-pulse" /> Tạo Thực Đơn Ngay
            </>
          )}
        </button>
      </div>
    </div>
  );
}
