import { ApiError } from "./apiClient";

export type FeedbackAudience = "consumer" | "admin";
export type FeedbackContext =
  | "generic"
  | "login"
  | "register"
  | "load_profile"
  | "save_profile"
  | "profile_exclusion"
  | "load_catalog"
  | "generate_menu"
  | "regenerate_menu"
  | "save_menu"
  | "load_history"
  | "load_shopping"
  | "update_shopping"
  | "share_shopping"
  | "revoke_share"
  | "load_inventory"
  | "update_inventory"
  | "discard_inventory"
  | "ai_status"
  | "ai_chat"
  | "admin_action";

export interface UserFeedback {
  title: string;
  message: string;
  code?: string;
  technicalMessage?: string;
  fields: Record<string, string>;
  retryable: boolean;
}

const CONTEXT_MESSAGES: Record<FeedbackContext, { title: string; message: string }> = {
  generic: { title: "Chưa thể hoàn tất", message: "Vui lòng thử lại. Nếu lỗi vẫn tiếp diễn, hãy tải lại trang." },
  login: { title: "Chưa đăng nhập được", message: "Kiểm tra email và mật khẩu rồi thử lại." },
  register: { title: "Chưa tạo được tài khoản", message: "Kiểm tra thông tin đăng ký rồi thử lại." },
  load_profile: { title: "Chưa tải được hồ sơ", message: "Hãy thử tải lại hồ sơ." },
  save_profile: { title: "Chưa lưu được hồ sơ", message: "Thông tin vừa nhập vẫn còn trên màn hình. Hãy kiểm tra rồi thử lại." },
  profile_exclusion: { title: "Chưa cập nhật được danh sách loại trừ", message: "Hãy thử lại sau ít phút." },
  load_catalog: { title: "Chưa tải được dữ liệu", message: "Hãy kiểm tra kết nối rồi thử lại." },
  generate_menu: { title: "Chưa tạo được thực đơn", message: "Hãy kiểm tra hồ sơ và các điều kiện đã chọn rồi thử lại." },
  regenerate_menu: { title: "Chưa tạo được phương án khác", message: "Thực đơn hiện tại vẫn được giữ nguyên. Hãy thử lại." },
  save_menu: { title: "Chưa lưu được thực đơn", message: "Thực đơn vẫn còn trên màn hình. Hãy thử lưu lại." },
  load_history: { title: "Chưa tải được thực đơn đã lưu", message: "Hãy thử tải lại danh sách." },
  load_shopping: { title: "Chưa tạo được danh sách đi chợ", message: "Hãy chọn lại thực đơn hoặc ngày rồi thử lại." },
  update_shopping: { title: "Chưa cập nhật được", message: "Trạng thái cũ đã được khôi phục. Hãy thử lại." },
  share_shopping: { title: "Chưa tạo được liên kết", message: "Danh sách của bạn chưa được chia sẻ. Hãy thử lại." },
  revoke_share: { title: "Chưa thu hồi được liên kết", message: "Liên kết hiện tại vẫn còn hiệu lực. Hãy thử lại." },
  load_inventory: { title: "Chưa tải được nguyên liệu còn lại", message: "Hãy thử tải lại danh sách." },
  update_inventory: { title: "Chưa lưu được thay đổi", message: "Thông tin cũ vẫn được giữ nguyên. Hãy thử lại." },
  discard_inventory: { title: "Chưa loại bỏ được nguyên liệu", message: "Nguyên liệu vẫn được giữ lại. Hãy thử lại." },
  ai_status: { title: "Chưa kết nối được với Menuto", message: "Hãy kiểm tra kết nối rồi thử lại." },
  ai_chat: { title: "Menuto chưa trả lời được", message: "Câu hỏi của bạn đã được giữ lại. Hãy thử lại." },
  admin_action: { title: "Thao tác chưa hoàn tất", message: "Kiểm tra chi tiết lỗi bên dưới rồi thử lại." },
};

