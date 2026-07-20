import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Flame, Wallet, User, UtensilsCrossed, Salad, ShoppingCart, AlertTriangle,
  ArrowRight, Calendar,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { profileApi } from "../api/profileApi";
import { mealPlanApi } from "../api/mealPlanApi";
import { StatCard, Card, FullPageSpinner, EmptyState, Badge, FeedbackBanner } from "../components/ui";
import { formatKcal, formatVND, formatDate } from "../lib/format";
import { toUserFeedback, type UserFeedback } from "../lib/userFeedback";
import type { Profile, MealPlan } from "../types";

const SHORTCUTS = [
  { to: "/create-menu", label: "Tạo thực đơn", icon: UtensilsCrossed, tone: "bg-brand-100 text-brand-700" },
  { to: "/profile", label: "Cập nhật hồ sơ", icon: User, tone: "bg-accent-100 text-accent-700" },
  { to: "/ingredients", label: "Nguyên liệu", icon: Salad, tone: "bg-sky-100 text-sky-700" },
  { to: "/shopping-list", label: "Đi chợ", icon: ShoppingCart, tone: "bg-indigo-100 text-indigo-700" },
];

export function Dashboard() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [profileFeedback, setProfileFeedback] = useState<UserFeedback | null>(null);
  const [plansFeedback, setPlansFeedback] = useState<UserFeedback | null>(null);

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setProfileFeedback(null);
    setPlansFeedback(null);
    const [profileResult, plansResult] = await Promise.allSettled([
      profileApi.getMyProfile(),
      mealPlanApi.list(),
    ]);
    if (profileResult.status === "fulfilled") setProfile(profileResult.value);
    else setProfileFeedback(toUserFeedback(profileResult.reason, "load_profile"));
    if (plansResult.status === "fulfilled") setPlans(plansResult.value.slice(0, 3));
    else setPlansFeedback(toUserFeedback(plansResult.reason, "load_history"));
    setLoading(false);
  }, [user]);

  useEffect(() => { void load(); }, [load]);

  if (loading) return <FullPageSpinner />;

  const incomplete =
    !profile ||
    profile.gender == null ||
    profile.age == null ||
    profile.height_cm == null ||
    profile.weight_kg == null;

  const greetingName = profile?.full_name || user?.email;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Xin chào, {greetingName} 👋</h1>
        <p className="mt-1 text-sm text-gray-500">Chúc bạn một ngày ăn uống ngon miệng và đủ chất.</p>
      </div>

      {profileFeedback && <FeedbackBanner feedback={profileFeedback} onRetry={() => void load()} className="mb-5" />}

      {incomplete && (
        <Link
          to="/profile"
          className="mb-6 flex items-start gap-3 rounded-2xl border border-accent-200 bg-accent-50 px-4 py-3.5 transition hover:bg-accent-100"
        >
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-accent-600" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-accent-800">Hoàn thiện hồ sơ của bạn</p>
            <p className="text-sm text-accent-700">
              Cập nhật giới tính, tuổi, chiều cao, cân nặng để tính nhu cầu dinh dưỡng và tạo thực đơn phù hợp.
            </p>
          </div>
          <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-accent-600" />
        </Link>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <StatCard
          label="Calo mục tiêu / ngày"
          value={formatKcal(profile?.daily_calorie_target)}
          icon={Flame}
          tone="brand"
          sub="Theo hồ sơ dinh dưỡng"
        />
        <StatCard
          label="Ngân sách / ngày"
          value={formatVND(profile?.daily_budget)}
          icon={Wallet}
          tone="accent"
          sub="Dùng khi tạo thực đơn"
        />
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {SHORTCUTS.map((s) => (
          <Link
            key={s.to}
            to={s.to}
            className="flex flex-col items-start gap-3 rounded-2xl border border-sand-200 bg-white p-4 shadow-sm transition hover:border-brand-200 hover:shadow"
          >
            <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${s.tone}`}>
              <s.icon className="h-5 w-5" />
            </span>
            <span className="text-sm font-semibold text-gray-800">{s.label}</span>
          </Link>
        ))}
      </div>

      <div className="mt-6">
        <Card
          title="Thực đơn gần đây"
          icon={<Calendar className="h-5 w-5" />}
          action={
            <Link to="/history" className="text-sm font-medium text-brand-600 hover:text-brand-700">
              Xem tất cả
            </Link>
          }
        >
          {plansFeedback ? (
            <FeedbackBanner feedback={plansFeedback} onRetry={() => void load()} />
          ) : plans.length === 0 ? (
            <EmptyState
              icon={UtensilsCrossed}
              title="Chưa có thực đơn nào"
              description="Hãy tạo thực đơn đầu tiên phù hợp ngân sách và mục tiêu của bạn."
              action={
                <Link
                  to="/create-menu"
                  className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700"
                >
                  Tạo thực đơn <ArrowRight className="h-4 w-4" />
                </Link>
              }
            />
          ) : (
            <ul className="divide-y divide-sand-100">
              {plans.map((plan) => (
                <li key={plan.id} className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-gray-800">{plan.name}</p>
                    <p className="text-xs text-gray-400">{formatDate(plan.start_date)}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-brand-100 text-brand-700">{formatVND(plan.total_cost)}</Badge>
                    <Badge className="bg-amber-100 text-amber-700">{formatKcal(plan.total_calories)}</Badge>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
