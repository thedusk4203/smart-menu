import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { UtensilsCrossed, AlertTriangle, Sparkles, ArrowRight } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi, isInfeasible } from "../../api/mealPlanApi";
import {
  PageHeader, Card, Button, SelectField, NumberField, Textarea,
} from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import type { GenerateParams } from "../../types";

function parseTags(text: string): string[] {
  return text
    .split(/[,\n]/)
    .map((t) => t.trim())
    .filter(Boolean);
}

export function CreateMenu() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [days, setDays] = useState("7");
  const [mealsPerDay, setMealsPerDay] = useState("3");
  const [budget, setBudget] = useState("");
  const [tags, setTags] = useState("");
  const [loading, setLoading] = useState(false);
  const [reasons, setReasons] = useState<string[]>([]);
  const [profileHint, setProfileHint] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setLoading(true);
    setReasons([]);
    setProfileHint(false);

    const params: GenerateParams = {
      days: Number(days),
      meals_per_day: Number(mealsPerDay),
      budget_limit: budget ? Number(budget) : null,
      preferred_tags: parseTags(tags),
    };

    try {
      const result = await mealPlanApi.generate(params);
      if (isInfeasible(result)) {
        setReasons(result.reasons.length ? result.reasons : ["Không thể tạo thực đơn với các ràng buộc hiện tại."]);
        return;
      }
      navigate("/menu-result", { state: { plan: result, params } });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Có lỗi xảy ra";
      toast.error(msg);
      // Loi thuong gap: ho so chua day du de tinh dinh duong.
      if (err instanceof ApiError && (err.status === 400 || err.status === 422 || /hồ sơ|profile|dinh dưỡng/i.test(msg))) {
        setProfileHint(true);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Tạo thực đơn"
        description="Chọn số ngày, số bữa và ngân sách — hệ thống sẽ sinh thực đơn phù hợp."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Tuỳ chọn thực đơn" icon={<UtensilsCrossed className="h-5 w-5" />}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <SelectField
                label="Số ngày"
                value={days}
                onChange={(e) => setDays(e.target.value)}
                options={[
                  { value: "3", label: "3 ngày" },
                  { value: "5", label: "5 ngày" },
                  { value: "7", label: "7 ngày" },
                ]}
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
            </div>
            <NumberField
              label="Giới hạn ngân sách (tổng)"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              min={0}
              suffix="đ"
              hint="Để trống nếu không giới hạn ngân sách"
            />
            <Textarea
              label="Thẻ ưu tiên (tuỳ chọn)"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Ví dụ: healthy, ít dầu mỡ, gà&#10;Cách nhau bằng dấu phẩy hoặc xuống dòng"
              rows={3}
              hint="Các món có thẻ này sẽ được ưu tiên chọn."
            />
            <Button type="submit" loading={loading} className="w-full">
              <Sparkles className="h-4 w-4" /> Sinh thực đơn
            </Button>
          </form>
        </Card>

        <div className="space-y-4">
          {reasons.length > 0 && (
            <Card title="Không thể tạo thực đơn" icon={<AlertTriangle className="h-5 w-5 text-red-500" />}>
              <p className="mb-3 text-sm text-gray-600">
                Hệ thống không tìm được thực đơn thoả mãn các ràng buộc. Lý do:
              </p>
              <ul className="space-y-2">
                {reasons.map((r, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                  >
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-sm text-gray-500">
                Thử tăng ngân sách, giảm số ngày hoặc bớt thẻ ưu tiên.
              </p>
            </Card>
          )}

          {profileHint && (
            <Card title="Kiểm tra hồ sơ" icon={<AlertTriangle className="h-5 w-5 text-accent-500" />}>
              <p className="text-sm text-gray-600">
                Có thể hồ sơ dinh dưỡng của bạn chưa đầy đủ. Hãy cập nhật giới tính, tuổi, chiều cao,
                cân nặng và mục tiêu để hệ thống tính đúng nhu cầu.
              </p>
              <Link
                to="/profile"
                className="mt-3 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
              >
                Cập nhật hồ sơ <ArrowRight className="h-4 w-4" />
              </Link>
            </Card>
          )}

          <Card title="Mẹo tạo thực đơn">
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Hoàn thiện hồ sơ để thực đơn khớp nhu cầu calo &amp; macro của bạn.</li>
              <li>• Ngân sách là tổng cho toàn bộ số ngày đã chọn.</li>
              <li>• Sau khi có kết quả, bạn có thể tạo lại hoặc lưu thực đơn.</li>
            </ul>
          </Card>
        </div>
      </div>
    </div>
  );
}