const CODE_MESSAGES: Record<string, { title: string; message: string }> = {
  NETWORK_UNAVAILABLE: {
    title: "Mất kết nối",
    message: "Smart Menu chưa kết nối được. Kiểm tra mạng rồi thử lại.",
  },
  AUTH_SESSION_EXPIRED: {
    title: "Phiên đăng nhập đã hết hạn",
    message: "Hãy đăng nhập lại để tiếp tục công việc đang làm.",
  },
  AUTH_TOKEN_INVALID: {
    title: "Cần đăng nhập lại",
    message: "Phiên đăng nhập không còn hợp lệ. Hãy đăng nhập lại để tiếp tục.",
  },
  AUTH_ACCOUNT_UNAVAILABLE: {
    title: "Tài khoản không còn khả dụng",
    message: "Hãy liên hệ quản trị viên nếu bạn cần hỗ trợ.",
  },
  AUTH_FORBIDDEN: {
    title: "Không có quyền truy cập",
    message: "Tài khoản của bạn không được phép thực hiện thao tác này.",
  },
  EMAIL_ALREADY_EXISTS: {
    title: "Email đã được sử dụng",
    message: "Hãy đăng nhập hoặc dùng một email khác.",
  },
  PROFILE_INCOMPLETE: {
    title: "Hồ sơ còn thiếu thông tin",
    message: "Bổ sung các trường được đánh dấu để Smart Menu tính nhu cầu dinh dưỡng và tạo thực đơn.",
  },
  PROFILE_NOT_FOUND: {
    title: "Bạn chưa có hồ sơ dinh dưỡng",
    message: "Hãy hoàn thiện hồ sơ trước khi tạo thực đơn.",
  },
  NUTRITION_TARGET_INFEASIBLE: {
    title: "Mục tiêu dinh dưỡng cần điều chỉnh",
    message: "Hãy kiểm tra mục tiêu cân nặng hoặc mức vận động trước khi tạo thực đơn.",
  },
  MEAL_SELECTION_INVALID: {
    title: "Thực đơn đã thay đổi",
    message: "Hãy tạo phương án mới rồi lưu lại.",
  },
  SHOPPING_PLAN_UNSUPPORTED: {
    title: "Thực đơn cần được tạo lại",
    message: "Thực đơn này thuộc phiên bản cũ. Hãy tạo thực đơn mới để lập danh sách đi chợ.",
  },
  SHOPPING_DAY_NOT_FOUND: {
    title: "Không tìm thấy ngày đã chọn",
    message: "Hãy chọn một ngày khác trong thực đơn.",
  },
  RESOURCE_GONE: {
    title: "Nội dung không còn khả dụng",
    message: "Liên kết có thể đã hết hạn hoặc bị thu hồi.",
  },
  AI_UNAVAILABLE: {
    title: "Menuto đang tạm gián đoạn",
    message: "Câu hỏi của bạn đã được giữ lại. Hãy thử lại sau.",
  },
  AI_RESPONSE_INVALID: {
    title: "Menuto chưa tạo được câu trả lời phù hợp",
    message: "Hãy thử lại câu hỏi này.",
  },
  AI_STREAM_FAILED: {
    title: "Câu trả lời bị gián đoạn",
    message: "Hãy thử lại để Menuto tạo câu trả lời mới.",
  },
  REQUEST_VALIDATION_FAILED: {
    title: "Một số thông tin chưa hợp lệ",
    message: "Kiểm tra các trường được đánh dấu rồi thử lại.",
  },
};

export function toUserFeedback(
  error: unknown,
  context: FeedbackContext = "generic",
  audience: FeedbackAudience = "consumer",
): UserFeedback {
  const contextual = CONTEXT_MESSAGES[context];
  if (!(error instanceof ApiError)) {
    return { ...contextual, fields: {}, retryable: true };
  }
  const specific = CODE_MESSAGES[error.code];
  const title = specific?.title ?? contextual.title;
  const message = specific?.message ?? (error.userMessage || contextual.message);
  return {
    title,
    message,
    code: audience === "admin" ? error.code : undefined,
    technicalMessage: audience === "admin" ? error.technicalMessage : undefined,
    fields: error.fields,
    retryable: error.retryable,
  };
}

export function feedbackMessage(error: unknown, context: FeedbackContext = "generic"): string {
  return toUserFeedback(error, context).message;
}

export function adminFeedbackMessage(error: unknown, context: FeedbackContext = "admin_action"): string {
  const feedback = toUserFeedback(error, context, "admin");
  return [
    feedback.message,
    feedback.code ? `Mã: ${feedback.code}` : "",
    feedback.technicalMessage ? `Chi tiết: ${feedback.technicalMessage}` : "",
  ].filter(Boolean).join(" · ");
}
