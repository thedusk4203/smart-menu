import { GoogleLogin } from "@react-oauth/google";
import toast from "react-hot-toast";
import { ApiError } from "../../lib/apiClient";
import { useAuth } from "../../context/AuthContext";
import type { User } from "../../types";

interface GoogleLoginButtonProps {
  onAuthenticated: (user: User) => void;
}

export function GoogleLoginButton({ onAuthenticated }: GoogleLoginButtonProps) {
  const { loginWithGoogle } = useAuth();
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID?.trim();

  if (!googleClientId) return null;

  return (
    <div className="my-6">
      <div className="relative">
        <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-sand-200" /></div>
        <div className="relative flex justify-center"><span className="bg-white px-3 text-xs font-medium uppercase tracking-[0.14em] text-gray-400">hoặc</span></div>
      </div>
      <div className="mt-5 flex justify-center">
        <GoogleLogin
          onSuccess={async ({ credential }) => {
            if (!credential) {
              toast.error("Google không trả về thông tin đăng nhập");
              return;
            }
            try {
              onAuthenticated(await loginWithGoogle(credential));
            } catch (err) {
              toast.error(err instanceof ApiError ? err.message : "Không thể đăng nhập với Google");
            }
          }}
          onError={() => toast.error("Không thể hoàn tất đăng nhập với Google")}
          text="continue_with"
          shape="rectangular"
          width="360"
        />
      </div>
    </div>
  );
}
