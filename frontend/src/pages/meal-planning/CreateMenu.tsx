import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { UtensilsCrossed, AlertTriangle, Sparkles, ArrowRight } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { mealPlanApi, isInfeasible } from "../../api/mealPlanApi";
import { aiApi } from "../../api/aiApi";
import {
  PageHeader, Card, Button, SelectField, MoneyField, Textarea,
} from "../../components/ui";
import { ApiError } from "../../lib/apiClient";
import { tagApi, type Tag } from "../../api/tagApi";
import { TagPicker } from "../../components/domain/TagPicker";
import type { GenerateParams, InfeasibleResult } from "../../types";
import { todayISO } from "../../lib/format";

export function CreateMenu() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [days, setDays] = useState("7");
  const [mealsPerDay, setMealsPerDay] = useState("3");
  const [budget, setBudget] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [reasons, setReasons] = useState<InfeasibleResult["reasons"]>([]);
  const [profileHint, setProfileHint] = useState(false);
  const [naturalRequest, setNaturalRequest] = useState("");
  const [parsing, setParsing] = useState(false);
  const [clarification, setClarification] = useState("");
  const [catalogTags, setCatalogTags] = useState<Tag[]>([]);

  useEffect(() => { tagApi.active().then(setCatalogTags).catch(() => undefined); }, []);

  const parseNaturalRequest = async () => {
    if (!naturalRequest.trim()) return;
    setParsing(true); setClarification("");
    try {
      const parsed = await aiApi.parseMenuRequest(naturalRequest.trim());
      if (parsed.days) setDays(String(parsed.days));
      if (parsed.meals_per_day) setMealsPerDay(String(parsed.meals_per_day));
      if (parsed.budget_limit != null) setBudget(String(parsed.budget_limit));
      if (parsed.preferred_tags.length) setTags(parsed.preferred_tags.filter((tag) => catalogTags.some((item) => item.name.toLocaleLowerCase("vi") === tag.toLocaleLowerCase("vi"))));
      if (parsed.needs_clarification) setClarification(parsed.clarification_question ?? "Hãy bổ sung thêm yêu cầu.");
      else toast.success("Đã điền form từ yêu cầu. Hãy kiểm tra trước khi sinh thực đơn.");
    } catch (err) { toast.error(err instanceof ApiError ? err.message : "Không thể phân tích yêu cầu."); }
    finally { setParsing(false); }
  };

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
      preferred_tags: tags,
      start_date: todayISO(),
    };

    try {
      const result = await mealPlanApi.generate(params);
      if (isInfeasible(result)) {
        setReasons(result.reasons.length ? result.reasons : [{ code: "NO_SOLUTION", message: "Không thể tạo thực đơn với các ràng buộc hiện tại." }]);
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
            <div className="rounded-2xl border border-brand-200 bg-brand-50 p-4">
              <Textarea label="Mô tả bằng tiếng Việt" value={naturalRequest}
                onChange={(e) => setNaturalRequest(e.target.value)}
                placeholder="Ví dụ: Thực đơn 5 ngày, 3 bữa, ngân sách 600k, ưu tiên giàu đạm..." rows={3}
                hint="AI chỉ chuyển mô tả thành các trường bên dưới; planner vẫn tính toán bằng dữ liệu hệ thống." />
              <Button type="button" variant="secondary" size="sm" className="mt-3" loading={parsing} onClick={parseNaturalRequest}><Sparkles className="h-4 w-4" /> Phân tích yêu cầu</Button>
              {clarification && <p className="mt-3 text-sm text-amber-800">AI cần làm rõ: {clarification}</p>}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <SelectField
                label="Số ngày"
                value={days}
                onChange={(e) => setDays(e.target.value)}
                options={[
                  { value: "1", label: "1 ngày" },
                  { value: "2", label: "2 ngày" },
                  { value: "3", label: "3 ngày" },
                  { value: "4", label: "4 ngày" },
                  { value: "5", label: "5 ngày" },
                  { value: "6", label: "6 ngày" },
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
            <MoneyField
              label="Giới hạn ngân sách (tổng)"
              value={budget}
              onValueChange={setBudget}
              min={0}
              hint="Để trống nếu không giới hạn ngân sách"
            />
            <TagPicker tags={catalogTags} selected={tags} onChange={setTags} />
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
                    <span>{r.message}</span>
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
